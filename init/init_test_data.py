import http.client
import json
from config.config import Config

test_project_id = 'test'
port = Config.get_config('port')


def get_token():
    conn = http.client.HTTPConnection("localhost", port)
    payload = ''
    headers = {
      'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ='
    }
    conn.request("POST", "/api/access_token", payload, headers)
    res = conn.getresponse()
    assert res.status == 201, res.status
    data = res.read()
    access_token = json.loads(data.decode("utf-8")).get('access_token', None)
    assert access_token
    print(data.decode("utf-8"))
    return access_token


def post_test_result(project_id, auth_token: str, body: dict):
    conn = http.client.HTTPConnection("localhost", port)
    payload = json.dumps(body)
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
    conn.request("POST", f"/api/projects/{project_id}/test_results", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data)
    updated = json.loads(data.decode("utf-8")).get('updated', 0)
    return updated


def get_test_results(project_id):
    test_results = [
        {
            "case_id": "feature1.001",
            "project": project_id,
            "testrun_id": "2019-11-20 10:27:26",
            "case_result": "error",
            "suite_name": "sanity",
            "env": "dev0",
            "stdout": "a b c d",
            "traceback": "t1 t2 t3",
            "duration": 1.2
        },
        {
            "case_id": "feature1.002",
            "project": project_id,
            "testrun_id": "2019-11-20 10:27:26",
            "case_result": "success",
            "suite_name": "sanity",
            "env": "dev0",
            "stdout": "a b c d",
            "traceback": "t1 t2 t3",
            "duration": 2.7
        },
        {
            "case_id": "feature2.003",
            "project": project_id,
            "testrun_id": "2019-11-20 10:27:26",
            "case_result": "failure",
            "suite_name": "sanity",
            "env": "dev0",
            "stdout": "a b",
            "traceback": "t1 t2 t3",
            "duration": 3.9
        },
        {
            "case_id": "feature1.001",
            "project": project_id,
            "testrun_id": "2018-11-20 10:27:26",
            "case_result": "success",
            "suite_name": "sanity",
            "env": "dev1",
            "stdout": "a b c",
            "traceback": "t1 t2 t3",
            "duration": 1.3
        },
        {
            "case_id": "feature1.002",
            "project": project_id,
            "testrun_id": "2018-11-20 10:27:26",
            "case_result": "success",
            "suite_name": "sanity",
            "env": "dev1",
            "stdout": "d e",
            "traceback": "t1",
            "duration": 1.9
        },
        {
            "case_id": "feature2.003",
            "project": project_id,
            "testrun_id": "2018-11-20 10:27:26",
            "case_result": "failure",
            "suite_name": "sanity",
            "env": "dev1",
            "stdout": "f g",
            "traceback": "t1 t2",
            "duration": 2.1
        }
    ]
    return test_results


if __name__ == '__main__':
    auth_token = get_token()
    test_results = get_test_results(test_project_id)
    updated = 0
    for res in test_results:
        post_test_result(test_project_id, auth_token, res)
