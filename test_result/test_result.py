from . import bp
from flask import jsonify, request

from .es_test_result import search_data


@bp.route('/')
def index():
    return 'Hello!'


@bp.route('/test_result', methods=['GET', 'PATCH'])
def test_result():
    print(request)
    print(request.args)
    print(request.data)
    print(request.json)

    if request.method == 'GET':
        params = request.args
        data = search_data(params)
        resp = {
            "data": data
        }
        return jsonify(resp), 200
    elif request.method == 'PATCH':
        params = request.args
        data = search_data(params)
        resp = {
            "data": data
        }
        return jsonify(resp), 200
