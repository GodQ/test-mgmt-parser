import abc


class DataStoreBase(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_testrun_list(self, params=None):
        """
        /api/testruns?index=test-result-demo&id_only=true
        response:
        {
            "data": [
                "2019-11-19 10:27:26",
                "2019-11-18 16:52:01",
                "2019-11-18 16:49:39",
                "2019-11-18 15:21:34",
            ]
        }
        or
        /api/testruns?index=test-result-demo&id_only=false&limit=10
        {
            "data": [
                {
                    case_count: 505,
                    error: 6,
                    failure: 48,
                    success: 451,
                    success_rate: 89.3,
                    testrun_id: "2020-01-16-16-09-23"
                }
            ]
        }
        """
        pass

    @abc.abstractmethod
    def get_test_index_list(self, params=None):
        """
        /api/test_index
        response:
        {
            "data": [
                "test-result-demo1",
                "test-result-demo2",
                "test-result-demo3"
            ]
        }
        """
        pass

    @abc.abstractmethod
    def search_results(self, params=None):
        """
            /api/test_result?index=test-result-demo&testrun_id=2019-11-19+10:27:26&keyword=error
            response:
            {
                "data": [
                    {
                        bugs: "123"
                        case_id: "test_lib.libs.testcase_loader.demo.test_aaa_1"
                        case_result: "failure"
                        comment: "None"
                        doc_id: "hyqVtW8B-V0jBDzk7Pyn"
                        index: "test-result-demo"
                        testrun_id: "2020-01-18-06-18-43"
                    }
                ]
            }
        """
        pass

    @abc.abstractmethod
    def update_results(self, items):
        """
            request:
            /api/test_result
            {
                "case_id": "TestDataProv#test01_data_prov_prov#22#2019-08-05-15_49_03",
                "case_result": "error",
                "doc_id": "V957gW4B6JSdAO9QIOkU",
                "index": "test-result-demo",
                "testrun_id": "2019-11-19 10:27:26",
                "comment": "111111"
            }
            response:
            {
                "updated": 1
            }
        """
        pass

    @abc.abstractmethod
    def get_summary(self):
        """
            /api/summary
            response:
            {
                "index_count": 3,
                "testrun_count": 160,
                "total": 1970
            }
        """
        pass

    @abc.abstractmethod
    def insert_results(self, results):
        pass
