import abc
import time


def check_post_result_fields(func):
    def func_t(self, results):
        if not isinstance(results, list):
            results = [results]
        required_fields = ['testrun_id', 'case_id', 'case_result']
        optional_fields = ['case_tags', 'traceback', 'case_comment', 'suite_name', 'env', 'call_type', 'bugs']
        project_id_fields = ['project_id', 'index', 'project', 'content-category']
        for result in results:
            for f in required_fields:
                assert f in result, f"field {f} is required"
            project_id = None
            if 'project_id' in result:
                pass
            elif 'index' in result:  # index is project_id
                result['project_id'] = result['index']
                del result['index']
            elif 'project' in result:  # project name should add prefix as project_id
                project_id = f"{self.test_result_prefix}{result['project']}"
                result['project_id'] = project_id
                del result['project']
            elif 'content-category' in result:  # content-category should add prefix as project_id
                project_id = f"{self.test_result_prefix}{result['content-category']}"
                result['project_id'] = project_id
                del result['content-category']
            assert 'project_id' in result, f"No project_id or content-category or project field in result {result}"
            assert result['case_result'] in ['failure', 'success', 'error', 'skip'], \
                f"case_result must be in ['failure','success','error','skip'] but it is {result['case_result']}"
        return func(self, results)

    return func_t


class ProjectsCache:
    projects_cache = dict()  # project_id => expire time
    EXPIRE_TIME = 60  # cache item expire after 60s

    @classmethod
    def hit(cls, project_id):
        if project_id not in cls.projects_cache:  # not match
            return False
        elif cls.projects_cache[project_id] < time.time():  # match but expire
            del cls.projects_cache[project_id]
            return False
        else:  # hit, refresh expire time
            cls.projects_cache[project_id] = time.time() + cls.EXPIRE_TIME
            return True

    @classmethod
    def add(cls, project_id):
        cls.projects_cache[project_id] = time.time() + cls.EXPIRE_TIME

    @classmethod
    def refresh(cls, projects):
        expire_time = time.time() + cls.EXPIRE_TIME
        for p in projects:
            cls.projects_cache[p] = expire_time


def check_project_exist(data_store, project_id):
    ret = ProjectsCache.hit(project_id)
    if ret:
        return True
    projects = data_store.get_project_list({"id_only": 'true'})
    ProjectsCache.refresh(projects)
    return ProjectsCache.hit(project_id)


class DataMgmtInterface(metaclass=abc.ABCMeta):
    test_result_prefix = "test-result-"

    @abc.abstractmethod
    def get_testrun_list(self, project_id, params=None):
        """
        /api/projects/project_id/testruns?id_only=true
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
        /api/projects/project_id/testruns?id_only=false&limit=10
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
        /api/projects/project_id/testruns?testrun_id=123
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
    def get_project_list(self, params=None):
        """
        /api/projects
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
    def get_project_settings(self, project_id):
        """
        GET /projects/<string:project_id>/settings
        {
            "envs": ['alp100', 'alp103'],
            "suites": ["regression", "smoke"]
        }
        """
        pass

    @abc.abstractmethod
    def create_project(self, params):
        """
        POST /api/projects
        {
            "project_id": "aaa"
        }
        response:
        {
            "project_id": "aaa"
        }
        """
        pass

    @abc.abstractmethod
    def search_results(self, project_id, params=None):
        """
            /api/projects/project_id/test_result?testrun_id=2019-11-19+10:27:26&keyword=error
            response:
            {
                "data": [
                    {
                        bugs: "123"
                        case_id: "test_lib.libs.testcase_loader.demo.test_aaa_1"
                        case_result: "failure"
                        comment: "None"
                        doc_id: "hyqVtW8B-V0jBDzk7Pyn"
                        project_id: "test-result-demo"
                        testrun_id: "2020-01-18-06-18-43"
                    }
                ]
            }
        """
        pass

    @abc.abstractmethod
    def update_case_info(self, project_id, items):
        """
            request:
            /api/projects/project_id/test_results
            {
                "case_id": "TestDataProv#test01_data_prov_prov#22#2019-08-05-15_49_03",
                "case_result": "error",
                "doc_id": "V957gW4B6JSdAO9QIOkU",
                "project_id": "test-result-demo",
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
                "project_count": 3,
                "testrun_count": 160,
                "total": 1970
            }
        """
        pass

    # @check_post_result_fields
    def batch_insert_results(self, project_id, results):
        assert project_id
        exist = check_project_exist(self, project_id)
        if not exist:
            return 404, f"Project ID '{project_id}' does not exist"

        count = 0
        for result in results:
            try:
                self.insert_result(project_id, result)
                count += 1
            except Exception as e:
                print(e)
        return 201, {'updated': count}

    @abc.abstractmethod
    def insert_result(self, project_id, result):
        """
        result:
        {
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
        }
        """
        pass

    def get_diff_from_testrun(self, project_id: str, testruns: list):
        def load_testrun_result(project_id, testrun_id):
            testrun_result = {}
            error_failure_id_set = set()
            params = {
                "testrun_id": testrun_id,
                # "case_result": 'skip',
                "limit": 5000}
            results_all, page_info = self.search_results(project_id, params)
            for res in results_all:
                testrun_result[res['case_id']] = res
                if res['case_result'] in ['error', 'failure']:
                    error_failure_id_set.add(res['case_id'])
            print("error_failure_id_set")
            print(error_failure_id_set)
            return testrun_result, error_failure_id_set

        testrun_results = []
        error_failure_id_all = set()
        for tr_id in testruns:
            tr_result, error_failure_id_set = load_testrun_result(project_id,
                                                                  tr_id)  # get all cases and error+failure cases of every testrun
            testrun_results.append(tr_result)
            error_failure_id_all = error_failure_id_all.union(error_failure_id_set)  # get all case id

        diff = []
        error_failure_id_all = list(error_failure_id_all)
        error_failure_id_all.sort()
        for case_id in error_failure_id_all:  # for every case id
            t = {"case_id": case_id, "results": []}
            for i, tr_result in enumerate(testrun_results):  # for every testrun, fill the case result
                case_result = ""
                if case_id in tr_result:
                    case_result = tr_result[case_id]['case_result']
                t['results'].append({'testrun_id': testruns[i], "result": case_result})
            diff.append(t)

        return diff
