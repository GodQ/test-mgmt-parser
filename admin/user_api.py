from . import bp
from flask import jsonify, request, make_response, abort, g
import json
import traceback

from common.user_model import User, add_user, list_users, load_user_by_name
from auth.auth import auth

# curl -v -X POST 127.0.0.1:5000/api/token -u root:password
# curl -v -X GET 127.0.0.1:5000/api/summary -H "Authorization: Bearer <token>"


@bp.route('/users', methods=['POST'])
@auth.login_required(role='admin')
def post_user():
    if not request.json:
        abort(make_response(jsonify(error="No user info"), 400))
    user_name = request.json.get('user_name')
    password = request.json.get('password')
    role = request.json.get('role', 'user')
    if user_name is None or password is None:
        abort(make_response(jsonify(error="user_name or password is missing"), 400))
    try:
        user = add_user(user_name=user_name, password=password, role=role)
        return {'user_name': user.user_name, 'id': user.id, 'role': user.role}
    except Exception as e:
        msg = str(e)
        abort(make_response(jsonify(error=msg), 400))


@bp.route('/users', methods=['GET'])
@auth.login_required(role='admin')
def get_all_users():
    users = list_users()
    return {'items': users}


@bp.route('/users/<user_name>', methods=['DELETE'])
def delete_user(user_name):
    try:
        user = load_user_by_name(user_name=user_name)
        user.delete()
        return {'status': 'Deleted', 'user_name': user.user_name, 'id': user.id, 'role': user.role}
    except Exception as e:
        msg = str(e)
        abort(make_response(jsonify(error=msg), 400))

