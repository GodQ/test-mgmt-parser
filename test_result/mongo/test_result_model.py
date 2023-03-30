from datetime import datetime
from mongoengine import connect, Document, StringField, ListField, DictField, MultiLineStringField
# Define a default Mongo client
from config.config import Config
connect(Config.get_config('mongo_url'))


class TestRusult(Document):
    testrun_id = StringField()
    case_id = StringField()
    case_name = StringField()
    case_tags = ListField()
    suite_name = StringField()
    env = StringField()
    result = StringField()
    case_comment = StringField()
    stdout = StringField()
    traceback = StringField()

