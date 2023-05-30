import os
import sys
import jwt
import grpc
import glob
import time
import datetime
import grpc_tools_pb2
import grpc_tools_pb2_grpc
from functools import wraps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from flask_restful import Api, Resource
from flask import Flask, jsonify, request, send_file, make_response

app = Flask(__name__)
api = Api(app)

# Used in JWT
app.config['SECRET_KEY'] = 'super-secret-key'

# Player struct:
# {
#     'pid': 1,
#     'name': 'Ivan',
#     'avatar': 'avatar_1.jpg',
#     'gender': 'male',
#     'email': 'ivan@mail.com',
#     'pwd': 'strong_pwd'
# }
players = {}  # pid -> player
pid_counter = 0

# Used to generate PDF
pdf_stats = {}  # pid -> file

# gRPC to game server
stub = None


def token_required(f):
    @wraps(f)
    def decorated(self, *args, **kwargs):
        token = None

        try:
            if 'Authorization' in request.headers:
                token = request.headers['Authorization'].split(' ')[1]
        except:
            return make_response(jsonify({'error': 'Bad Authorization Header'}), 400)

        if not token:
            return make_response(jsonify({'error': 'Token is missing'}), 401)

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_player = players.get(data['pid'], None)
        except:
            return make_response(jsonify({'error': 'Token is invalid'}), 401)

        if not current_player:
            return make_response(jsonify({'error': 'You must first register this pid via /register'}), 404)

        return f(self, current_player, *args, **kwargs)

    return decorated


class RegistrationResource(Resource):
    # curl -X POST -H "Content-Type: application/json" -d '{"pid": 23, "pwd": "1234"}' http://localhost:5000/register
    def post(self):
        data = request.get_json()

        if (not data) or ('pid' not in data) or ('pwd' not in data):
            return make_response(jsonify({'error': 'Missing pid or password'}), 400)

        try:
            pid = int(data['pid'])
        except:
            return make_response(jsonify({'error': 'Bad pid value'}), 400)

        if pid in players.keys():
            return make_response(jsonify({'error': 'Player already registered'}), 409)

        try:
            response = stub.GetPlayerStats(grpc_tools_pb2.PlayerId(player_id=pid))
        except:
            return make_response(jsonify({'error': 'Can not connect to game server via gRPC'}), 409)

        if not response.is_pid_valid:
            return make_response(jsonify({'error': 'This pid not valid on game server'}), 409)

        new_player = {
            'pid': pid,
            'name': '',
            'avatar': '',
            'gender': '',
            'email': '',
            'pwd': data['pwd']
        }

        players[new_player['pid']] = new_player
        print(f'\nRegistration of new player:\n{new_player}\n')

        return make_response(jsonify({'message': 'Registration successful'}), 201)


class LoginResource(Resource):
    # curl -X POST -H "Content-Type: application/json" -d '{"pid":23, "pwd": "1234"}' http://localhost:5000/login
    def post(self):
        data = request.get_json()

        if (not data) or ('pid' not in data) or ('pwd' not in data):
            return make_response(jsonify({'error': 'Missing pid or password'}), 400)

        try:
            pid = int(data['pid'])
        except:
            return make_response(jsonify({'error': 'Bad pid value'}), 400)

        if pid not in players.keys():
            return make_response(jsonify({'error': 'You must first register this pid via /register'}), 404)

        if players[pid]['pwd'] != data['pwd']:
            return make_response(jsonify({'error': 'Invalid password'}), 401)

        try:
            token = jwt.encode({'pid': pid, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                               app.config['SECRET_KEY'], algorithm="HS256")
        except:
            return make_response(jsonify({'error': 'Can not create jwt token'}), 409)

        return jsonify({'jwt_token': token})


class PlayerResource(Resource):
    # curl -X GET -H "Content-Type: application/json" -d '{"pids":[0, 1, 23]}' http://localhost:5000/player
    def get(self):
        data = request.get_json()

        if (not data) or ('pids' not in data):
            return make_response(jsonify({'error': 'Missing pids'}), 400)

        try:
            data['pids'] = list(map(int, data['pids']))
        except:
            return make_response(jsonify({'error': 'Invalid pid in pids'}), 401)

        response = []
        for target_pid in data['pids']:
            try:
                current_player = players.get(target_pid).copy()
                current_player.pop('pwd')
                response.append(current_player)
            except:
                response.append({'error': f'Invalid pid {target_pid}'})

        return jsonify(response)

    # curl -X PUT -H "Authorization: Bearer <JWT_TOKEN>" -F avatar=@avatar_file.jpg http://localhost:5000/player
    # curl -X PUT -H "Authorization: Bearer <JWT_TOKEN>" -H "Content-Type: application/json" -d '{"name":"Ivan", "email":"ivan@mail.com", "gender":"male"}' http://localhost:5000/player
    @token_required
    def put(self, current_player):
        try:
            file_name = f'avatar_{current_player["pid"]}.jpg'
            f = request.files['avatar']
            f.save(file_name)

            current_player['avatar'] = file_name
        except:
            pass

        try:
            data = request.get_json()

            current_player['name'] = data.get('name', current_player['name'])
            current_player['gender'] = data.get('gender', current_player['gender'])
            current_player['email'] = data.get('email', current_player['email'])
        except:
            pass

        return jsonify(players[current_player['pid']])

    # curl -X DELETE -H "Authorization: Bearer <JWT_TOKEN>" -H "Content-Type: application/json" -d '{"values":["name", "email", "gender", "avatar"]}' http://localhost:5000/player
    @token_required
    def delete(self, current_player):
        data = request.get_json()

        if (not data) or ('values' not in data):
            return make_response(jsonify({'error': 'Missing values'}), 400)

        if not all(value in ['name', 'email', 'gender', 'avatar'] for value in data['values']):
            return make_response(jsonify({'error': 'Invalid value in values'}), 401)

        for value in data['values']:
            current_player[value] = ''

        return jsonify(players[current_player['pid']])


class StatisticsResource(Resource):
    # curl -X GET http://localhost:5000/stats/<int:pid>
    def get(self, pid):
        if pid not in players.keys():
            return make_response(jsonify({'error': 'You must first register this pid via /register'}), 404)

        pdf_stats[pid] = f'statistics_{pid}.pdf'
        return jsonify({'url': f'/pdf/{pid}'})


class PDFResource(Resource):
    # curl -X GET http://localhost:5000/pdf/<int:pid> >temp.pdf
    def get(self, pid):
        if pid not in pdf_stats.keys():
            return make_response(jsonify({'error': 'You must first request this link via /stats/<int:pid>'}), 404)

        if pid not in players.keys():
            return make_response(jsonify({'error': 'You must first register this pid via /register'}), 404)

        try:
            response = stub.GetPlayerStats(grpc_tools_pb2.PlayerId(player_id=pid))
        except:
            return make_response(jsonify({'error': 'Can not connect to game server via gRPC'}), 404)

        if not response.is_pid_valid:
            return make_response(jsonify({'error': 'This pid not valid on game server'}), 404)

        pdf_filename = pdf_stats[pid]
        generate_statistics_pdf(players[pid], response, pdf_filename)

        return send_file(pdf_filename, download_name=pdf_filename)


def generate_statistics_pdf(player, game_stats, filename):
    pdf = canvas.Canvas(filename, pagesize=letter)

    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(50, 750, f"Player Statistics")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 720, f"Pid: {player['pid']}")
    pdf.drawString(50, 700, f"Name: {player['name']}")
    pdf.drawString(50, 680, f"Email: {player['email']}")
    pdf.drawString(50, 660, f"Gender: {player['gender']}")
    pdf.drawString(50, 640, f"Session count: {game_stats.session_count}")
    pdf.drawString(50, 620, f"Win count: {game_stats.win_count}")
    pdf.drawString(50, 600, f"Lose count: {game_stats.lose_count}")
    pdf.drawString(50, 580, f"Time in game: {game_stats.time_in_game} (in seconds)")

    avatar_file = 'default.jpg'
    if os.path.isfile(player['avatar']):
        avatar_file = player['avatar']

    try:
        pdf.drawImage(avatar_file, 430, 600, 150, 150)
    except:
        pass

    pdf.save()


api.add_resource(RegistrationResource, '/register')
api.add_resource(LoginResource, '/login')
api.add_resource(PlayerResource, '/player')
api.add_resource(StatisticsResource, '/stats/<int:pid>')
api.add_resource(PDFResource, '/pdf/<int:pid>')


if __name__ == '__main__':
    try:
        for file_path in glob.glob('./avatar_*.jpg'):
            try:
                os.remove(file_path)
            except:
                pass

        for file_path in glob.glob('./statistics_*.pdf'):
            try:
                os.remove(file_path)
            except:
                pass

        while stub is None:
            try:
                grpc_channel = grpc.insecure_channel(str(os.environ.get('SERVER_ADDR', '0.0.0.0:50051')))
                stub = grpc_tools_pb2_grpc.MafiaGameStub(grpc_channel)
                stub.GetAllPlayers(grpc_tools_pb2.Empty())
            except:
                stub = None
                print('Cannot connect to game server')
                time.sleep(1)
        print('Connected to gRPC stub')

        app.run()
    except:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
