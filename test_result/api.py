from . import bp
from flask import jsonify, request, make_response, abort
import json
import traceback
from test_result.data_store import DataStore
from auth.auth import auth

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


@bp.route('/test_index', methods=['GET'])
@auth.login_required
def test_index_list():
    args = request.args
    testruns = ds.get_test_index_list(args)
    resp = {
        "data": testruns
    }
    return jsonify(resp), 200


@bp.route('/testruns', methods=['GET'])
@auth.login_required
def testrun_list():
    args = request.args
    testruns = ds.get_testrun_list(args)
    resp = {
        "data": testruns
    }
    return jsonify(resp), 200


@bp.route('/test_result', methods=['GET'])
# @auth.login_required
def get_test_result():
    print(request)
    print(request.args)
    print(request.data)
    # print(request.json)

    args = request.args
    body_json = request.json

    if request.method == 'GET':
        params = request.args.to_dict()
        if 'limit' not in params:
            params['limit'] = 10
        if 'offset' not in params:
            params['offset'] = 0
        try:
            data, page_info = ds.search_results(params)
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


@bp.route('/test_result', methods=['PATCH'])
@auth.login_required
def update_test_result():
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
        updated = ds.update_results(body_json)
        resp = {
            "updated": updated
        }
        if updated == 0:
            status = 404
        else:
            status = 201
        return jsonify(resp), status


@bp.route('/test_result', methods=['POST'])
@auth.login_required
def post_test_result():
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
        updated = ds.insert_results(body_json)
        resp = {
            "updated": updated
        }
        if updated == 0:
            status = 404
        else:
            status = 201
        return jsonify(resp), status

