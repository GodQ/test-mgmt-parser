import records
import copy
from pprint import pprint

db = records.Database('sqlite:///test-result.db')


def insert_results(results):
    return 1


def get_summary():
    data = dict()
    data["total"] = es_data['hits']['total']['value']
    data['index_count'] = es_data['aggregations']['index_count']['value']
    data['testrun_count'] = es_data['aggregations']['testrun_count']['value']

    return data


def get_testrun_list(params=None):
    if params is None:
        params = {}
    id_only = params.get("id_only", "true")
    if id_only != "true":
        return get_testrun_list_details(params)
    else:
        return get_testrun_list_id_only(params)


def get_testrun_list_id_only(params=None):
    if params is None:
        params = {}
    index = params.get("index", test_result_index)
    limit = params.get("limit", 1000)
    if not isinstance(limit, int):
        limit = int(limit)

    return d


def get_testrun_list_details(params=None):
    if params is None:
        params = {}
    index = params.get("index", test_result_index)
    limit = params.get("limit", 10)
    if not isinstance(limit, int):
        limit = int(limit)
    return data


def get_test_index_list(params=None):
    if params is None:
        params = {}
    limit = params.get("limit", 10000)
    if not isinstance(limit, int):
        limit = int(limit)

    return data


def search_results(params=None):
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

    return data


def _update_es_by_query(index, queries, updates):

    print(ret)


def update_results(items):
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
    pprint(get_test_index_list())
    # pprint(get_testrun_list({"id_only": "true"}))
    # pprint(search_results({'limit': 100}))
    # pprint(get_summary())
    # pprint(get_testrun_list_details({"limit":3}))
