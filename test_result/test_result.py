from . import bp
from flask import jsonify, request, make_response
import json

from .mock_data import search_data, update_data


@bp.route('/')
def index():
    return 'Hello!'


@bp.route('/test_result', methods=['GET', 'PATCH'])
def test_result():
    print(request)
    print(request.args)
    print(request.data)
    # print(request.json)

    args = request.args
    body_json = request.json

    if request.method == 'GET':
        params = request.args
        data = search_data(params)
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
        updated = update_data(body_json)
        resp = {
            "updated": updated
        }
        if updated == 0:
            status = 404
        else:
            status = 201
        return jsonify(resp), status
