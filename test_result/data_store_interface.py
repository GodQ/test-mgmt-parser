import abc


def check_post_result_fields(func):
    def func_t(self, results):
        if not isinstance(results, list):
            results = [results]
        required_fields = ['testrun_id', 'case_id', 'case_result']
        optional_fields = ['case_tags', 'traceback', 'case_comment', 'suite_name', 'env', 'call_type', 'bugs']
        index_fields = ['index', 'project', 'content-category']
        for result in results:
            for f in required_fields:
                assert f in result, f"field {f} is required"
            index = None
            if 'index' in result:
                pass
            elif 'project' in result:
                index = f"{self.test_result_prefix}{result['project']}"
                result['index'] = index
                del result['project']
            elif 'content-category' in result:
                index = f"{self.test_result_prefix}{result['content-category']}"
                result['index'] = index
                del result['content-category']
            assert 'index' in result, f"No index or content-category or project field in result {result}"
            assert result['case_result'] in ['failure', 'success', 'error', 'skip'], \
                f"case_result must be in ['failure','success','error','skip'] but it is {result['case_result']}"
        return func(self, results)
    return func_t


class DataStoreBase(metaclass=abc.ABCMeta):
    test_result_prefix = "test-result-"

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
        or
        /api/testruns?index=test-result-demo&testrun_id=123
        {
            "data": [
                {
                    case_count: 505,
                    error: 6,
                    failure: 48,
                    success: 451,
                    success_rate: 89.3,
                    testrun_id: "123"
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

    @check_post_result_fields
    def batch_insert_results(self, results):
        count = 0
        for result in results:
            try:
                self.insert_results(result)
                count += 1
            except Exception as e:
                print(e)
        return count

    @abc.abstractmethod
    def insert_results(self, results):
        """
        results:
        [{
            "case_comment": "",
            "testrun_id": "2020-09-30-06-19-20",
            "method_name": "test_pa_get_top-app-usage_7",
            "module_name": "vflow.testcase_loader",
            "call_type": "schedule",
            "suite_name": "regression",
            "env": "alp100",
            "case_id": "vflow.testcase_loader.system.statistics.app.test_pa_get_top-app-usage_7",
            "func_doc": null,
            "content-category": "test-result-app-launchpad",
            "stdout": "",
            "case_result": "success",
            "case_tags": ["P2"],
            "class_name": "system.statistics.app",
            "traceback": ""
        }]
        """
        pass

    def get_diff_from_testrun(self, index: str, testruns: list):
        def load_testrun_result(index, testrun_id):
            testrun_result = {}
            results_error, page_info = self.search_results({"index": index,
                                                  "testrun_id": testrun_id,
                                                  "case_result": 'error',
                                                  "limit": 5000})
            for res in results_error:
                testrun_result[res['case_id']] = res
            results_failure, page_info = self.search_results({"index": index,
                                                    "testrun_id": testrun_id,
                                                    "case_result": 'failure',
                                                    "limit": 5000})
            for res in results_failure:
                testrun_result[res['case_id']] = res
            return testrun_result

        testrun_results = []
        id_all = set()
        for tr_id in testruns:
            tr_result = load_testrun_result(index, tr_id)
            testrun_results.append(tr_result)
            id_all.update(set(tr_result.keys()))

        diff = []
        for case_id in id_all:
            t = {"case_id": case_id, "results": []}
            for i, tr_result in enumerate(testrun_results):
                if case_id in tr_result:
                    t['results'].append({'testrun_id': testruns[i], "result": tr_result[case_id]['case_result']})
                else:
                    t['results'].append({'testrun_id': testruns[i], "result": "success"})
            diff.append(t)

        return diff
