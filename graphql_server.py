import os
import sys
import time
import grpc
import grpc_tools_pb2
import grpc_tools_pb2_grpc
from flask import Flask, request
from graphene import ObjectType, String, Int, List, Schema, Mutation, Field, Boolean

app = Flask(__name__)

# Connect to game server
stub = None

# Game comments
game_comments = {}  # sid -> list(str)


class SessionPlayer(ObjectType):
    pid = Int()
    name = String()
    role = String()


class Scoreboard(ObjectType):
    sid = Int()
    is_session_valid = Boolean()
    is_session_ended = Boolean()
    is_day = Boolean()
    players = List(SessionPlayer)


class Game(ObjectType):
    sid = Int()
    scoreboard = Scoreboard()
    comments = List(String)


class Query(ObjectType):
    current_games = List(Int)
    past_games = List(Int)
    scoreboard = Field(Scoreboard, sid=Int())

    def resolve_current_games(self, info):
        try:
            return stub.GetCurrentSessions(grpc_tools_pb2.Empty()).sids
        except:
            return []

    def resolve_past_games(self, info):
        try:
            return stub.GetPastSessions(grpc_tools_pb2.Empty()).sids
        except:
            return []

    def resolve_scoreboard(self, info, sid):
        try:
            response = stub.GetScoreboard(grpc_tools_pb2.SessionId(session_id=sid))
        except:
            return {'sid': sid, 'is_session_valid': False, 'is_session_ended': False, 'is_day': True, 'players': []}

        if not response.is_session_valid:
            return {'sid': sid, 'is_session_valid': False, 'is_session_ended': False, 'is_day': True, 'players': []}

        return {'sid': sid, 'is_session_valid': True,
                'is_session_ended': response.is_session_ended, 'is_day': response.is_day,
                'players': [{'pid': p.player_id, 'name': p.player_name, 'role': p.player_role} for p in response.players]}


class AddComment(Mutation):
    class Arguments:
        sid = Int(required=True)
        comment = String(required=True)

    comments = List(String)

    def mutate(self, info, sid, comment):
        if sid in game_comments.keys():
            game_comments[sid].append(comment)
        else:
            game_comments[sid] = [comment]

        return AddComment(comments=game_comments[sid])


class CommentMutation(ObjectType):
    add_comment = AddComment.Field()


schema = Schema(query=Query, mutation=CommentMutation)


@app.route("/graphql", methods=["POST"])
def graphql():
    data = request.get_json()
    result = schema.execute(data["query"])
    print(result, data['query'])
    return {"data": result.data}


if __name__ == "__main__":
    try:
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

        app.run(port=int(os.environ.get('GRAPHQL_PORT', '50021')), host='0.0.0.0')
    except:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
