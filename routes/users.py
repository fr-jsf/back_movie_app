from flask import Blueprint, jsonify, request
from cerberus import Validator
from werkzeug.security import generate_password_hash
from utils import db_connection, token_required

app = Blueprint('users', __name__)

v = Validator({
    'user_name': {
        'type': 'string',
        'minlength': 3,
        'maxlength': 100,
        'required': True
    },
    'user_mail': {
        'type': 'string',
        'minlength': 8,
        'maxlength': 255,
        'required': True,
        'regex': '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'
    },
    'user_password': {
        'type': 'string',
        'minlength': 8,
        'maxlength': 50,
        'required': True,
        'regex': '^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).*$'
    },
    'user_picture': {
        'type': 'string',
        'allowed': ['default.jpg', 'girlBabyFace.jpg'],
        'default': 'default.jpg'
    },
    'user_tag': {
        'type': 'string',
        'minlength': 3,
        'maxlength': 25,
        'required': True
    }
})


@app.route('/users')
def getUsers():
    try:
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        if len(users) == 0:
            return jsonify({
                'success': True,
                'message': 'No user found'
            }), 404
        return jsonify({
            'success': True,
            'message': 'User(s) found',
            'data': users
        })
    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'Internal error'
        }), 500


@app.route('/users/<string:tag>')
@token_required
def getUser(current_user, tag):
    if current_user['user_tag'] != tag:  # Check if the role is admin too
        return jsonify({
            'success': False,
            'message': 'Insuffisant rights'
        }), 403
    try:
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_tag = %s", tag)
        userData = cursor.fetchone()
        if len(userData) == 0:
            return jsonify({
                'success': True,
                'message': 'No user found'
            })
        return jsonify({
            'success': True,
            'message': 'User found',
            'data': userData
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal error'
        }), 500


@app.route('/users', methods=['POST'])
def register():
    try:
        userData = request.form.to_dict()
        if v.validate(userData):  # Now check if all the data is correct
            conn = db_connection()
            cursor = conn.cursor()
            userData = v.document
            cursor.execute("SELECT is_unique(%s, %s) AS RESULTAT",
                           [userData['user_tag'], userData['user_mail']])
            result = cursor.fetchone()["RESULTAT"]
            if not result:
                return jsonify({
                    'success': False,
                    'message': 'Mail or tag already exists',
                })
            userData['user_password'] = generate_password_hash(
                userData['user_password'])
            cursor.execute(
                "INSERT INTO users VALUES (%s, %s, %s, %s, %s, CURDATE())",
                [userData['user_tag'], userData['user_name'], userData['user_picture'],
                    userData['user_mail'], userData['user_password']])
            conn.commit()
            del userData['user_password']
            return jsonify({
                'success': True,
                'message': 'User created',
                'inserted ': userData
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Registration not possible',
                'data': v.errors
            }), 404
    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'Unable to register. Please try later !'
        }), 500
