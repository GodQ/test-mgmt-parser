import time
from app_init import db


class Case(db.Model):
    project_id = db.Column(db.String(80), primary_key=True)
    case_id = db.Column(db.String(80), primary_key=True)
    bugs = db.Column(db.String(512))
    comment = db.Column(db.String(512))

    def to_dict(self):
        t = {
            'project_id': self.project_id,
            'case_id': self.case_id,
            'bugs': self.bugs,
            'comment': self.comment,
        }
        return t


class Project(db.Model):
    project_id = db.Column(db.String(80), primary_key=True)
    created_time = db.Column(db.String(100))

    def to_dict(self):
        t = {
            'project_id': self.project_id,
            'created_time': self.created_time,
        }
        return t


class BadRequest(Exception):
    pass


class DuplicatedProject(Exception):
    pass


class NotExistProject(Exception):
    pass


class CaseUtils:
    @staticmethod
    def update_cases(project_id, case_id, bugs='', comment=''):
        if not bugs:
            bugs = ''
        if not comment:
            comment = ''
        # case = Case.query.filter_by(and_(Case.project_id==project_id, Case.case_id==case_id)).first()
        case = Case.query.filter_by(project_id=project_id).filter_by(case_id=case_id).first()
        if not case:
            case = Case(project_id=project_id, case_id=case_id)
            case.bugs = str(bugs)
            case.comment = str(comment)
            db.session.add(case)
        else:
            case.bugs = str(bugs)
            case.comment = str(comment)
        db.session.commit()
        return case.to_dict()

    @staticmethod
    def list_cases(project_id=None, data_type='dict'):
        if project_id:
            cases = Case.query.filter_by(project_id=project_id).all()
            # print('cases:', cases)
        else:
            cases = Case.query.all()
        if data_type == 'dict':
            ret = {}
            for c in cases:
                ret[c.case_id] = c.to_dict()
        else:
            ret = [c.to_dict() for c in cases]
        return ret


class ProjectUtils:
    @staticmethod
    def check_project_exist(project_id):
        project = Project.query.filter_by(project_id=project_id).first()
        if project:
            return True
        else:
            return False

    @staticmethod
    def create_project(project_id):
        project = Project.query.filter_by(project_id=project_id).first()
        if project:
            raise DuplicatedProject(f'Project {project_id} has existed')
        created_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()))
        project = Project(project_id=project_id, created_time=created_time)
        db.session.add(project)
        db.session.commit()
        return project

    @staticmethod
    def list_projects():
        projects = Project.query.all()
        ret = [p.to_dict() for p in projects]
        return ret

    @staticmethod
    def delete_project(project_id):
        project = Project.query.filter_by(project_id=project_id).first()
        if not project:
            raise NotExistProject(f'Project {project_id} did not exist')
        db.session.delete(project)
        db.session.commit()
        return project


if __name__ == '__main__':
    pass

