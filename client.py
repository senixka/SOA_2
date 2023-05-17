import time
import grpc
import os
import grpc_tools_pb2
import grpc_tools_pb2_grpc
from threading import Thread, Lock
import random


class Client:
    def __init__(self) -> None:
        self.player_name = ''
        self.player_id = -1
        self.updates = []
        self.stub = None
        self.lock = Lock()

        self.is_client_alive = True
        self.thread_hb = Thread(target=self.ThreadHB)
        self.thread_hb.start()

    def Exit(self):
        self.is_client_alive = False
        self.thread_hb.join()

    def TryConnect(self, name: str = '') -> None:
        with self.lock:
            addr = str(os.environ.get('SERVER_ADDR', '0.0.0.0:50051'))

            try:
                channel = grpc.insecure_channel(addr)
                self.stub = grpc_tools_pb2_grpc.MafiaGameStub(channel)
            except:
                self.stub = None
                return

            self.player_name = name
            while len(self.player_name) == 0:
                self.player_name = input('Enter your name (non empty string): ')
                self.player_name = self.player_name.strip()

            try:
                response = self.stub.OnClientConnect(grpc_tools_pb2.PlayerName(player_name=self.player_name))
                self.player_id = response.player_id
            except:
                print('Cannot connect to server addr:', addr)
                print('Cannot set client name or obtain id from server')
                self.stub = None
                self.player_id = -1
                self.player_name = ''
                return

            print(f'Player {name} successfully registered on server with id {self.player_id}')

    def ThreadHB(self) -> None:
        while self.is_client_alive:
            time.sleep(0.5)

            with self.lock:
                if (self.stub is None) or self.player_id == -1:
                    continue

                try:
                    response = self.stub.OnClientHeartbeat(grpc_tools_pb2.PlayerId(player_id=self.player_id))
                    self.updates += response.actions
                except:
                    continue

                for action in self.updates:
                    print('# Update from server:', action)
                self.updates.clear()

    def PrintHelp(self) -> None:
        with self.lock:
            print('################ Help ###################')
            print('# help - print this help.               #')
            print('# c - to Connect to server.             #')
            print('# v - to get Valid actions in session.  #')
            print('# a - to print All players.             #')
            print('# s - to print Session info.            #')
            print('# exit - exit client.                   #')
            print('#########################################')

    def PrintAllPlayers(self) -> None:
        with self.lock:
            try:
                players = self.stub.GetAllPlayers(grpc_tools_pb2.Empty()).all_players
            except:
                print('Cannot get all players')
                return

            print('################## All Players #################')
            print('# == Session Id == Player Id == Player Name == #')
            for player in players:
                print(f'# == {player.session_id : <10d} == {player.player_id : <9d} == {player.player_name:11s} == #')
            print('################################################')
            print()

    def PrintSessionInfo(self) -> None:
        with self.lock:
            try:
                info = self.stub.GetSessionInfo(grpc_tools_pb2.PlayerId(player_id=self.player_id))
                sid = info.session_id
                is_day = info.is_day
                players = info.players
            except:
                print('Cannot get session info')
                return

            print('################ Current Session ################')
            print(f'# Session Id:  {sid :<32d} #')
            if sid != -1:
                print(f'# Is day time: {str(is_day):32s} #')
                print('# --------------------------------------------- #')
                print('# == Player Id == Player Name == Player Role == #')
                for player in players:
                    print(
                        f'# == {player.player_id : <9d} == {player.player_name:11s} == {player.player_role:<11s} == #')
            print('#################################################')
            print()

    def PrintValidActions(self) -> None:
        with self.lock:
            try:
                response = self.stub.GetValidActions(grpc_tools_pb2.PlayerId(player_id=self.player_id))
            except:
                print('Cannot get valid actions')
                return

            print('Valid actions:', response.actions)

    def SendClientAction(self, action):
        with self.lock:
            try:
                response = self.stub.OnClientAction(
                    grpc_tools_pb2.ActionRequest(player_id=self.player_id, action=action))
                is_success = response.is_success
            except:
                print('Cannot process client action')
                return

            if not is_success:
                print('Invalid action:', action)

    def BotMode(self) -> None:
        basic = ['v', 'a', 's']
        while True:
            time.sleep(0.5)

            if random.randint(0, 2) == 1:
                random.shuffle(basic)
                action = basic[0]
                print(f'Bot action: {basic[0]}')

                if action == 'v':
                    self.PrintValidActions()
                if action == 'a':
                    self.PrintAllPlayers()
                elif action == 's':
                    self.PrintSessionInfo()
            else:
                with self.lock:
                    try:
                        valid = self.stub.GetValidActions(grpc_tools_pb2.PlayerId(player_id=self.player_id)).actions
                    except:
                        valid = []

                random.shuffle(valid)
                if len(valid) != 0:
                    print(f'Bot action: {valid[0]}')
                    self.SendClientAction(valid[0])


def main():
    bot_mode = input('Bot mode? (yes/no): ').strip()

    client = Client()
    client.TryConnect()

    if bot_mode == 'yes':
        client.BotMode()
        exit(0)

    while True:
        action = input()

        if action == 'help':
            client.PrintHelp()
        elif action == 'c':
            client.TryConnect()
        elif action == 'v':
            client.PrintValidActions()
        elif action == 'a':
            client.PrintAllPlayers()
        elif action == 's':
            client.PrintSessionInfo()
        elif action == 'exit':
            client.Exit()
            exit(0)
        else:
            client.SendClientAction(action)


if __name__ == "__main__":
    main()
