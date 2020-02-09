from elasticsearch import Elasticsearch
import elasticsearch
import copy
from pprint import pprint

from test_result.data_store_interface import DataStoreBase


class ElasticSearchOperation:
    def __init__(self):
        hosts = ["10.110.124.130:9200"]
        self.es = Elasticsearch(hosts=hosts)

    def search(self, **kwargs):
        return self.es.search(**kwargs)

    def index(self, **kwargs):
        return self.es.index(**kwargs)

    def common_search(self, index, query_body, attach_id=False, **kwargs):
        query_body = copy.deepcopy(query_body)
        b_size = query_body.get('size', None)
        limit = 100
        if b_size is not None:
            limit = b_size
        k_limit = kwargs.get('limit', None)
        if k_limit is not None:
            limit = k_limit
            del kwargs['limit']

        data = list()
        kwargs.update({
            'index': index,
            "body": query_body,
        })
        query_body.update({'size': limit})
        kwargs['body'] = query_body
        print("\nES query:")
        pprint(kwargs)
        res = self.es.search(**kwargs)
        for hit in res['hits']['hits']:
            d = hit["_source"]
            if attach_id:
                d['index'] = hit['_index']
                d['doc_id'] = hit['_id']
            data.append(d)
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
    test_result_prefix = "test-result-"
    test_result_index = "{}*".format(test_result_prefix)
    search_source = ['case_id', 'case_result', 'testrun_id', 'comment', 'bugs']

    def get_case_bugs_mapping_index(self, index):
        project = index.replace(self.test_result_prefix, "", 1)
        mapping_index = project.strip() + "_case_bugs"
        return mapping_index

    def insert_results(self, results):
        return

    def get_summary(self):
        data = dict()

        query_body = {
            "size": 0,
            "aggs": {
                "index_count": {
                    "cardinality": {
                        "field": "_index"
                    }
                },
                "testrun_count": {
                    "cardinality": {
                        "field": "testrun_id.keyword"
                    }
                },
            }
        }
        es_data = self.es.search(index=self.test_result_index, body=query_body)

        data["total"] = es_data['hits']['total']['value']
        data['index_count'] = es_data['aggregations']['index_count']['value']
        data['testrun_count'] = es_data['aggregations']['testrun_count']['value']

        return data

    def get_testrun_list(self, params=None):
        if params is None:
            params = {}
        id_only = params.get("id_only", "true")
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
            "query": {"match_all": {}},
            "collapse": {"field": "testrun_id.keyword"},
            "sort": {"testrun_id.keyword": {"order": "desc"}}
        }
        data = self.es.common_search(
            index=index,
            query_body=query_body,
            limit=limit,
            _source=['testrun_id'])
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

        query_body = {
            "query": {"match_all": {}},
            "size": 0,
            "aggs": {
                "testruns": {
                    "terms": {
                        "field": "testrun_id.keyword",
                        "size": limit,
                        "order": {
                            "_term": "desc"
                        }
                    },
                    "aggs": {
                        "case_results": {
                            "terms": {
                                "field": "case_result.keyword"
                            }
                        }
                    }
                },
            }
        }

        es_data = self.es.search(index=index, body=query_body)
        # pprint(es_data)
        if not es_data:
            return {}
        data = list()
        for testrun in es_data['aggregations']['testruns']['buckets']:
            item = dict()
            item['testrun_id'] = testrun['key']
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
        query_body = {
            "query": {"match_all": {}},
            "sort": {"_index": {"order": "desc"}}
        }
        data = self.es.common_search(
            index=self.test_result_index,
            query_body=query_body,
            limit=limit,
            attach_id=True,
            _source=['testrun_id'])
        index_set = set()
        for d in data:
            index_set.add(d['index'])
        data = [d for d in index_set]
        return data

    def search_results(self, params=None):
        if params is None:
            params = {}
        limit = params.get("limit", 100)
        if not isinstance(limit, int):
            limit = int(limit)
        del params['limit']
        if "index" in params:
            index = params["index"]
            del params["index"]
        else:
            index = "test-result-*"
        details_flag = params.get('details')
        if details_flag == True or isinstance(details_flag, str) and details_flag.lower()=='true':
            del params['details']
            search_source = ""
        else:
            search_source = self.search_source

        multi_matches = list()
        if "keyword" in params:
            keyword = params['keyword']
            keyword = keyword.replace(" ", "")
            del params["keyword"]

            key_splits = keyword.split("&")
            for key_split in key_splits:
                key_split = key_split
                kv = key_split.split(":", 1)
                if len(kv) == 2:
                    multi_matches.append({
                        "query": kv[1],
                        "type": "phrase_prefix",
                        "fields": [kv[0]]
                    })
                else:
                    multi_matches.append({
                        "query": key_split,
                        "type": "phrase_prefix",
                        "fields": ["*"]
                    })
            if len(multi_matches) == 0:
                multi_matches.append({
                    "query": keyword,
                    "type": "phrase_prefix",
                    "fields": ["*"]
                })

        query_must = list()
        for k, v in params.items():
            query_must.append({"match_phrase": {k: v}})

        query_body = {"query": {"bool": {"must": query_must}}}
        if multi_matches:
            for multi_match in multi_matches:
                query_body["query"]["bool"]["must"].append({"multi_match": multi_match})
        query_body['sort'] = {"testrun_id.keyword": {"order": "desc"}}
        pprint(query_body)
        
        data = self.es.common_search(
            index=index,
            query_body=query_body,
            limit=limit,
            attach_id=True,
            _source=search_source)
        if data:
            case_bugs_mapping = self.get_case_bugs_mapping(index)
            if case_bugs_mapping:
                for item in data:
                    case_id = item['case_id']
                    if case_id in case_bugs_mapping:
                        item['bugs'] = case_bugs_mapping[case_id]
        return data


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
                update = {
                    "comment": d.get('comment'),
                    "bugs": d.get('bugs')
                }
                self.es.update_es_by_query(d.get("index"), query, update)

                # update bugs in case bugs mapping index
                query = {
                    "case_id": d.get('case_id')
                }
                update = {
                    "bugs": d.get('bugs')
                }
                mapping_index = self.get_case_bugs_mapping_index(d.get("index"))
                try:
                    self.es.update_es_by_query(mapping_index, query, update)
                except elasticsearch.exceptions.NotFoundError as e:
                    data = {
                        "case_id": d.get('case_id'),
                        "bugs": d.get('bugs')
                    }
                    self.es.index(index=mapping_index, body=data)

                updated += 1
        return updated

    def get_case_bugs_mapping(self, index):
        mapping_index = self.get_case_bugs_mapping_index(index)
        try:
            mapping = self.es.common_search(mapping_index, query_body={})
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
    indexes = ds.get_test_index_list()
    pprint(indexes)
    pprint(ds.get_case_bugs_mapping(indexes[0]))
    # pprint(ds.get_testrun_list({"id_only": "true"}))
    # pprint(ds.search_results({'limit': 100}))
    # pprint(ds.get_summary())
    # pprint(ds.get_testrun_list_details({"limit":3}))
