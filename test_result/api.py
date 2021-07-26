import traceback

from flask import jsonify, request, make_response, abort

from auth.auth import auth
from test_result.data_store import DataStore
from . import bp

# from .es.data_store import DataStore
# from .mock.mock_data_store import DataStore
# from .sql.sql_data_store import DataStore

ds = DataStore()


@bp.route('/')
def index():
    return 'Hello!'


@bp.route('/summary', methods=['GET'])
@auth.login_required
def summary():
    summary = ds.get_summary()
    print(summary)
    return jsonify(summary), 200


@bp.route('/projects', methods=['GET'])
@auth.login_required
def test_project_list():
    args = request.args
    testruns = ds.get_project_list(args)
    resp = {
        "data": testruns
    }
    return jsonify(resp), 200


@bp.route('/projects/<string:project_id>/testruns', methods=['GET'])
@auth.login_required
def testrun_list(project_id):
    args = request.args.to_dict()
    testruns = ds.get_testrun_list(project_id, args)
    resp = {
        "data": testruns
    }
    return jsonify(resp), 200


@bp.route('/projects/<string:project_id>/test_results', methods=['GET'])
@auth.login_required
def get_test_result(project_id):
    print(request)
    print(request.args)
    print(request.data)
    # print(request.json)

    args = request.args
    body_json = request.json

    if request.method == 'GET':
        params = request.args.to_dict()
        params['project_id'] = project_id
        if 'limit' not in params:
            params['limit'] = 10
        if 'offset' not in params:
            params['offset'] = 0
        try:
            data, page_info = ds.search_results(project_id, params)
            resp = {
                "data": data,
                "page_info": page_info
            }
            return jsonify(resp), 200
        except Exception as e:
            print("params:", params)
            traceback.print_exc()
            resp = {
                "error": str(e)
            }
            return jsonify(resp), 400


@bp.route('/projects/<string:project_id>/test_results', methods=['PATCH'])
@auth.login_required(role=['admin', 'developer'])
def update_test_result(project_id):
    print(request)
    print(request.args)
    print(request.data)
    # print(request.json)

    args = request.args
    body_json = request.json

    if request.method == 'PATCH':
        if not body_json:
            resp = {
                "error": "no json body or header"
            }
            return jsonify(resp), 400
        if isinstance(body_json, list):
            items = body_json
        else:
            items = [body_json]
        for i in items:
            i['project_id'] = project_id
        status, info = ds.update_results(project_id, items)
        resp = {
            "info": info
        }
        return jsonify(resp), status


@bp.route('/projects', methods=['POST'])
@auth.login_required(role=['admin'])
def create_project():
    print(request)
    print(request.args)
    print(request.data)
    # print(request.json)

    args = request.args
    body_json = request.json
    print(request.content_type)
    if request.content_type != 'application/json':
        abort(make_response(jsonify(error="Only json is supported"), 400))

    if request.method == 'POST':
        if not body_json:
            resp = {
                "error": "no json body or header"
            }
            return jsonify(resp), 400

        project_id = body_json.get('project_id')

        status, reason = ds.create_project({'project_id': project_id})
        resp = {
            "info": reason
        }

        return jsonify(resp), status


@bp.route('/projects/<string:project_id>/test_results', methods=['POST'])
@auth.login_required(role=['admin', 'developer'])
def post_test_results(project_id):
    print(request)
    print(request.args)
    print(request.data)
    # print(request.json)

    args = request.args
    body_json = request.json
    print(request.content_type)
    if request.content_type != 'application/json':
        abort(make_response(jsonify(error="Only json is supported"), 400))

    if request.method == 'POST':
        if not body_json:
            resp = {
                "error": "no json body or header"
            }
            return jsonify(resp), 400
        if not isinstance(body_json, list):
            body_json = [body_json]

        for i in body_json:
            i['project_id'] = project_id

        try:
            status, info = ds.batch_insert_results(project_id, body_json)
            resp = {
                "info": info
            }
        except Exception as e:
            error_msg = str(e)
            resp = {
                "error": error_msg
            }
            status = 400

        return jsonify(resp), status


@bp.route('/projects/<string:project_id>/test_result_diff', methods=['GET'])
@auth.login_required
def diff_test_result(project_id):
    '''
    /api/projects/project_id/test_result_diff?testruns=2020-10-18-07-19-13,2020-10-17-12-27-34,2020-10-13-06-19-28'
    '''
    print(request)
    print(request.args)
    print(request.data)
    # print(request.json)

    args = request.args
    body_json = request.json

    if request.method == 'GET':
        params = request.args.to_dict()
        params['project_id'] = project_id
        if "testruns" not in params:
            abort(make_response(jsonify(error="testruns must be set"), 400))
        testruns = params['testruns'].split(',')
        diff = ds.get_diff_from_testrun(project_id, testruns)
        testrun_summary = []
        for tr_id in testruns:
            tr_info = ds.get_testrun_list(
                project_id, {"testrun_id": tr_id, "id_only": 'false'}
            )
            if len(tr_info) > 0:
                testrun_summary.append(tr_info[0])
        resp = {
            "data": diff,
            "testruns": testruns,
            "summary": testrun_summary
        }
        return resp, 200
