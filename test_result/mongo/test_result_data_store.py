import pymongo
from pprint import pprint

from config.config import Config
from test_result.data_mgmt_interface import check_project_exist
from test_result.data_store_interface import TestResultDataStoreInterface

MONGO_URL = Config.get_config('mongo_url')
MONGO_DB = Config.get_config('mongo_db')


def reformat_params(params: dict):
    if params is None:
        params = {}

    limit = params.get("limit", None)
    if not limit:
        limit = 10
    if not isinstance(limit, int):
        limit = int(limit)
    params['limit'] = limit

    offset = params.get("offset", 0)
    if not offset:
        offset = 0
    if not isinstance(offset, int):
        offset = int(offset)
    params['offset'] = offset

    with_page_info = params.get("with_page_info", True)
    if isinstance(with_page_info, str) and with_page_info.lower() == 'false':
        with_page_info = False
    else:
        with_page_info = True
    params['with_page_info'] = with_page_info

    suite_name = params.get("suite_name", '') or params.get("suite", '')
    params['suite_name'] = suite_name

    return params


class MongoTestResultDataStore(TestResultDataStoreInterface):
    search_source = ['case_id', 'case_result', 'testrun_id', 'comment']

    def __init__(self):
        self.mongo_client = pymongo.MongoClient(MONGO_URL)
        self.db = self.mongo_client[MONGO_DB]

    def create_project(self, project_id, enable_full_text=True):
        assert isinstance(project_id, str) and project_id
        self.db.create_collection(project_id)
        if enable_full_text is True:
            self.enable_full_text_search(project_id)

    def enable_full_text_search(self, project_id):
        assert isinstance(project_id, str) and project_id
        self.db[project_id].create_index([("$**", pymongo.TEXT)], background=False)

    def get_project_stat(self, project_id, params=None):
        assert isinstance(project_id, str)
        stats = self.db.command("collstats", project_id)
        testrun_ids = self.get_testrun_list_id_only(project_id)
        testrun_count = len(testrun_ids)
        t = {
                "index": project_id,
                "project_id": project_id,
                "test_result_count": stats['count'],
                "store_size": stats['storageSize'],
                "testrun_count": testrun_count
            }
        return t

    def get_projects_stat(self, project_ids):
        assert isinstance(project_ids, list)
        res = {}
        for project_id in project_ids:
            stat = self.get_project_stat(project_id)
            res[project_id] = stat
        return res

    def get_summary_info(self, project_ids):
        db_stats = self.db.command("dbstats")
        # print(db_stats)
        data = dict()
        data["total"] = db_stats['objects']
        data['project_count'] = db_stats['collections'] - 1  # base is the default collection
        data["store_size"] = db_stats['storageSize']

        testrun_count = 0
        for p in project_ids:
            testrun_ids = self.get_testrun_list_id_only(p)
            testrun_count += len(testrun_ids)
        data['testrun_count'] = testrun_count

        return data

    def get_testrun_list_id_only(self, project_id, params=None):
        if not params:
            params = {}
        if not params.get('limit'):
            params['limit'] = 999999
        params = reformat_params(params)
        offset = params.get("offset", 0)
        limit = params.get("limit", 10)
        env = params.get("env", 'all')
        suite_name = params.get("suite_name", 'all')

        # queries = {}
        # if env:
        #     queries['env'] = env
        # if suite_name:
        #     queries['suite_name'] = suite_name
        # testrun_ids = self.db[project_id].distinct(key='testrun_id', filter=queries)
        pipeline = [
            {"$project": {'testrun_id': 1}},
            {'$group': {'_id': "$testrun_id"}},
            # {'$group': {'_id': "$testrun_id", 'count': {'$sum': 1}}}
        ]
        if env and env != 'all':
            pipeline.insert(0, {'$match': {'env': env}})
        if suite_name and suite_name != 'all':
            pipeline.insert(0, {'$match': {'suite_name': suite_name}})
        testrun_ids_cursor = self.db[project_id].aggregate(pipeline)
        testrun_ids = [i['_id'] for i in list(testrun_ids_cursor)]
        testrun_ids.sort(reverse=True)
        return testrun_ids[offset: offset + limit]

    def get_testrun_list_details(self, project_id, params=None):
        params = reformat_params(params)
        offset = params.get("offset", 0)
        limit = params.get("limit", 10)
        env = params.get("env", 'all')
        suite_name = params.get("suite_name", 'all')
        testrun_id = params.get("testrun_id", None)

        queries = {}
        if env:
            queries['env'] = env
        if suite_name:
            queries['suite_name'] = suite_name

        pipeline = []
        if env and env != 'all':
            pipeline.append({'$match': {'env': env}})
        if suite_name and suite_name != "all":
            pipeline.append({'$match': {'suite_name': suite_name}})
        if testrun_id:
            pipeline.append({'$match': {'testrun_id': testrun_id}})

        # pipeline.append({'$sort': {'testrun_id': -1}})
        # pipeline.append({'$group': {'_id': "$testrun_id",
        #                             'case_results': {'$push': '$case_result'},
        #                             'suite_name': {'$last': '$suite_name'},
        #                             'env': {'$last': '$env'},
        #                             }})
        pipeline.append({
            '$group': {
                '_id': {
                    'testrun_id': "$testrun_id",
                    'case_result': "$case_result"
                },
                'count': {'$sum': 1},
                'suite_name': {'$last': '$suite_name'},
                'env': {'$last': '$env'},
        }})

        testrun_ids_cursor = self.db[project_id].aggregate(pipeline)
        testruns = {}
        for i in list(testrun_ids_cursor):
            testrun_id = i['_id']['testrun_id']
            case_result = i['_id']['case_result']
            count = i['count']
            if testrun_id not in testruns:
                suite_name = i['suite_name']
                env = i['env']
                testruns[testrun_id] = {
                    'testrun_id': testrun_id,
                    'suite_name': suite_name,
                    'env': env,
                    'case_count': 0
                }
            testruns[testrun_id][case_result] = count
            testruns[testrun_id]['case_count'] += count

        data = list()
        for testrun in testruns.values():
            if testrun.get('success') and testrun.get('case_count'):
                rate = float(testrun.get('success', 0)) / (testrun['case_count'] - testrun.get('skip', 0))
                testrun['success_rate'] = int(rate * 1000) / 10
            else:
                testrun['success_rate'] = 0
            data.append(testrun)
        data.sort(key=lambda t: t['testrun_id'], reverse=True)
        # data.reverse()
        return data[offset: offset + limit]

    def insert_test_result(self, project_id, data):
        assert project_id
        assert isinstance(data, dict)
        data['project_id'] = project_id

        r = self.db[project_id].insert_one(document=data)
        return r

    def search_test_result_field(self, project_id, key):
        values = self.db[project_id].distinct(key)
        return values

    def search_test_results(self, project_id, params=None):
        assert project_id
        # exist = check_project_exist(project_id)
        # if not exist:
        #     return 404, f"Project ID '{project_id}' does not exist"
        params = reformat_params(params)
        offset = params.get("offset", 0)
        limit = params.get("limit", 10)
        env = params.get("env", 'all')
        suite_name = params.get("suite_name", 'all')
        with_page_info = params.get("with_page_info", True)
        details_flag = params.get('details')
        if details_flag is True or isinstance(details_flag, str) and details_flag.lower() == 'true':
            search_source = None
        else:
            search_source = self.search_source

        queries = {}

        if params.get("testrun_id", None):
            queries['testrun_id'] = params['testrun_id']
        if params.get("case_id", None):
            queries['case_id'] = params['case_id']
        if params.get("case_result", None):
            t = params['case_result'].split(',')
            queries['case_result'] = {'$in': t}

        if "keyword" in params:
            keyword = params['keyword']
            # keyword = keyword.replace(" ", "")
            # keyword = keyword.replace(".", " ")
            del params["keyword"]

            key_splits = keyword.split("&")
            for key_split in key_splits:
                # key_split = key_split
                kv = key_split.split(":", 1)
                if len(kv) == 2:
                    # format field:query_str
                    field = kv[0].strip()
                    value = ".*{}.*".format(kv[1].strip())
                    queries[field] = {'$regex': value}
                else:
                    # full search string
                    queries['$text'] = {"$search": key_split}
        print('filter:')
        pprint(queries)
        sort_config = [
                    ('testrun_id', pymongo.DESCENDING),
                    ('case_id', pymongo.ASCENDING)]
        # search
        test_results_cursor = self.db[project_id].find(filter=queries, projection=search_source).\
            sort(sort_config)
        test_results = list(test_results_cursor.skip(offset).limit(limit))
        for tr in test_results:
            tr['_id'] = str(tr['_id'])

        if with_page_info is True:
            total_count = test_results_cursor.count(with_limit_and_skip=False)
            page_info = {
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
        else:
            page_info = None
        return test_results, page_info


if __name__ == '__main__':
    mongo = MongoTestResultDataStore()
    projects = ['test', 'test-1']
    doc = {
            "case_id": "new",
            "project": "demo1",
            "testrun_id": "2018-11-20 10:27:26",
            "case_result": "error",
            "suite_name": "sanity",
            "env": "dev2"
        }
    # print(mongo.get_testrun_list_id_only(projects[0]))
    # print(mongo.get_testrun_list_details(projects[0]))
    # mongo.insert_test_result(projects[0], doc)
    # print(mongo.get_projects_stat(projects))
    # print(mongo.get_summary_info(projects))
    # print(mongo.search_test_result_field(projects[0], 'env'))
    # pprint(mongo.search_test_results(projects[0]))
    params = {
        'with_page_info': 'true',
        # 'keyword': 'case_result:success&env:dev0', # match
        'keyword': 'b',   # full text search
        'offset': 0,
        'limit': 3,
        'details': True
    }
    pprint(mongo.search_test_results(projects[0], params))
