from flask import Blueprint, jsonify, request, current_app
from marshmallow.utils import INCLUDE
from utils import db_connection
import datetime
import re
import jwt
from werkzeug.security import check_password_hash
from marshmallow import Schema, fields, ValidationError, validates_schema


app = Blueprint('auth', __name__)


@app.route('/auth', methods=['POST'])
def login():
    try:
        auth = request.form
        if not auth or not auth.get('user_mail') or not auth.get('user_password'):
            return jsonify({'success': False, 'message': 'Des données sont manquantes'}), 404
        user_mail = auth.get('user_mail')
        user_password = auth.get('user_password')
        if user_mail == current_app.config['ADMIN_USER'] and user_password == current_app.config['ADMIN_PASS']:
            token = jwt.encode({
                'user_tag': user_mail,
                'role': 'ADMIN',
                'exp': datetime.datetime.utcnow() + datetime.timedelta(weeks=8)
            }, current_app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({'success': True, 'message': 'Token créée', 'data': token}), 200
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_tag, user_password FROM users WHERE user_mail = %s", user_mail)
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'Adresse email ou mot de passe incorrect'}), 401
        if check_password_hash(user['user_password'], user_password):
            token = jwt.encode({
                'user_tag': user['user_tag'],
                'role': 'USER',
                'exp': datetime.datetime.utcnow() + datetime.timedelta(weeks=8)
            }, current_app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({'success': True, 'message': 'Token créée', 'data': token}), 200
        return jsonify({'success': False, 'message': 'Adresse email ou mot de passe incorrect'}), 403
    except Exception as err:
        print(err)
        return jsonify({'success': False, 'message': 'Erreur interne'}), 500


class FirstStep(Schema):
    user_mail = fields.String(required=True, error_messages={
        'required': 'Saisissez votre adresse email'
    })
    user_tag = fields.String(required=True, error_messages={
        'required': 'Saisissez votre nom d’utilisateur',
    })
    user_name = fields.String(required=True, error_messages={
        'required': 'Saisissez votre nom d’affichage',
    })
    user_picture = fields.String(required=True, error_messages={
        'required': 'Veuillez sélectionner une image'
    })

    @validates_schema()
    def validate_input(self, data, **kwargs):
        errors = dict()
        pattern = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
        pictures = current_app.config['USER_PICTURES']
        if not re.fullmatch(pattern, data['user_mail']):
            errors['user_mail'] = ['Veuillez saisir une adresse email valide']
        if len(data['user_tag']) not in range(3, 25):
            errors['user_tag'] = [
                'Votre nom d’utilisateur doit comporter entre 3 et 25 caractères']
        if len(data['user_name']) not in range(8, 50):
            errors['user_name'] = [
                'Votre nom d’utilisateur doit comporter entre 8 et 50 caractères']
        if data['user_picture'] not in pictures:
            errors['user_picture'] = ['L’image sélectionnée est invalide']
        if errors:
            raise ValidationError(errors)


class SecondStep(Schema):
    user_password = fields.String(required=True, error_messages={
        'required': 'Veuillez saisir votre mot de passe'
    })
    user_confirm_password = fields.String(required=True, error_messages={
        'required': 'Veuillez confirmer votre mot de passe'
    })

    @validates_schema()
    def validate_input(self, data, **kwargs):
        pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!@#$%^&*()_+,.\\\/;:"-]).{8,32}$'
        if not re.fullmatch(pattern, data['user_password']):
            raise ValidationError({'user_password': [
                                  'Utilisez entre 8 et 32 caractères dont une miniscule et une majuscule, un chiffre et un symbole']})


@app.route('/verify', methods=['POST'])
def dataVerification():
    auth_step = request.args.get('auth_step')
    if not auth_step:
        return jsonify({
            'success': False,
            'message': 'Veuillez spécifier le paramètre auth_step'
        }), 404
    if auth_step == "0":
        return firstStep()
    elif auth_step == "1":
        return secondStep()
    return jsonify({
        'success': False,
        'message': 'Le paramètre auth_step doit être compris entre 0 et 1'
    }), 404


def firstStep():
    try:
        userData = request.form.to_dict()
        schema = FirstStep(unknown=INCLUDE)
        user = schema.load(userData)
        result = schema.dump(user)
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_unique(%s, %s) AS RESULTAT",
                       [result['user_tag'], result['user_mail']])
        unique = cursor.fetchone()["RESULTAT"]
        if not unique:
            raise ValidationError(
                {'error': ['Email ou nom d’utilisateur déjà utilisé.']})
        return jsonify({
            'success': True,
            'message': 'Données correctes',
            'data': result
        }), 200
    except ValidationError as err:
        return jsonify({
            'success': False,
            'message': 'Données incorrectes',
            'data': err.messages
        }), 404


def secondStep():
    try:
        userData = request.form.to_dict()
        schema = SecondStep(unknown=INCLUDE)
        user = schema.load(userData)
        result = schema.dump(user)
        if result['user_password'] != result['user_confirm_password']:
            raise ValidationError(
                {'user_confirm_password': ['Ces mots de passe ne correspondent pas']})
        return jsonify({
            'success': True,
            'message': 'Données correctes',
            'data': result
        }), 200
    except ValidationError as err:
        return jsonify({
            'success': False,
            'message': 'Données incorrectes',
            'data': err.messages
        }), 404
