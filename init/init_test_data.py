import http.client
import json


def get_token():
    conn = http.client.HTTPConnection("localhost", 5000)
    payload = ''
    headers = {
      'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ='
    }
    conn.request("POST", "/api/token", payload, headers)
    res = conn.getresponse()
    data = res.read()
    token = json.loads(data.decode("utf-8")).get('token', None)
    print(data.decode("utf-8"))
    return token


def post_test_result(auth_token: str, body: dict):
    conn = http.client.HTTPConnection("localhost", 5000)
    payload = json.dumps(body)
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/api/test_result", payload, headers)
    res = conn.getresponse()
    data = res.read()
    updated = json.loads(data.decode("utf-8")).get('updated', 0)
    return updated


def get_test_results():
    test_results = [
        {
            "case_id": "001",
            "project": "demo1",
            "testrun_id": "2019-11-20 10:27:26",
            "case_result": "error",
            "suite_name": "sanity",
            "env": "dev0",
            "stdout": "a b c d",
            "traceback": "t1 t2 t3"
        },
        {
            "case_id": "002",
            "project": "demo1",
            "testrun_id": "2019-11-20 10:27:26",
            "case_result": "success",
            "suite_name": "sanity",
            "env": "dev0",
            "stdout": "a b c d",
            "traceback": "t1 t2 t3"
        },
        {
            "case_id": "003",
            "project": "demo1",
            "testrun_id": "2019-11-20 10:27:26",
            "case_result": "failure",
            "suite_name": "sanity",
            "env": "dev0",
            "stdout": "a b",
            "traceback": "t1 t2 t3"
        },
        {
            "case_id": "001",
            "project": "demo1",
            "testrun_id": "2018-11-20 10:27:26",
            "case_result": "success",
            "suite_name": "sanity",
            "env": "dev1",
            "stdout": "a b c",
            "traceback": "t1 t2 t3"
        },
        {
            "case_id": "002",
            "project": "demo1",
            "testrun_id": "2018-11-20 10:27:26",
            "case_result": "success",
            "suite_name": "sanity",
            "env": "dev1",
            "stdout": "d e",
            "traceback": "t1"
        },
        {
            "case_id": "003",
            "project": "demo1",
            "testrun_id": "2018-11-20 10:27:26",
            "case_result": "failure",
            "suite_name": "sanity",
            "env": "dev1",
            "stdout": "f g",
            "traceback": "t1 t2"
        }
    ]
    return test_results


if __name__ == '__main__':
    auth_token = get_token()
    test_results = get_test_results()
    updated = 0
    for res in test_results:
        post_test_result(auth_token, res)
