from . import bp
from flask import jsonify, request, make_response, abort, g
import json
import traceback

from auth.model import User, create_user, list_users
from auth.auth import auth, generate_auth_token

# curl -v -X POST 127.0.0.1:5000/api/token -u root:password
# curl -v -X GET 127.0.0.1:5000/api/summary -H "Authorization: Bearer <token>"


@bp.route('/users', methods=['POST'])
def post_user():
    if not request.json:
        abort(400, "No user info")
    user_name = request.json.get('user_name')
    password = request.json.get('password')
    if user_name is None or password is None:
        abort(400)  # missing arguments
    try:
        user = create_user(user_name=user_name, password=password)
        return {'user_name': user.username, 'id': user.id}
    except Exception as e:
        msg = str(e)
        abort(400, msg)


@bp.route('/users', methods=['GET'])
@auth.login_required(role='admin')
def get_all_users():
    users = list_users()
    return {'items': users}


@bp.route('/current_user', methods=['GET'])
@auth.login_required
def get_current_user():
    user = g.user
    return user.to_dict()


@bp.route('/token', methods=['POST'])
@auth.login_required
def get_auth_token():
    token = generate_auth_token(g.user)
    return jsonify({'token': token.decode('ascii')}), 201


