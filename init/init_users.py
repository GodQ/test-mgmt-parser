
# from models.user_model import UserUtils, DuplicatedUserName
from models.user_model import *
from app_init import db, app
from config.config import Config


def init_users():
    users = Config.get_config('users')
    for user in users:
        user_name = user.get('name', 'user')
        user_password = user.get('password', 'password')
        user_role = user.get('role', 'developer')
        try:
            UserUtils.add_user(user_name, user_password, user_role)
        except DuplicatedUserName as e:
            print(f"User name {user_name} has existed")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_users()
