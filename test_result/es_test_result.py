from elasticsearch import Elasticsearch
import copy

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
        query_body.update({"from": from_id, 'size': 100})
        kwargs['body'] = query_body
        res = es.search(**kwargs)
        if not total:
            total = res['hits']['total']['value']
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



def get_testrun_list(params=None):
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
        _source=['testrun_id'])
    testrun_set = set()
    for d in data:
        testrun_set.add(d['testrun_id'])
    data = [d for d in testrun_set]
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
    query_body = {"query": {"match_all": {}}}
    data = common_search(
        index=test_result_index, 
        query_body=query_body,
        limit=limit, 
        attach_id=True,
        _source=search_source)
    return data


def update_data(item):
    for i,d in enumerate(data):
        if d.get('case_id') == item.get('case_id') and d.get('testrun_id') == item.get('testrun_id'):
            data[i].update(item)
            return 1
    return 0


if __name__ == '__main__':
    print(get_test_index_list())
    # print(get_testrun_list())
    # print(search_data({'limit':10})[0])