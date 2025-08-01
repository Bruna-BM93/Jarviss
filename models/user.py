from db import db

class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    plan = db.Column(db.String(80), nullable=False, default='Gratuito')

    def __init__(self, username, password, plan='Gratuito'):
        self.username = username
        self.password = password
        self.plan = plan

    def json(self):
        return {"id": self.id, "username": self.username, "plan": self.plan}

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
