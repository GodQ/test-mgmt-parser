from elasticsearch import Elasticsearch
import copy
from pprint import pprint

hosts = ["10.110.124.130:9200"]
test_result_index = "test-result-*"
search_source = ['case_id', 'case_name', 'case_result', 'testrun_id', 'comment']
es = Elasticsearch(hosts=hosts)


def common_search(index, query_body, attach_id=False, **kwargs):
    query_body = copy.deepcopy(query_body)
    from_id = query_body.get('from', 0)
    b_size = query_body.get('size', None)
    if b_size is not None:
        limit = b_size
    k_limit = kwargs.get('limit', None)
    if k_limit is not None:
        limit = k_limit
        del kwargs['limit']

    total = None
    count = 0
    data = list()
    limited = False
    kwargs.update({
        'index': index,
        "body": query_body,
    })
    while not total or count < total:
        # print(total, count)
        query_body.update({"from": from_id, 'size': 100})
        kwargs['body'] = query_body
        print("\nES query:")
        pprint(kwargs)
        res = es.search(**kwargs)
        if not total:
            total = res['hits']['total']['value']
            if not total:
                break
        for hit in res['hits']['hits']:
            d = hit["_source"]
            if attach_id:
                d['index'] = hit['_index']
                d['doc_id'] = hit['_id']
            data.append(d)
            count += 1
            if count == limit:
                limited = True
                break
        if limited:
            break
        from_id = count
    return data


def get_summary():
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
    es_data = es.search(index=test_result_index, body=query_body)

    data["total"] = es_data['hits']['total']['value']
    data['index_count'] = es_data['aggregations']['index_count']['value']
    data['testrun_count'] = es_data['aggregations']['testrun_count']['value']

    return data


def get_testrun_list(params=None):
    if params is None:
        params = {}
    limit = params.get("limit", 10000)
    index = params.get("index", test_result_index)
    id_only = params.get("id_only", "true")
    if id_only != "true":
        return get_testrun_list_details(params)

    if not isinstance(limit, int):
        limit = int(limit)
    query_body = {"query": {"match_all": {}}}
    data = common_search(
        index=index,
        query_body=query_body,
        limit=limit,
        _source=['testrun_id'])
    testrun_set = set()
    for d in data:
        testrun_set.add(d['testrun_id'])
    data = [d for d in testrun_set]
    return data


def get_testrun_list_details(params=None):
    if params is None:
        params = {}
    index = params.get("index", test_result_index)
    limit = params.get("limit", 10)
    if not isinstance(limit, int):
        limit = int(limit)

    query_body = {
        "query": {"match_all": {}},
        "size": 0,
        "aggs": {
            "testruns": {
                "terms": {
                    "field": "testrun_id.keyword"
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

    es_data = es.search(index=index, body=query_body)
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
        if item['success'] and item['case_count']:
            item['success_rate'] = float(item['success']) / item['case_count'] * 100
        data.append(item)
    return data


def get_test_index_list(params=None):
    if params is None:
        params = {}
    limit = params.get("limit", 10000)
    if not isinstance(limit, int):
        limit = int(limit)
    query_body = {"query": {"match_all": {}}}
    data = common_search(
        index=test_result_index,
        query_body=query_body,
        limit=limit,
        attach_id=True,
        _source=['testrun_id'])
    index_set = set()
    for d in data:
        index_set.add(d['index'])
    data = [d for d in index_set]
    return data


def search_data(params=None):
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
        index = "test-result-vose"

    multi_matches = list()
    if "keyword" in params:
        keyword = params['keyword']
        keyword = keyword.replace(" ", "")
        del params["keyword"]

        key_splits = keyword.split("&")
        for key_split in key_splits:
            key_split = key_split
            kv = key_split.split(":")
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
    print(query_body)
    data = common_search(
        index=index,
        query_body=query_body,
        limit=limit,
        attach_id=True,
        _source=search_source)
    return data


def _update_es_by_query(index, queries, updates):
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
    ret = es.update_by_query(index, body)
    print(ret)


def update_data(items):
    updated = 0
    if isinstance(items, list):
        data = items
    else:
        data = [items]
    for i, d in enumerate(data):
        if d.get('case_id') and d.get('testrun_id') and d.get("index"):
            query = {
                'testrun_id': d.get('testrun_id'),
                "case_id": d.get('case_id')
            }
            update = {
                "comment": d.get('comment')
            }
            _update_es_by_query(d.get("index"), query, update)
            updated += 1
    return updated


if __name__ == '__main__':
    # print(get_test_index_list())
    # print(get_testrun_list())
    # print(search_data({'limit': 10})[0])
    # print(get_summary())
    print(get_testrun_details())
