from . import bp
from flask import jsonify, request, make_response
import json

# from .mock_data import get_testrun_list, get_test_index_list, search_data, update_data
from .es_test_result import get_testrun_list, get_test_index_list, search_results, update_results, get_summary


@bp.route('/')
def index():
    return 'Hello!'


@bp.route('/summary', methods=['GET'])
def summary():
    summary = get_summary()
    print(summary)
    return summary, 200


@bp.route('/test_index', methods=['GET'])
def test_index_list():
    args = request.args
    testruns = get_test_index_list(args)
    resp = {
        "data": testruns
    }
    return jsonify(resp), 200


@bp.route('/testruns', methods=['GET'])
def testrun_list():
    args = request.args
    testruns = get_testrun_list(args)
    resp = {
        "data": testruns
    }
    return jsonify(resp), 200


@bp.route('/test_result', methods=['GET', 'PATCH'])
def test_result():
    print(request)
    print(request.args)
    print(request.data)
    # print(request.json)

    args = request.args
    body_json = request.json

    if request.method == 'GET':
        params = request.args.to_dict()
        if 'limit' not in params:
            params['limit'] = 500
        data = search_results(params)
        resp = {
            "data": data
        }
        return jsonify(resp), 200
    elif request.method == 'PATCH':
        if not body_json:
            resp = {
                "error": "no json body or header"
            }
            return jsonify(resp), 400
        updated = update_results(body_json)
        resp = {
            "updated": updated
        }
        if updated == 0:
            status = 404
        else:
            status = 201
        return jsonify(resp), status
