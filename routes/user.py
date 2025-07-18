from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import UserModel
from db import db
import jwt
from datetime import datetime, timedelta
import os

user_blueprint = Blueprint('user', __name__)

JWT_SECRET = os.environ.get('JWT_SECRET', 'CHANGE_ME')

@user_blueprint.route('/register', methods=['POST'])
def register():
    dados = request.json or {}
    if UserModel.find_by_username(dados['username']):
        return jsonify({'message': 'User already exists.'}), 400

    hashed_password = generate_password_hash(dados['password'])
    user = UserModel(username=dados['username'], password=hashed_password, plan=dados.get('plan', 'Gratuito'))
    user.save_to_db()

    return jsonify({'message': 'User created successfully.'}), 201

@user_blueprint.route('/login', methods=['POST'])
def login():
    dados = request.json or {}
    user = UserModel.find_by_username(dados['username'])

    if user and check_password_hash(user.password, dados['password']):
        token = jwt.encode({
            'sub': user.username,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, JWT_SECRET, algorithm='HS256')
        return jsonify({'token': token})

    return jsonify({'message': 'Invalid credentials.'}), 401
