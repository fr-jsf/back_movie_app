from flask import Blueprint, jsonify, request, current_app
from utils import db_connection
import datetime
import jwt
from werkzeug.security import check_password_hash

app = Blueprint('auth', __name__)


@app.route('/auth', methods=['POST'])
def login():
    try:
        auth = request.form
        if not auth or not auth.get('mail') or not auth.get('password'):
            return jsonify({'success': False, 'message': 'Invalid Data'}), 422
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_mail = %s",
                       auth.get('mail'))
        user = cursor.fetchone()
        # Ici, rajouter une condition pour créer un utilisateur ADMIN
        if not user:
            return jsonify({'success': False, 'message': 'Unauthorized Access!'}), 401
        if check_password_hash(user['user_password'], auth.get('password')):
            token = jwt.encode({
                'user_tag': user['user_tag'],
                'role': 'user',
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({'success': True, 'message': 'Token generated!', 'token': token})
        return jsonify({'success': False, 'message': 'Invalid Mail or Password!'}), 403
    except Exception as e:
        print("Error : ", e)
        return jsonify({'success': False, 'message': 'Internal Error!'}), 422
