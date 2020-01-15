import records

db = records.Database('sqlite:///test-result.db')


create_db_sql = """
CREATE DATABASE test-results;
CREATE TABLE test-results
(
    doc_id datetime,
    testrun_id varchar(255),
    env varchar(255),
    call_type varchar(255),
    suite_name varchar(255),
    method_name varchar(1024),
    case_id varchar(1024),
    func_doc varchar(1024),
    stdout varchar(1024000),
    traceback varchar(10240),
    case_tags varchar(1024),
    case_result varchar(255),
    index varchar(255),
    bugs varchar(255)
);
"""