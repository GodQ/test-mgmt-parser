import traceback

from flask import jsonify, request, make_response, abort

from auth.auth import auth
from test_result.data_mgmt import DataMgmt
from . import bp

dm = DataMgmt()


@bp.route('/')
def index():
    return 'Hello!'


@bp.route('/summary', methods=['GET'])
@auth.login_required
def summary():
    summary = dm.get_summary()
    print(summary)
    return jsonify(summary), 200


@bp.route('/projects', methods=['GET'])
@auth.login_required
def test_project_list():
    args = request.args
    testruns = dm.get_project_list(args)
    resp = {
        "data": testruns
    }
    return jsonify(resp), 200


@bp.route('/projects/<string:project_id>/settings', methods=['GET'])
@auth.login_required
def project_settings(project_id):
    args = request.args.to_dict()
    settings = dm.get_project_settings(project_id)
    resp = {
        "data": settings
    }
    return jsonify(resp), 200


@bp.route('/projects', methods=['POST'])
@auth.login_required(role=['admin'])
def create_project():
    # print(request)
    # print(request.args)
    print('create new project:', request.data)
    # print(request.json)

    args = request.args
    body_json = request.json
    # print(request.content_type)
    if request.content_type != 'application/json':
        abort(make_response(jsonify(error="Only json is supported"), 400))

    if request.method == 'POST':
        if not body_json:
            resp = {
                "error": "no json body or header"
            }
            return jsonify(resp), 400

        project_id = body_json.get('project_id')

        status, resp = dm.create_project({'project_id': project_id})
        return jsonify(resp), status


@bp.route('/projects/<string:project_id>', methods=['DELETE'])
@auth.login_required
def delete_project(project_id):
    status, resp = dm.delete_project(project_id)
    return jsonify(resp), status


@bp.route('/projects/<string:project_id>/full_text_search', methods=['POST'])
@auth.login_required
def enable_project_full_text_search(project_id):
    status, resp = dm.enable_project_full_text_search(project_id)
    return jsonify(resp), status


@bp.route('/projects/<string:project_id>/index', methods=['POST'])
@auth.login_required
def create_project_index(project_id):
    args = request.args
    if str(args.get('full_text_search')).lower() == 'true':
        full_text_search = True
    else:
        full_text_search = False
    status, resp = dm.create_index(project_id, full_text_search)
    return jsonify(resp), status
