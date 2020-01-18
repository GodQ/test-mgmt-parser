from . import bp
from flask import jsonify, request, make_response
import json

from .es_data_store import DataStore
# from .mock_data_store import DataStore

ds = DataStore()


@bp.route('/')
def index():
    return 'Hello!'


@bp.route('/summary', methods=['GET'])
def summary():
    summary = ds.get_summary()
    print(summary)
    return summary, 200


@bp.route('/test_index', methods=['GET'])
def test_index_list():
    args = request.args
    testruns = ds.get_test_index_list(args)
    resp = {
        "data": testruns
    }
    return jsonify(resp), 200


@bp.route('/testruns', methods=['GET'])
def testrun_list():
    args = request.args
    testruns = ds.get_testrun_list(args)
    resp = {
        "data": testruns
    }
    return jsonify(resp), 200


@bp.route('/test_result', methods=['GET', 'PATCH', 'POST'])
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
        data = ds.search_results(params)
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
        updated = ds.update_results(body_json)
        resp = {
            "updated": updated
        }
        if updated == 0:
            status = 404
        else:
            status = 201
        return jsonify(resp), status
    elif request.method == 'POST':
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
