from flask import jsonify, current_app, request
from utils import db_connection, token_required
from flask import Blueprint
import requests


app = Blueprint('shows', __name__)


@app.route("/shows")
@token_required
def getShows(current_user):
    try:
        if not current_user['role'] == 'USER':
            return jsonify({
                'success': False,
                'message': 'Seul un utilisateur peut voir ses shows favoris'
            }), 401
        page = request.args.get('page', default=0, type=int)
        page = int(page) * int(current_app.config['NB_ELEM_BY_PAGE'])
        show_id = request.args.get('show_id', default='%', type=int)
        show_type = request.args.get('show_type', type=str)
        if show_type not in ['MOVIE', 'SERIE']:
            show_type = '%'
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM shows NATURAL JOIN liked WHERE user_tag = %s AND show_type LIKE %s AND show_id LIKE %s ORDER BY liked_datetime DESC LIMIT %s OFFSET %s",
            [current_user['user_tag'], show_type, show_id, int(current_app.config['NB_ELEM_BY_PAGE']), page])
        shows = cursor.fetchall()
        if len(shows) == 0:
            return jsonify({
                'success': False,
                'message': 'Aucun show trouvé'
            }), 404
        return jsonify({
            'success': True,
            'message': 'Shows trouvé(s)',
            'data': shows
        }), 200
    except Exception as err:
        print(err)
        return jsonify({
            'success': False,
            'message': 'Erreur interne'
        }), 500


@app.route("/shows/<string:id>")
def getShow(id):
    show_type = request.args.to_dict().get('show_type')
    types = ['MOVIE', 'SERIE']
    links = {
        'MOVIE': ['https://api.betaseries.com/movies/movie', 'https://api.betaseries.com/movies/characters'],
        'SERIE': ['https://api.betaseries.com/shows/display', 'https://api.betaseries.com/shows/characters']
    }
    if not show_type:
        return jsonify({
            'success': False,
            'message': 'Veuillez spécifier le paramètre show_type'
        }), 404
    if show_type.upper() not in types:
        return jsonify({
            'success': False,
            'message': 'Le paramètre show_type doit être égale à MOVIE ou SERIE'
        }), 404
    search = requests.get(links[show_type.upper()][0], params={
        'key': current_app.config['KEY'],
        'id': id
    })
    pre = ('Le film' if show_type.upper() == 'MOVIE' else 'La série')
    if search.status_code == 400:
        return jsonify({
            'success': False,
            'message': f'{pre} avec l’ID {id} n’existe pas'
        }), 400
    characters = requests.get(links[show_type.upper()][1], params={
        'key': current_app.config['KEY'],
        'id': id
    })
    result = search.json()
    if characters.status_code == 400:
        return jsonify(result), 200
    images = []
    for character in characters.json()['characters']:
        image = requests.get('https://api.betaseries.com/pictures/characters', params={
            'key': current_app.config['KEY'],
            'id': character['id'],
            'type': show_type.lower(),
            'width': 248,
            'height': 248
        }).url
        images.append({
            'name': character['actor'],
            'role': character['name'],
            'picture': image
        })
    result['actors'] = images
    return jsonify(result), 200


@app.route("/shows/<string:id>", methods=['POST'])
@token_required
def like(current_user, id):
    try:
        if not current_user['role'] == 'USER':
            return jsonify({
                'success': False,
                'message': 'Seul un utilisateur peut aimer un show'
            }), 401
        show_type = request.args.to_dict().get('show_type')
        types = ['MOVIE', 'SERIE']
        user_tag = current_user['user_tag']
        links = {
            'MOVIE': 'https://api.betaseries.com/movies/movie',
            'SERIE': 'https://api.betaseries.com/shows/display'
        }
        if not show_type:
            return jsonify({
                'success': False,
                'message': 'Veuillez spécifier le paramètre show_type'
            }), 404
        if show_type.upper() not in types:
            return jsonify({
                'success': False,
                'message': 'Le paramètre show_type doit être égale à MOVIE ou SERIE'
            }), 404
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM shows WHERE show_id = %s AND show_type = %s", [id, show_type])
        show = cursor.fetchone()
        pre = ('Le film' if show_type.upper() == 'MOVIE' else 'La série')
        if not show:
            search = requests.get(links[show_type.upper()], params={
                'key': current_app.config['KEY'],
                'id': id
            })
            if search.status_code != 200:
                return jsonify({
                    'success': False,
                    'message': f'{pre} avec l’ID {id} n’existe pas'
                }), 404
            title = search.json()['movie' if show_type.upper()
                                  == 'MOVIE' else 'show']['title']
            cursor.execute("INSERT INTO shows VALUES (DEFAULT, %s, %s, %s)", [
                           id, show_type.upper(), title])
            conn.commit()
            cursor.execute(
                "SELECT * FROM shows WHERE show_id = %s AND show_type = %s", [id, show_type])
            show = cursor.fetchone()
        show_tag = show['show_tag']
        cursor.execute("SELECT is_liked(%s, %s) AS RESULTAT",
                       [user_tag, show_tag])
        liked = cursor.fetchone()["RESULTAT"]
        if liked != 0:
            return jsonify({
                'success': False,
                'message': f'Vous aimez déjà {pre.lower()} avec l’ID {id}'
            }), 404
        cursor.execute("INSERT INTO liked VALUES (%s, %s, NOW())",
                       [user_tag, show_tag])
        conn.commit()
        return jsonify({
            'success': True,
            'message': f'{user_tag} vient d’aimer {pre.lower()} avec l’ID {id}'
        }), 201
    except Exception as err:
        print(err)
        return jsonify({
            'success': False,
            'message': 'Erreur interne'
        }), 500


@app.route('/shows/<string:id>', methods=['DELETE'])
@token_required
def dislike(current_user, id):
    try:
        if not current_user['role'] == 'USER':
            return jsonify({
                'success': False,
                'message': 'Seul un utilisateur peut supprimer un show'
            }), 401
        show_type = request.args.to_dict().get('show_type')
        types = ['MOVIE', 'SERIE']
        user_tag = current_user['user_tag']
        if not show_type:
            return jsonify({
                'success': False,
                'message': 'Veuillez spécifier le paramètre show_type'
            }), 404
        if show_type.upper() not in types:
            return jsonify({
                'success': False,
                'message': 'Le paramètre show_type doit être égale à MOVIE ou SERIE'
            }), 404
        pre = ('Le film' if show_type.upper() == 'MOVIE' else 'La série')
        conn = db_connection()
        cursor = conn.cursor()
        result = cursor.execute(
            "DELETE FROM liked WHERE user_tag = %s AND show_tag IN (SELECT show_tag FROM shows WHERE show_type = %s AND show_id = %s)",
            [user_tag, show_type, id])
        conn.commit()
        if result == 0:
            return jsonify({
                'success': False,
                'message': f'L’utilisateur {user_tag} n’aime pas {pre.lower()} avec l’ID {id}'
            }), 404
        return jsonify({
            'success': True,
            'message': f'L’utilisateur {user_tag} a bien retiré de ses favoris {pre.lower()} avec l’ID {id}'
        }), 204
    except Exception as err:
        print(err)
        return jsonify({
            'success': False,
            'message': 'Erreur interne'
        }), 500
