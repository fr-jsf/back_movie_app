import pymysql
from flask import request, jsonify, current_app
import jwt
from functools import wraps


def db_connection():
    conn = None
    try:
        conn = pymysql.connect(
            host=current_app.config['HOST_DB'],
            database=current_app.config['NAME_DB'],
            user=current_app.config['USER_DB'],
            port=int(current_app.config['PORT_DB']),
            password=current_app.config['PASS_DB'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except pymysql.Error as err:
        print(err)
    return conn


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']
        if not token:
            return jsonify({
                'success': False,
                'message': 'Token manquant'
            }), 401
        try:  # TODO: Faire une condition pour gérér l'expiration des tokens
            data = jwt.decode(
                token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            if current_app.config['ADMIN_USER'] == data['user_tag'] and data['role'] == 'ADMIN':
                pass
            else:
                conn = db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT user_tag FROM users WHERE user_tag = %s", data['user_tag'])
                user = cursor.fetchone()
                if not user:
                    return jsonify({
                        'success': False,
                        'message': 'Accès interdit'
                    }), 401
            current_user = data
        except:
            return jsonify({
                'success': False,
                'message': 'Token invalide'
            }), 401

        return f(current_user, *args, **kwargs)
    return decorator
