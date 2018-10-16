from run import db
from passlib.hash import pbkdf2_sha256 as sha256
from util import calculate_avergage
import calendar
import time


class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255),  nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

class IdeaModel(db.Model):
    __tablename__ = 'ideas'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255),  nullable=False)
    impact = db.Column(db.Integer,  nullable=False)
    ease = db.Column(db.Integer,  nullable=False)
    confidence = db.Column(db.Integer,  nullable=False)
    created_at= db.Column(db.Integer,   nullable=False, default=calendar.timegm(time.gmtime()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            nullable=False)
    user = db.relationship('UserModel',
                               backref=db.backref('ideas', lazy=True))


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def return_paginated(cls):
        def to_json(x):
            return {
                 'id': x.id,
                'content': x.content,
                'impact': x.impact,
                'ease': x.ease,
                'confidence': x.confidence,
                'average': calculate_avergage(x),
                'created_at': x.created_at,
            }

        return list(map(lambda x: to_json(x), IdeaModel.query.limit(10).all()))


class RevokedTokenModel(db.Model):
    __tablename__ = 'revoked_tokens'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120))

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = cls.query.filter_by(jti=jti).first()
        return bool(query)

