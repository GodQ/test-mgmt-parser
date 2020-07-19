from test_result.data_store_interface import DataStoreBase


class MockDataStore(DataStoreBase):
    def get_testrun_list(self, params=None):
        testrun_list_id_only = {
            "data": [
                "2019-11-19 10:27:26",
                "2019-11-18 16:52:01",
                "2019-11-18 16:49:39",
                "2019-11-18 15:21:34",
            ]
        }
        testrun_list_details = {
            "data": [
                {
                    "case_count": 505,
                    "error": 6,
                    "failure": 48,
                    "success": 451,
                    "success_rate": 89.3,
                    "testrun_id": "2020-01-16-16-09-23"
                }
            ]
        }
        if params is None:
            params = {}
        id_only = params.get("id_only", "true")
        if id_only != "true":
            return testrun_list_details
        else:
            return testrun_list_id_only

    def get_test_index_list(self, params=None):
        response = {
            "data": [
                "test-result-demo1",
                "test-result-demo2",
                "test-result-demo3"
            ]
        }
        return response

    def search_results(self, params=None):
        response = {
            "data": [
                {
                    "bugs": "123",
                    "case_id": "test_lib.libs.testcase_loader.demo.test_aaa_1",
                    "case_result": "failure",
                    "comment": "None",
                    "doc_id": "hyqVtW8B-V0jBDzk7Pyn",
                    "index": "test-result-demo",
                    "testrun_id": "2020-01-18-06-18-43"
                }
            ]
        }
        return response

    def update_results(self, items):

        response = {
            "updated": 1
        }
        return response

    def get_summary(self):
        response = {
            "index_count": 3,
            "testrun_count": 160,
            "total": 1970
        }
        return response

    def insert_results(self, results):
        pass


DataStore = MockDataStore