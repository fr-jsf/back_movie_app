from flask import Blueprint, jsonify, request
from flask.typing import StatusCode
from werkzeug.security import generate_password_hash
from utils import db_connection, token_required
from . import auth

app = Blueprint('users', __name__)


@app.route('/users')
@token_required
def getUsers(current_user):
    try:
        if current_user['role'] != 'ADMIN':
            return jsonify({
                'success': False,
                'message': 'Droits insuffisants'
            }), 401
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        if len(users) == 0:
            return jsonify({
                'success': True,
                'message': 'Aucun utilisateur trouvé'
            }), 404
        return jsonify({
            'success': True,
            'message': 'Utilisateurs trouvé(s)',
            'data': users
        }), 200
    except Exception as err:
        print(err)
        return jsonify({
            'success': False,
            'message': 'Erreur interne'
        }), 500


@app.route('/users/<string:tag>')
@token_required
def getUser(current_user, tag):
    if current_user['role'] != 'ADMIN' and not (current_user['user_tag'] == tag and current_user['role'] == 'USER'):
        return jsonify({
            'success': False,
            'message': 'Droits insuffisants'
        }), 403
    try:
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_tag = %s", tag)
        user = cursor.fetchone()
        if len(user) == 0:
            return jsonify({
                'success': True,
                'message': 'Aucun utilisateur trouvé'
            }), 404
        return jsonify({
            'success': True,
            'message': 'Utilisateur trouvé',
            'data': user
        }), 200
    except Exception as err:
        print(err)
        return jsonify({
            'success': False,
            'message': 'Erreur interne'
        }), 500


@app.route('/users', methods=['POST'])
def register():
    try:
        if auth.firstStep()[1] == 404 or auth.secondStep()[1] == 404:
            return jsonify({
                'success': False,
                'message': 'Inscription impossible'
            }), 404
        userData = request.form.to_dict()
        userData['user_password'] = generate_password_hash(
            userData['user_password'])
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users VALUES (%s, %s, %s, %s, %s, CURDATE())", [
                       userData['user_tag'], userData['user_name'], userData['user_picture'], userData['user_mail'], userData['user_password']])
        conn.commit()
        del userData['user_password']
        del userData['user_confirm_password']
        return jsonify({
            'success': True,
            'message': 'Utilisateur crée',
            'data': userData
        }), 201
    except Exception as err:
        print(err)
        return jsonify({
            'success': False,
            'message': 'Erreur interne'
        }), 500


@app.route('/users/<string:tag>', methods=['DELETE'])
@token_required
def deleteUser(current_user, tag):
    if current_user['role'] != 'ADMIN' and not (current_user['user_tag'] == tag and current_user['role'] == 'USER'):
        return jsonify({
            'success': False,
            'message': 'Droits insuffisants'
        }), 403
    try:
        conn = db_connection()
        cursor = conn.cursor()
        result = cursor.execute("DELETE FROM users WHERE user_tag = %s", tag)
        conn.commit()
        if result == 0:
            return jsonify({
                'success': True,
                'message': f'L’utilisateur {tag} n’existe pas'
            }), 404
        return jsonify({
            'success': True,
            'message': f'L’utilisateur {tag} a bien été supprimé'
        }), 204
    except Exception as err:
        print(err)
        return jsonify({
            'success': False,
            'message': 'Erreur interne'
        }), 500
