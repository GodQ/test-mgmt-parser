from elasticsearch import Elasticsearch
import elasticsearch
import copy
import sys
import time
from pprint import pprint
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch, Match
from elasticsearch_dsl import connections, Document, Nested, Date, Integer, Keyword, Text

from test_result.data_store_interface import DataStoreBase

# Define a default Elasticsearch client
connections.create_connection(hosts=["10.110.124.130:9200"])


class ElasticSearchOperation:
    def __init__(self):
        hosts = ["10.110.124.130:9200"]
        self.es = Elasticsearch(hosts=hosts)

    def search(self, **kwargs):
        return self.es.search(**kwargs)

    def index(self, **kwargs):
        return self.es.index(**kwargs)

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
        search_obj = search_obj[offset: offset+limit]
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


class ElasticSearchDataStore(DataStoreBase):
    es = ElasticSearchOperation()
    test_result_index = "{}*".format(DataStoreBase.test_result_prefix)
    search_source = ['case_id', 'case_result', 'testrun_id', 'comment']

    def get_case_bugs_mapping_index(self, index):
        project = index.replace(self.test_result_prefix, "", 1)
        mapping_index = project.strip() + "_case_bugs"
        return mapping_index

    def insert_results(self, results):
        if not isinstance(results, list):
            results = [results]
        count = 0
        for r in results:
            index = r.get('index')
            if not index:
                print(f"No index or content-category or project field in result {r}")
                continue
            if not index.startswith(self.test_result_prefix):
                index = f"{self.test_result_prefix}{index}"
            if "timestamp" not in r:
                r['@timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()))
            if "created_time" not in r:
                r['created_time'] = r['@timestamp']
            self.es.index(index=index, body=r)
            count += 1
        return count

    def get_summary(self):
        data = dict()

        query_body = {
            "track_total_hits": True
        }
        # es_data = self.es.search(index=self.test_result_index, body=query_body)
        search_obj = Search.from_dict(query_body)
        search_obj.aggs.bucket('index_count', 'cardinality', field='_index')
        search_obj.aggs.bucket('testrun_count', 'cardinality', field='testrun_id.keyword')
        es_data = self.es.common_search(
            search_obj=search_obj,
            index=self.test_result_index,
            limit=0,
            raw_result=True
        )

        data["total"] = es_data.hits.total.value
        data['index_count'] = es_data.aggregations.index_count.value
        data['testrun_count'] = es_data.aggregations.testrun_count.value

        return data

    def get_testrun_list(self, params=None):
        if params is None:
            params = {}
        id_only = params.get("id_only", "true")
        if "testrun_id" in params and params['testrun_id']:
            id_only = "false"
        id_only = id_only.lower()
        if id_only != "true":
            return self.get_testrun_list_details(params)
        else:
            return self.get_testrun_list_id_only(params)

    def get_testrun_list_id_only(self, params=None):
        if params is None:
            params = {}
        index = params.get("index", self.test_result_index)
        limit = params.get("limit", 1000)
        if not isinstance(limit, int):
            limit = int(limit)
        query_body = {
            "collapse": {"field": "testrun_id.keyword"}
        }
        search_obj = Search.from_dict(query_body)
        search_obj = search_obj.source(['testrun_id']).sort({"testrun_id.keyword": {"order": "desc"}})
        data = self.es.common_search(
            search_obj=search_obj,
            index=index,
            limit=limit)
        d = list()
        for t in data:
            i = t.get('testrun_id')
            if i:
                d.append(i)
        return d

    def get_testrun_list_details(self, params=None):
        if params is None:
            params = {}
        index = params.get("index", self.test_result_index)
        limit = params.get("limit", 10)
        if not isinstance(limit, int):
            limit = int(limit)
        testrun_id = params.get("testrun_id", None)

        search_obj = Search()
        if testrun_id:
            # search_obj = search_obj.filter("term", testrun_id=testrun_id)
            search_obj = search_obj.query("match_phrase", testrun_id=testrun_id)
        search_obj.aggs.bucket('testruns', 'terms', field='testrun_id.keyword', size=limit, order={"_term": "desc"})\
            .metric('case_results', 'terms', field="case_result.keyword") \
            .metric('suite_name', 'terms', field="suite_name.keyword") \
            .metric('env', 'terms', field="env.keyword")
        es_data = self.es.common_search(
            search_obj=search_obj,
            index=index,
            limit=1,
            raw_result=True
        )
        # pprint(len(es_data.hits.hits))
        if not es_data:
            return {}
        data = list()
        for testrun in es_data.aggregations.testruns.buckets:
            # print(testrun['env'].buckets)
            item = dict()
            item['testrun_id'] = testrun['key']
            item['env'] = testrun['env']['buckets'][0]['key']
            item['suite_name'] = testrun['suite_name']['buckets'][0]['key']
            item['case_count'] = testrun['doc_count']
            for status in testrun['case_results']['buckets']:
                item[status['key']] = status['doc_count']
            if item.get('success') and item.get('case_count'):
                item['success_rate'] = int(float(item['success']) / item['case_count'] * 1000)/10
            else:
                item['success_rate'] = 0
            data.append(item)
        # data.sort(key=lambda i: i['testrun_id'])
        data.reverse()
        return data

    def get_test_index_list(self, params=None):
        if params is None:
            params = {}
        limit = params.get("limit", 10000)
        if not isinstance(limit, int):
            limit = int(limit)

        search_obj = Search()
        search_obj.sort({"_index": {"order": "desc"}})
        search_obj = search_obj.source(['testrun_id'])
        # print(search_obj.to_dict())
        data = self.es.common_search(
            search_obj=search_obj,
            index=self.test_result_index,
            limit=limit,
            attach_id=True)
        index_set = set()
        for d in data:
            index_set.add(d['index'])
        data = [d for d in index_set]
        return data

    def search_results(self, params=None):
        if params is None:
            params = {}
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
        if "index" in params:
            index = params["index"]
            del params["index"]
        else:
            index = "test-result-*"
            # raise Exception("Index is required")
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
        data, page_info = self.es.common_search(
            search_obj=search_obj,
            offset=offset,
            index=index,
            limit=limit,
            attach_id=True,
            with_page_info=True
        )
        if data:
            case_bugs_mapping = self.get_case_bugs_mapping(index)
            if case_bugs_mapping:
                for item in data:
                    case_id = item['case_id']
                    if case_id in case_bugs_mapping:
                        item['bugs'] = case_bugs_mapping[case_id]
        return data, page_info

    def update_results(self, items):
        updated = 0
        if isinstance(items, list):
            data = items
        else:
            data = [items]
        for i, d in enumerate(data):
            if d.get('case_id') and d.get('testrun_id') and d.get("index"):
                # update comment in test-results index
                query = {
                    'testrun_id': d.get('testrun_id'),
                    "case_id": d.get('case_id')
                }
                update = {}
                if 'comment' in d:
                    update['comment'] = d.get('comment')
                if update:
                    self.es.update_es_by_query(d.get("index"), query, update)

                # update bugs in case bugs mapping index
                if 'bugs' in d:
                    mapping_index = self.get_case_bugs_mapping_index(d.get("index"))
                    data = {
                            "case_id": d.get('case_id'),
                            "bugs": d.get('bugs')
                    }
                    ret = self.es.index(index=mapping_index, body=data, id=d.get('case_id'))
                    print(ret)

                updated += 1
        return updated

    def get_case_bugs_mapping(self, index):
        mapping_index = self.get_case_bugs_mapping_index(index)
        try:
            search_obj = Search()
            mapping = self.es.common_search(search_obj=search_obj, index=mapping_index)
            if not mapping:
                mapping = {}
            t = dict()
            for m in mapping:
                if 'case_id' in m and 'bugs' in m:
                    t[m['case_id']] = m['bugs']
            mapping = t
        except elasticsearch.exceptions.NotFoundError as e:
            mapping = {}
        return mapping


DataStore = ElasticSearchDataStore

if __name__ == '__main__':
    ds = ElasticSearchDataStore()
    # indexes = ds.get_test_index_list()
    # pprint(indexes)
    # pprint(ds.get_testrun_list_id_only())
    # pprint(ds.get_testrun_list({"id_only": "true"}))
    # pprint(ds.get_testrun_list({"id_only": "false"}))
    # pprint(ds.get_case_bugs_mapping(indexes[0]))
    # pprint(ds.get_summary())
    # pprint(ds.get_testrun_list_details({"limit":3}))
    pprint(ds.search_results({'limit': 2}))
