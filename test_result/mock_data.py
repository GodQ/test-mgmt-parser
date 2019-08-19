import json
import os

data = []
data_path = os.path.join(os.path.dirname(__file__), "mock_data.json")
with open(data_path, "r") as fd:
    data_str = str(fd.read())
    data = json.loads(data_str)

def get_testrun_list(params=None):
    testrun_set = set()
    for d in data:
        testrun_set.add(d['testrun_id'])
    data = [d for d in testrun_set]
    return data

def get_test_index_list(params=None):
    index_set = set()
    for d in data:
        index_set.add(d['index'])
    data = [d for d in index_set]
    return data
    
def search_data(params=None):
    return data

def update_data(item):
    for i,d in enumerate(data):
        if d.get('case_id') == item.get('case_id') and d.get('testrun_id') == item.get('testrun_id'):
            data[i].update(item)
            return 1
    return 0
