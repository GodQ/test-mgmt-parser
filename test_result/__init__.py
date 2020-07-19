from flask import Blueprint
import os


bp = Blueprint("test_result", __name__, url_prefix="/api")


base_dir = os.path.dirname(__file__)
for file in os.listdir(base_dir):
    path = os.path.join(base_dir, file)
    if os.path.isfile(path) and file.endswith(".py") and file != "__init__.py":
        module = "{}.{}".format(__name__, file[:-3])
        print(module, __name__)
        __import__(module, globals(), locals(), __name__)


