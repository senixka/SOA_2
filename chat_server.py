import time
import grpc
import pika
import sys
import os
import grpc_tools_pb2
import grpc_tools_pb2_grpc


def SendToClient(connection, client_queue, btext):
    channel = None
    try:
        channel = connection.channel()
        channel.queue_declare(queue=client_queue)
    except:
        print(f'Cannot make RabbitMQ channel to client queue "{client_queue}"')
        try:
            channel.close()
        except:
            pass
        return

    try:
        channel.basic_publish(exchange='', routing_key=client_queue, body=btext)
    except:
        try:
            channel.close()
        except:
            pass
    print(f"[chat log] Sent '{btext}' with routing_key {client_queue}")


def main():
    stub = None
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

    connection, channel = None, None
    while channel is None:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='0.0.0.0'))
            channel = connection.channel()
            channel.queue_declare(queue='to_server')
        except:
            try:
                channel.close()
            except:
                pass
            try:
                connection.close()
            except:
                pass
            channel, connection = None, None
            time.sleep(1)

    print('Connected to RabbitMQ server')

    try:
        def callback(ch, method, properties, body):
            print(f"[x] Received {body} with headers {properties.headers}")
            pid = int(properties.headers['pid'])

            try:
                response = stub.GetLightSessionInfo(grpc_tools_pb2.PlayerId(player_id=pid))
            except:
                print('Cannot get session info from game server')
                return

            if not response.is_pid_valid:
                print(f'No routing: {pid} not registered on game server.')
                return

            if response.session_id == -1:
                print(f'Pid {pid} to non-session players routing')
                try:
                    players = list(stub.GetNonSessionPids(grpc_tools_pb2.Empty()).pids)
                except:
                    print('Cannot get non-session players list from game server')
                    return

                try:
                    players.remove(pid)
                except:
                    print('Pid not in players')

                print(f'Route {body} from pid {pid} to pids {players}')
                for value in players:
                    SendToClient(connection, 'to_client_' + str(value), body)
            else:
                print(f'Pid {pid} to session routing')
                if response.player_role == 'ghost':
                    print(f'No routing: {pid} is ghost.')
                    return

                to_pids = list(response.mafia_pids)
                if response.is_day:
                    to_pids += list(response.other_pids)
                elif response.player_role != 'mafia':
                    print(f'No routing: {pid} not a mafia, but its a night time.')
                    return

                try:
                    to_pids.remove(pid)
                except:
                    print('Pid not in to_pids')

                print(f'Route {body} from pid {pid} to pids {to_pids}')
                for value in to_pids:
                    SendToClient(connection, 'to_client_' + str(value), body)

        channel.basic_consume(queue='to_server', on_message_callback=callback, auto_ack=True)
        channel.start_consuming()
    except:
        try:
            channel.close()
        except:
            pass
        try:
            connection.close()
        except:
            pass

        raise KeyboardInterrupt


if __name__ == '__main__':
    try:
        main()
    except:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
