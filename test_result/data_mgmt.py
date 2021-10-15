import time
from pprint import pprint

from test_result.data_mgmt_interface import DataMgmtInterface, check_project_exist
# from test_result.es.test_result_data_store import TestResultDataStore
from models.test_mgmt_model import CaseUtils, ProjectUtils
from test_result.data_store_factory import DataStore


class DataMgmt(DataMgmtInterface):
    test_result_data_store = DataStore()

    def get_summary(self):
        project_ids = self.get_project_list({'id_only': 'true'})
        data = self.test_result_data_store.get_summary_info(project_ids)
        return data

    def create_project(self, params):
        project_id = params.get('project_id')
        assert project_id
        exist = check_project_exist(self, project_id)
        if exist:
            return 409, f"Project ID '{project_id}' has existed"

        try:
            project = ProjectUtils.create_project(project_id)
            return 201, f'created {project.to_dict()}'
        except Exception as e:
            return 400, str(e)

    def get_project_list(self, params=None):
        if params is None:
            params = {}
        id_only = params.get("id_only", 'false')

        data = ProjectUtils.list_projects()
        index_ids = [i['project_id'] for i in data]
        if id_only == 'true':
            return index_ids
        else:
            projects_info = self.test_result_data_store.get_projects_stat(project_ids=index_ids)
            res = []
            for project in data:
                i = projects_info.get(project['project_id'])
                p = project
                if i:
                    t = {
                        "test_result_count": i['test_result_count'],
                        "store_size": i['store_size'],
                    }
                    p.update(t)
                else:
                    t = {
                        "test_result_count": 0,
                        "store_size": 0,
                    }
                    p.update(t)
                res.append(p)
            return res

    def get_project_settings(self, project_id):
        assert project_id
        exist = check_project_exist(self, project_id)
        if not exist:
            return 404, f"Project ID '{project_id}' does not exist"

        envs = self.test_result_data_store.search_test_result_field(project_id=project_id, key='env')
        suites = self.test_result_data_store.search_test_result_field(project_id=project_id, key='suite_name')
        res = {
            'envs': envs,
            'suites': suites
        }
        return res

    def get_testrun_list(self, project_id, params=None):
        assert project_id
        exist = check_project_exist(self, project_id)
        if not exist:
            return 404, f"Project ID '{project_id}' does not exist"

        id_only = params.get("id_only", "true")
        if "testrun_id" in params and params['testrun_id']:
            id_only = "false"
        id_only = id_only.lower()
        try:
            if id_only != "true":
                return self.test_result_data_store.get_testrun_list_details(project_id, params)
            else:
                return self.test_result_data_store.get_testrun_list_id_only(project_id, params)
        except Exception as e:
            return []

    def insert_result(self, project_id, r):
        if "timestamp" not in r:
            r['@timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()))
        if "created_time" not in r:
            r['created_time'] = r['@timestamp']
        self.test_result_data_store.insert_test_result(project_id=project_id, data=r)

    def search_results(self, project_id, params=None):
        assert project_id
        exist = check_project_exist(self, project_id)
        if not exist:
            return 404, f"Project ID '{project_id}' does not exist"

        data, page_info = self.test_result_data_store.search_test_results(project_id, params)
        if data:
            cases_info = CaseUtils.list_cases(project_id, data_type='dict')
            print(cases_info)
            if cases_info:
                for item in data:
                    item['project_id'] = item['index']
                    del item['index']
                    case_id = item['case_id']
                    if case_id in cases_info:
                        item['bugs'] = cases_info[case_id]['bugs']
                        item['comment'] = cases_info[case_id]['comment']
        return data, page_info

    def update_case_info(self, project_id, items):
        assert project_id
        exist = check_project_exist(self, project_id)
        if not exist:
            return 404, f"Project ID '{project_id}' does not exist"

        updated = 0
        assert isinstance(items, list)
        errors = []
        for i, d in enumerate(items):
            if not d.get('case_id'):
                continue
            case_id = d.get('case_id')
            bugs = d.get('bugs')
            comment = d.get('comment')
            try:
                CaseUtils.update_cases(project_id, case_id, bugs, comment)
                updated += 1
            except Exception as e:
                error_info = f"Error '{str(e)}' when update case info, " \
                             f"{project_id}, {case_id}, {bugs}, {comment}"
                errors.append(error_info)
        return 200, {"updated": updated, "total": len(items), "errors": errors}


if __name__ == '__main__':

    ds = DataMgmt()
    # r = ds.create_project({'project_id': 'aaa'})
    # pprint(r)
    # indexes = ds.get_project_list()
    # pprint(indexes)
    project_settings = ds.get_project_settings("test-result-alp-saas")
    pprint(project_settings)
    # pprint(ds.get_testrun_list_id_only())
    # pprint(ds.get_testrun_list({"id_only": "true"}))
    # pprint(ds.get_testrun_list({"id_only": "false"}))
    # pprint(ds.get_case_bugs_mapping(indexes[0]))
    # pprint(ds.get_summary())
    # pprint(ds.get_testrun_list_details({"limit":3}))
    # pprint(ds.search_results({'limit': 2}))
