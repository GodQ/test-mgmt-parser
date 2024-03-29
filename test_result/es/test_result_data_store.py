import time
from pprint import pprint

import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl import connections

from config.config import Config
from test_result.data_mgmt_interface import check_project_exist
from test_result.data_store_interface import TestResultDataStoreInterface


ES_HOSTS = Config.get_config('es_hosts')
# Define a default Elasticsearch client
connections.create_connection(hosts=ES_HOSTS, timeout=30)


class ESTestResultDataStore(TestResultDataStoreInterface):
    search_source = ['case_id', 'case_result', 'testrun_id', 'comment']

    def __init__(self):
        super().__init__()
        hosts = ES_HOSTS
        self.es = Elasticsearch(hosts=hosts)

    def create_project(self, project_id, enable_full_text=True):
        # No action to create project storage, and enable full test search
        pass

    def enable_full_text_search(self, project_id):
        # No action to create project storage, and enable full test search
        pass

    def common_search(self, search_obj: Search, **kwargs):
        assert search_obj
        if kwargs.get('offset'):
            offset = kwargs.get('offset')
        else:
            offset = 0
        if kwargs.get('limit'):
            limit = kwargs.get('limit')
        else:
            limit = 100
        search_obj = search_obj[offset: offset + limit]
        if kwargs.get('index'):
            index = kwargs.get('index')
            search_obj = search_obj.index(index)

        if kwargs.get('raw_result') is not None:
            raw_result = kwargs.get('raw_result')
        else:
            raw_result = False
        if kwargs.get('attach_id'):
            attach_id = kwargs.get('attach_id')
        else:
            attach_id = False
        if kwargs.get('with_page_info') is not None:
            with_page_info = kwargs.get('with_page_info')
        else:
            with_page_info = False

        print("\nES query:", search_obj.to_dict())

        res = search_obj.execute()

        if raw_result is True:
            return res

        data = list()

        for hit in res.hits.hits:
            d = hit['_source'].to_dict()
            if attach_id:
                d['index'] = hit['_index']
                d['doc_id'] = hit['_id']
            data.append(d)
        if with_page_info is True:
            page_info = {
                "total": res.hits.total.value,
                "limit": limit,
                "offset": offset
            }
            return data, page_info
        else:
            return data

    def update_es_by_query(self, index, queries, updates):
        query_must = list()
        for k, v in queries.items():
            query_must.append({"match_phrase": {k: v}})

        script_source = list()
        for k, v in updates.items():
            script_source.append("ctx._source['{}']='{}'".format(k, v))
        script_source = ";".join(script_source)
        body = {
            "script": {"source": script_source},
            "query": {"bool": {"must": query_must}}
        }
        ret = self.es.update_by_query(index, body)
        print(ret)

    def search(self, **kwargs):
        return self.es.search(**kwargs)

    def get_projects_stat(self, project_ids):
        assert isinstance(project_ids, list)
        index_id_set = set(project_ids)
        all_indexes = self.es.cat.indices('*', format='json')
        res = {}
        for i in all_indexes:
            if i['index'] in index_id_set:
                t = {
                    "index": i['index'],
                    "test_result_count": i['docs.count'],
                    "store_size": i['store.size'],
                }
                res[i['index']] = t
        return res

    def get_summary_info(self, project_ids):
        query_body = {
            "track_total_hits": True
        }
        search_obj = Search.from_dict(query_body)
        search_obj = search_obj.query("terms", _index=project_ids)
        search_obj.aggs.bucket('project_count', 'cardinality', field='_index')
        search_obj.aggs.bucket('testrun_count', 'cardinality', field='testrun_id.keyword')
        # print(search_obj.to_dict())
        es_data = self.common_search(
            search_obj=search_obj,
            index="*",
            limit=0,
            raw_result=True
        )
        print(es_data.aggregations)
        data = dict()
        data["total"] = es_data.hits.total.value
        data['project_count'] = len(project_ids)  # es_data.aggregations.project_count.value
        data['testrun_count'] = es_data.aggregations.testrun_count.value

        return data

    def insert_test_result(self, project_id, data):
        assert project_id
        assert isinstance(data, dict)
        data['index'] = project_id

        r = self.es.index(index=project_id, body=data)
        return r

    def search_test_result_field(self, project_id, key):
        query_body = {
            "collapse": {"field": f"{key}.keyword"}
        }
        search_obj = Search.from_dict(query_body)
        search_obj = search_obj.source([key]).sort({f"{key}.keyword": {"order": "asc"}})
        data = self.common_search(
            search_obj=search_obj,
            index=project_id)
        print(data)
        d = list()
        for t in data:
            i = t.get(key)
            if i:
                d.append(i)
        return d

    def get_testrun_list_id_only(self, project_id, params=None):
        if params is None:
            params = {}
        index = project_id
        limit = params.get("limit", 1000)
        if not isinstance(limit, int):
            limit = int(limit)
        env = params.get("env", '')
        suite = params.get("suite", '')

        query_body = {
            "collapse": {"field": "testrun_id.keyword"}
        }
        search_obj = Search.from_dict(query_body)
        if env and env != "all":
            search_obj = search_obj.query("match_phrase", env=env)
        if suite and suite != "all":
            search_obj = search_obj.query("match_phrase", suite_name=suite)
        search_obj = search_obj.source(['testrun_id']).sort({"testrun_id.keyword": {"order": "desc"}})
        data = self.common_search(
            search_obj=search_obj,
            index=index,
            limit=limit)
        d = list()
        for t in data:
            i = t.get('testrun_id')
            if i:
                d.append(i)
        return d

    def get_testrun_list_details(self, project_id, params=None):
        if params is None:
            params = {}
        index = project_id
        limit = params.get("limit", 10)
        if not isinstance(limit, int):
            limit = int(limit)
        testrun_id = params.get("testrun_id", None)
        env = params.get("env", '')
        suite = params.get("suite", '')

        search_obj = Search()
        if testrun_id:
            # search_obj = search_obj.filter("term", testrun_id=testrun_id)
            search_obj = search_obj.query("match_phrase", testrun_id=testrun_id)
        if env and env != "all":
            search_obj = search_obj.query("match_phrase", env=env)
        if suite and suite != "all":
            search_obj = search_obj.query("match_phrase", suite_name=suite)
        search_obj.aggs.bucket('testruns', 'terms', field='testrun_id.keyword', size=limit, order={"_term": "desc"}) \
            .metric('case_results', 'terms', field="case_result.keyword") \
            .metric('suite_name', 'terms', field="suite_name.keyword") \
            .metric('env', 'terms', field="env.keyword")

        es_data = self.common_search(
            search_obj=search_obj,
            index=index,
            limit=1,
            raw_result=True
        )
        # pprint(len(es_data.hits.hits))
        if not es_data:
            return []
        data = list()
        for testrun in es_data.aggregations.testruns.buckets:
            # print(testrun['env'].buckets)
            item = dict()
            item['testrun_id'] = testrun['key']
            try:
                item['env'] = testrun['env']['buckets'][0]['key']
                item['suite_name'] = testrun['suite_name']['buckets'][0]['key']
            except Exception as e:
                print(e)
            item['case_count'] = testrun['doc_count']
            for status in testrun['case_results']['buckets']:
                item[status['key']] = status['doc_count']
            if item.get('success') and item.get('case_count'):
                rate = float(item.get('success', 0)) / (item['case_count'] - item.get('skip', 0))
                item['success_rate'] = int(rate * 1000) / 10
            else:
                item['success_rate'] = 0
            data.append(item)
        # data.sort(key=lambda i: i['testrun_id'])
        # data.reverse()
        return data

    def search_test_results(self, project_id, params=None):
        assert project_id
        exist = check_project_exist(project_id)
        if not exist:
            return 404, f"Project ID '{project_id}' does not exist"
        index = project_id

        limit = params.get("limit", 10)
        if not isinstance(limit, int):
            limit = int(limit)
        if "limit" in params:
            del params['limit']
        offset = params.get("offset", 0)
        if not isinstance(offset, int):
            offset = int(offset)
        if "offset" in params:
            del params['offset']
        details_flag = params.get('details')
        if details_flag is True or isinstance(details_flag, str) and details_flag.lower() == 'true':
            del params['details']
            search_source = []
        else:
            search_source = self.search_source

        regexp_queries = list()
        multi_matches = list()

        if "keyword" in params:
            keyword = params['keyword']
            # keyword = keyword.replace(" ", "")
            # keyword = keyword.replace(".", " ")
            del params["keyword"]

            key_splits = keyword.split("&")
            for key_split in key_splits:
                # key_split = key_split
                kv = key_split.split(":", 1)
                if len(kv) == 2:
                    # format field:query_str
                    field = kv[0].strip()
                    value = ".*{}.*".format(kv[1].strip())

                    regexp_queries.append({
                        field: value
                    })
                else:
                    # full search string
                    multi_matches.append({
                        "query": key_split.strip(),
                        "type": "best_fields",
                        "fields": ["*"],
                        # "operator": "or"
                    })
            if len(regexp_queries) == 0 and len(multi_matches) == 0:
                multi_matches.append({
                    "query": keyword.strip(),
                    "type": "best_fields",
                    "fields": ["*"],
                    # "operator": "or"
                })
                # print('**************')

        query_must = list()
        for k, v in params.items():
            query_must.append({"match_phrase": {k: v}})

        query_body = {"query": {"bool": {"must": query_must}}}
        if regexp_queries:
            for regexp_q in regexp_queries:
                query_body["query"]["bool"]["must"].append({"regexp": regexp_q})
        if multi_matches:
            for multi_match in multi_matches:
                query_body["query"]["bool"]["must"].append({"multi_match": multi_match})

        query_body['track_total_hits'] = True
        search_obj = Search.from_dict(query_body)
        search_obj = search_obj.sort(
            {"testrun_id.keyword": {"order": "desc"}},
            {"case_id.keyword": {"order": "asc"}}
        )
        search_obj = search_obj.source(search_source)
        data, page_info = self.common_search(
            search_obj=search_obj,
            offset=offset,
            index=index,
            limit=limit,
            attach_id=True,
            with_page_info=True
        )
        return data, page_info


if __name__ == '__main__':
    es = ESTestResultDataStore()
    # print(es.get_index_list())
