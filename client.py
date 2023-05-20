import sys
import time
import grpc
import os
import grpc_tools_pb2
import grpc_tools_pb2_grpc
from threading import Thread, Lock
import random
import pika


class Client:
    def __init__(self) -> None:
        self.player_name = ''
        self.player_id = -1
        self.updates = []
        self.stub = None
        self.lock = Lock()

        self.rmq_connection = None
        self.rmq_server_queue = 'to_server'
        self.rmq_client_channel = None
        self.rmq_client_queue = None

        self.is_client_alive = True
        self.thread_hb = Thread(target=self.ThreadHB)
        self.thread_hb.start()

        self.thread_mc = Thread(target=self.ThreadMC)
        self.thread_mc.start()

    def Exit(self):
        with self.lock:
            self.is_client_alive = False
            try:
                self.rmq_client_channel.stop_consuming()
            except:
                pass

        self.thread_hb.join()
        self.thread_mc.join()

    def TryConnect(self, name: str = '') -> None:
        with self.lock:
            addr = str(os.environ.get('SERVER_ADDR', '0.0.0.0:50051'))

            try:
                channel = grpc.insecure_channel(addr)
                self.stub = grpc_tools_pb2_grpc.MafiaGameStub(channel)
                self.stub.GetAllPlayers(grpc_tools_pb2.Empty())
            except:
                print('Cannot connect to game server')
                self.stub = None
                return

            self.player_name = name
            while len(self.player_name) == 0:
                self.player_name = input('Enter your name (non empty string): ')
                self.player_name = self.player_name.strip()
            try:
                response = self.stub.OnClientConnect(grpc_tools_pb2.PlayerName(player_name=self.player_name))
                self.player_id = response.player_id
                self.rmq_client_queue = 'to_client_' + str(self.player_id)
            except:
                print('Cannot connect to server addr:', addr)
                print('Cannot set client name or obtain id from server')
                self.stub = None
                self.player_id = -1
                self.player_name = ''
                self.rmq_client_queue = None
                return

            addr = str(os.environ.get('RMQ_ADDR', '0.0.0.0'))

            try:
                if self.rmq_connection is None:
                    self.rmq_connection = pika.BlockingConnection(pika.ConnectionParameters(host=addr))
                    channel = self.rmq_connection.channel()
                    channel.queue_declare(queue=self.rmq_server_queue)
                    channel.close()
                else:
                    try:
                        self.rmq_client_channel.stop_consuming()
                    except:
                        pass
            except:
                print(f'Cannot connect to RabbitMQ server on addr {addr}')
                self.rmq_connection = None

        print('Connected to RabbitMQ server')
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
                    print('[game]', action)
                self.updates.clear()

    def ThreadMC(self) -> None:
        while self.is_client_alive:
            time.sleep(0.5)

            with self.lock:
                if self.rmq_connection is None:
                    continue

                try:
                    addr = str(os.environ.get('RMQ_ADDR', '0.0.0.0'))
                    connection = pika.BlockingConnection(pika.ConnectionParameters(host=addr))
                    self.rmq_client_channel = connection.channel()
                    self.rmq_client_channel.queue_declare(queue=self.rmq_client_queue)

                    def client_callback(ch, method, properties, body):
                        try:
                            text = body.decode(encoding='UTF-8', errors='replace')
                            print(f'[chat] {text}')
                        except:
                            print(f'[error chat] Cannot decode "{body}"')

                    self.rmq_client_channel.basic_consume(
                        queue=self.rmq_client_queue,
                        on_message_callback=client_callback,
                        auto_ack=True
                    )
                except:
                    try:
                        connection.close()
                    except:
                        pass

                    self.rmq_client_channel = None
                    continue

            try:
                self.rmq_client_channel.start_consuming()
            except:
                try:
                    connection.close()
                except:
                    pass
                self.rmq_client_channel = None

    def Chat(self, text: str):
        with self.lock:
            if self.rmq_connection is None:
                print('No connection to RabbitMQ')
                return

            try:
                btext = text.encode(encoding='UTF-8', errors='replace')
            except:
                print('Cannot encode string "{text}" to utf-8.')
                print('Perhaps you are using Windows (bad idea),'
                      'or you have the terminal encodings set incorrectly.')
                return

            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(host='0.0.0.0'))
                channel = connection.channel()
                channel.basic_publish(
                    exchange='',
                    properties=pika.BasicProperties(headers={'pid': str(self.player_id)}),
                    routing_key=self.rmq_server_queue,
                    body=btext
                )
                channel.close()
                connection.close()
            except:
                print(f'Cannot make channel to RabbitMQ server or publish message')
                try:
                    connection.close()
                except:
                    pass

    def PrintHelp(self) -> None:
        with self.lock:
            print('################ Help ###################')
            print('# help - print this help.               #')
            print('# c - to Connect to server.             #')
            print('# v - to get Valid actions in session.  #')
            print('# a - to print All players.             #')
            print('# s - to print Session info.            #')
            print('# t <TEXT> - to send <TEXT> to chat.    #')
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
        basic = ['v', 'a', 's', 't']
        while True:
            time.sleep(0.8)

            if random.randint(0, 2) == 1:
                random.shuffle(basic)
                action = basic[0]
                print(f'Bot action: {basic[0]}')

                if action == 'v':
                    self.PrintValidActions()
                elif action == 'a':
                    self.PrintAllPlayers()
                elif action == 's':
                    self.PrintSessionInfo()
                elif action == 't':
                    self.Chat('Bot message')
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
        action = input().strip()

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
        elif action.startswith('t '):
            client.Chat(action.removeprefix('t '))
        elif action == 'exit':
            client.Exit()
            raise KeyboardInterrupt
        else:
            client.SendClientAction(action)


if __name__ == "__main__":
    try:
        main()
    except:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
