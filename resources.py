from flask_restful import Resource, reqparse
from models import UserModel, IdeaModel, RevokedTokenModel
from run import db
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                jwt_required, jwt_refresh_token_required,
                                get_jwt_identity, get_raw_jwt)
from flask import request
import urllib, hashlib
from util import calculate_avergage

parser = reqparse.RequestParser()
parser.add_argument('name', help='This field cannot be blank', required=True)
parser.add_argument('email', help='This field cannot be blank', required=True)
parser.add_argument('password', help='This field cannot be blank',
                    required=True)


class UserRegistration(Resource):
    def __init__(self):
        self.reqparse_args = reqparse.RequestParser()
        self.reqparse_args.add_argument('name',
                                        help='This field cannot be blank',
                                        required=True)
        self.reqparse_args.add_argument('email',
                                        help='This field cannot be blank',
                                        required=True)
        self.reqparse_args.add_argument('password',
                                        help='This field cannot be blank',
                                        required=True)
        super(UserRegistration, self).__init__()

    def post(self):
        data = self.reqparse_args.parse_args()
        if UserModel.find_by_email(data['email']):
            return {
                'message': 'User {} already exists'.format(data['email'])}
        new_user = UserModel(
            name=data['name'],
            email=data['email'],
            password=UserModel.generate_hash(data['password'])
        )
        try:
            new_user.save_to_db()
            access_token = create_access_token(identity=data['email'])
            refresh_token = create_refresh_token(identity=data['email'])
            return {
                'message': 'User {} was created'.format(data['name']),
                'jwt': access_token,
                'refresh_token': refresh_token
            }
        except:
            return {'message': 'Something went wrong'}, 500
        return data


class UserLogin(Resource):
    def __init__(self):
        self.reqparse_args = reqparse.RequestParser()
        self.reqparse_args.add_argument('email',
                                        help='This field cannot be blank',
                                        required=True)
        self.reqparse_args.add_argument('password',
                                        help='This field cannot be blank',
                                        required=True)
        super(UserLogin, self).__init__()

    def post(self):
        data = self.reqparse_args.parse_args()
        current_user = UserModel.find_by_email(data['email'])
        if not current_user:
            return {
                'message': 'User {} doesn\'t exist'.format(data['email'])}

        if UserModel.verify_hash(data['password'], current_user.password):
            access_token = create_access_token(identity=data['email'])
            refresh_token = create_refresh_token(identity=data['email'])
            return {
                'jwt': access_token,
                'refresh_token': refresh_token
            }
        else:
            return {'message': 'Wrong credentials'}


class UserProfile(Resource):
    @jwt_required
    def get(self):
        current_user = UserModel.find_by_email(get_jwt_identity())
        if current_user:
            return {
                'name': current_user.name,
                'email': current_user.email,
                'avatar_url': generate_gravatar(current_user.email)
            }


class UserLogoutAccess(Resource):
    @jwt_required
    def post(self):
        print(request.headers.get('X-Access-Token'))
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'message': 'Refresh token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class Ideas(Resource):
    def __init__(self):
        self.reqparse_args = reqparse.RequestParser()
        self.reqparse_args.add_argument('content',
                                        help='This field cannot be blank',
                                        required=True)
        self.reqparse_args.add_argument('impact',
                                        help='This field cannot be blank',
                                        required=True)
        self.reqparse_args.add_argument('ease',
                                        help='This field cannot be blank',
                                        required=True)
        self.reqparse_args.add_argument('confidence',
                                        help='This field cannot be blank',
                                        required=True)
        super(Ideas, self).__init__()

    @jwt_required
    def post(self):
        current_user = UserModel.find_by_email(get_jwt_identity())
        data = self.reqparse_args.parse_args()
        new_idea = IdeaModel(
            content=data['content'],
            impact=data['impact'],
            ease=data['ease'],
            confidence=data['confidence'],
            user_id=current_user.id
        )
        try:
            new_idea.save_to_db()
            return {
                'id': new_idea.id,
                'content': new_idea.content,
                'impact': new_idea.impact,
                'ease': new_idea.ease,
                'confidence': new_idea.confidence,
                'average': calculate_avergage(new_idea),
                'created_at': new_idea.created_at,

            }
        except:
            return {'message': 'Something went wrong'}, 500

    @jwt_required
    def delete(self, id):
        idea = IdeaModel.find_by_id(id)
        if idea:
            db.session.delete(idea)
            db.session.commit()
        else:
            return  {"msg": "Resource not found"}, 404

    @jwt_required
    def get(self, id):
        print("GET CALLED")

    @jwt_required
    def get(self):
        print("HERE")
        return IdeaModel.return_paginated()


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return {'jwt': access_token}


class SecretResource(Resource):
    def get(self):
        return {
            'answer': 42
        }


def generate_gravatar(email):
    gravatar_url = "https://www.gravatar.com/avatar/" + \
                   hashlib.md5(email).hexdigest() + "?"
    default = "mm"
    size = 100
    gravatar_url += urllib.urlencode({'d': default, 's': str(size)})
    return gravatar_url

