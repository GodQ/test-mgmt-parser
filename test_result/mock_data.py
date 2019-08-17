import json
import os

data = []
data_path = os.path.join(os.path.dirname(__file__), "mock_data.json")
with open(data_path, "r") as fd:
    data_str = str(fd.read())
    data = json.loads(data_str)


def search_data(params=None):
    return data

def update_data(item):
    for i,d in enumerate(data):
        if d.get('case_id') == item.get('case_id') and d.get('testrun_id') == item.get('testrun_id'):
            data[i].update(item)
            return 1
    return 0
