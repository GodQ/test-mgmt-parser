from datetime import datetime
from elasticsearch_dsl import Document, Nested, Date, Integer, Keyword, Text, connections

# Define a default Elasticsearch client
connections.create_connection(hosts=["10.110.124.130:9200"])


class TestRusult(Document):
    testrun_id = Keyword()
    case_id = Keyword()
    case_name = Text()
    case_tags = Keyword()
    suite_name = Keyword()
    env = Keyword()
    result = Keyword()
    case_comment = Text()
    stdout = Text()
    traceback = Text()

    class Index:
        name = 'test-result-*'


class CaseBugMapping(Document):
    case_id = Keyword()
    bugs = Keyword()

    class Index:
        name = '*-case-bugs'

