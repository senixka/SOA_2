import os
import sys
import time
import requests


def run_query(query):
    addr = str(os.environ.get('GRAPHQL_ADDR', '0.0.0.0:50021')).strip()
    response = requests.post(f'http://{addr}/graphql', json={"query": query})
    return response.json()


def query_current_games() -> str:
    return 'query { currentGames }'


def query_past_games() -> str:
    return 'query { pastGames }'


def query_scoreboard(sid: int) -> str:
    return f'query {{ scoreboard(sid: {sid}) {{sid, isSessionValid, isSessionEnded, isDay, players {{pid, name, role}} }} }}'


def mutation_add_comment(sid: int, comment: str) -> str:
    return f'mutation {{ addComment(sid: {sid}, comment: "{comment}") {{comments}} }}'


def print_scoreboard(sid: int) -> None:
    try:
        info = run_query(query_scoreboard(sid))['data']['scoreboard']
    except:
        print('Cannot get scoreboard')
        return

    if not info['isSessionValid']:
        print('Sid value is invalid')
        return

    print('################## Scoreboard ###################')
    print(f'# Session Id:  {sid :<32d} #')
    print(f'# Is day time: {str(info["isDay"]):32s} #')
    print(f'# Is game end: {str(info["isSessionEnded"]):32s} #')
    print('# --------------------------------------------- #')
    print('# == Player Id == Player Name == Player Role == #')
    for player in info['players']:
        print(f'# == {player["pid"] : <9d} == {player["name"]:11s} == {player["role"]:<11s} == #')
    print('#################################################')
    print()

def print_scoreboard_stream(sid: int) -> None:
    info = {}
    while True:
        try:
            new_info = run_query(query_scoreboard(sid))['data']['scoreboard']
        except:
            print('Cannot get scoreboard')
            return

        if info != new_info:
            info = new_info
            try:
                os.system('cls' if os.name in ('nt', 'dos') else 'clear')
            except:
                pass
            print_scoreboard(sid)

            if info['isSessionEnded']:
                break

        time.sleep(1)


def main():
    while True:
        action = input('Action: ').strip()

        if action == 'c':
            try:
                print('Current games sid:', run_query(query_current_games())['data']['currentGames'])
            except:
                print('Can not get current games sid')
        elif action == 'p':
            try:
                print('Past games sid:', run_query(query_past_games())['data']['pastGames'])
            except:
                print('Can not get past games sid')
        elif action == 's':
            try:
                sid = int(input('Enter sid: '))
                print_scoreboard(sid)
            except:
                print('Can not get scoreboard')
        elif action == 'ss':
            try:
                sid = int(input('Enter sid: '))
                print_scoreboard_stream(sid)
            except:
                print('Can not get scoreboard stream')
        elif action == 'a':
            try:
                sid = int(input('Enter sid: '))
                comment = input('Enter comment: ').strip()
                print(f'Comments on game with sid {sid}:', run_query(mutation_add_comment(sid, comment))['data']['addComment']['comments'])
            except:
                print('Can not add comment to game')
        elif action == 'exit':
            break


if __name__ == '__main__':
    try:
        main()
    except:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
