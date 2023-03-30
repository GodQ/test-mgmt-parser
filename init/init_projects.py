
from models.test_mgmt_model import *
from app_init import db, app
from config.config import Config


if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()
        db.create_all()
        project_id = 'test'
        print(ProjectUtils.list_projects())
        print(ProjectUtils.create_project(project_id))
        print(ProjectUtils.list_projects())

        case_id = 'case'
        print(CaseUtils.list_cases())
        print(CaseUtils.list_cases(project_id))
        print(CaseUtils.update_cases(project_id, case_id, [1], 'aaa'))
        print(CaseUtils.list_cases())
        print(CaseUtils.list_cases(project_id))
        print(CaseUtils.update_cases(project_id, case_id, [1,2,3], 'bbb'))
        print(CaseUtils.list_cases())
        print(CaseUtils.list_cases(project_id))
