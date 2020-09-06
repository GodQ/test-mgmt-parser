from test_result.es.model import *


def init():
    # create the mappings in elasticsearch
    TestRusult.init()
    CaseBugMapping.init()


def load():
    test_result_list = [
        {
            'testrun_id': 'r1',
            'case_id': '1',
            'case_name': '1',
            'case_tags': [1, 2],
            'case_project': 'proj1',
            'suite_name': 's1',
            'env': 'env1',
            'result': 'success',
            'case_comment': 'c1',
            'stdout': 's1',
            'traceback': 't1'
        },
        {
            'testrun_id': 'r1',
            'case_id': '2',
            'case_name': '2',
            'case_tags': [1, 2],
            'case_project': 'proj1',
            'suite_name': 's1',
            'env': 'env1',
            'result': 'success',
            'case_comment': 'c1',
            'stdout': 's2',
            'traceback': 't2'
        },
        {
            'testrun_id': 'r2',
            'case_id': '1',
            'case_name': '1',
            'case_tags': [1, 2],
            'case_project': 'proj1',
            'suite_name': 's1',
            'env': 'env1',
            'result': 'success',
            'case_comment': 'c1',
            'stdout': 's1',
            'traceback': 't1'
        }
    ]
    for d in test_result_list:
        tr = TestRusult()
        for k in d.keys():
            setattr(tr, k, d[k])
        tr.save()

    bug_case_list = [
        {
            'bugs': '1',
            'case_id': '1',
            'case_project': '1'
        }
    ]
    for d in bug_case_list:
        cb = CaseBugMapping()
        for k in d.keys():
            setattr(cb, k, d[k])
        cb.save()


def clean():
    try:
        trs = TestRusult.search().execute()
        for tr in trs:
            tr.delete()
    except Exception as e:
        pass

    try:
        bcs = CaseBugMapping.search().execute()
        for cb in bcs:
            cb.delete()
    except Exception as e:
        pass


def search():
    c = TestRusult.search()[0:2].execute()
    print(c)
    print(c.hits)
    print(dir(c.hits))
    print(list(c.hits.hits)[0].to_dict())

# init()
# clean()
# load()
search()