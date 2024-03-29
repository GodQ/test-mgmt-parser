import abc


class TestResultDataStoreInterface(metaclass=abc.ABCMeta):
    search_source = ['case_id', 'case_result', 'testrun_id', 'comment']

    def __init__(self):
        pass

    # def search(self, **kwargs):
    #     return self.es.search(**kwargs)

    def create_project(self, project_id, enable_full_text=True):
        '''
        create project storage, and enable full test search
        '''
        pass

    def create_index(self, project_id, full_text_search=False):
        '''
        create index for project
        '''
        pass

    def enable_full_text_search(self, project_id):
        '''
        enable_full_text_search for project
        '''
        pass

    def get_projects_stat(self, project_ids):
        '''
        get project stat list
        '''
        pass

    def get_summary_info(self, project_ids):
        '''
        get summary info for all projects
        '''
        pass

    def insert_test_result(self, project_id, data):
        '''
        insert one test case result
        '''
        pass

    def search_test_result_field(self, project_id, key):
        '''
        Get one key data, for example env list or suite list
        '''
        pass

    def get_testrun_list_id_only(self, project_id, params=None):
        '''
        get test run list id
        '''
        pass

    def get_testrun_list_details(self, project_id, params=None):
        '''
        get test run details list
        '''
        pass

    def search_test_results(self, project_id, params=None):
        '''
        search test results
        '''
        pass


if __name__ == '__main__':
    pass
