import records
import copy
from pprint import pprint

db = records.Database('sqlite:///test-result.db')


def insert_results(results):
    return 1


def get_summary():
    """
    /api/summary
    {
        "index_count": 3,
        "testrun_count": 160,
        "total": 1970
    }
    """
    return data


def search_results(params=None):
    """
    /api/test_result?index=test-result-app-launchpad&testrun_id=2019-11-19+10:27:26&keyword=error
    {
        "data": [
            {
                "case_id": "TestOnly#test_only#3#2019-08-12-10_35_58",
                "case_result": "failure",
                "doc_id": "kd49km4B6JSdAO9QQOn4",
                "index": "test-result-vose",
                "testrun_id": "2019-11-22 16:33:27"
            }
        ]
    }
    """
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


def get_testrun_list(params=None):
    """
    /api/testruns
    """
    if params is None:
        params = {}
    id_only = params.get("id_only", "true")
    if id_only != "true":
        return get_testrun_list_details(params)
    else:
        return get_testrun_list_id_only(params)


def get_testrun_list_id_only(params=None):
    """
    /api/testruns?index=test-result-app-launchpad&id_only=true
    {
        "data": [
            "2019-11-19 10:27:26",
            "2019-11-18 16:52:01",
            "2019-11-18 16:49:39",
            "2019-11-18 15:21:34",
        ]
    }
    """
    if params is None:
        params = {}
    index = params.get("index", test_result_index)
    limit = params.get("limit", 1000)
    if not isinstance(limit, int):
        limit = int(limit)

    return d


def get_testrun_list_details(params=None):
    """
    /api/testruns?index=test-result-app-launchpad&id_only=false&limit=10
    {
        "data": [
            {
                "case_count": 6,
                "success": 6,
                "success_rate": 100.0,
                "testrun_id": "2019-11-18 13:31:49"
            }
        ]
    }
    """
    if params is None:
        params = {}
    index = params.get("index", test_result_index)
    limit = params.get("limit", 10)
    if not isinstance(limit, int):
        limit = int(limit)
    return data


def get_test_index_list(params=None):
    """
    /api/test_index
    {
        "data": [
            "test-result-vose1",
            "test-result-app-launchpad",
            "test-result-vose"
        ]
    }
    """
    if params is None:
        params = {}
    limit = params.get("limit", 10000)
    if not isinstance(limit, int):
        limit = int(limit)

    return data


def update_results(items):
    """
    request:
    /api/test_result
    {
        "case_id": "TestDataProv#test01_data_prov_prov#22#2019-08-05-15_49_03",
        "case_result": "error",
        "doc_id": "V957gW4B6JSdAO9QIOkU",
        "index": "test-result-app-launchpad",
        "testrun_id": "2019-11-19 10:27:26",
        "comment": "111111"
    }
    response:
    {
        "updated": 1
    }
    """
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
