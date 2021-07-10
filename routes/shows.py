from flask import Blueprint

app = Blueprint('shows', __name__)


@app.route("/shows")
def getShow():
    return 'shows'
