import os
from flask import Flask, render_template, redirect, request
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
from routes.shows import app as shows
from routes.auth import app as auth
from routes.users import app as users

load_dotenv(dotenv_path='.env')

app = Flask(__name__)

SWAGGER_URL = '/docs'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "MovieApp"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

app.url_map.strict_slashes = False
app.config['PORT'] = os.getenv('APP_PORT')
app.config['DOMAIN'] = os.getenv('APP_DOMAIN')
app.config['KEY'] = os.getenv('APP_KEY')
app.config['HOST_DB'] = os.getenv('HOST_DB')
app.config['PORT_DB'] = os.getenv('PORT_DB')
app.config['USER_DB'] = os.getenv('USER_DB')
app.config['NAME_DB'] = os.getenv('NAME_DB')
app.config['PASS_DB'] = os.getenv('PASS_DB')
app.config['NB_ELEM_BY_PAGE'] = os.getenv('NB_ELEM_BY_PAGE')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['ADMIN_USER'] = os.getenv('ADMIN_USER')
app.config['ADMIN_PASS'] = os.getenv('ADMIN_PASS')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.register_blueprint(shows)
app.register_blueprint(auth)
app.register_blueprint(users)


@app.route('/')
def index():
    return redirect(request.url_root + '/docs')


if __name__ == "__main__":
    app.run(debug=True, port=int(app.config['PORT']))
