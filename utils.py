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
    except pymysql.Error as e:
        print(e)
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
                'message': 'Token is missing!'
            }), 401
        try:
            data = jwt.decode(
                token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_tag FROM users WHERE user_tag = %s", data['user_tag'])
            current_user = cursor.fetchone()
            if not current_user:
                return jsonify({
                    'success': False,
                    'message': 'Unauthorized Access!'
                }), 401
        except:
            return jsonify({
                'success': False,
                'message': 'Token is invalid!'
            }), 401

        return f(current_user, *args, **kwargs)
    return decorator
