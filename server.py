import sys
from datetime import datetime
import time
import os
import random
from threading import Lock, Thread
import grpc
import grpc_tools_pb2
import grpc_tools_pb2_grpc
from concurrent import futures


class MafiaGameServicer(grpc_tools_pb2_grpc.MafiaGameServicer):
    def __init__(self) -> None:
        print('In server constructor')
        self.last_hb_time = {}  # pid -> datetime
        self.notify = {}  # pid -> message queue
        self.id_counter = 0  # to create unique id
        self.all_players = {}  # pid -> pb_Player
        self.session_info = {}  # sid -> info
        self.lock = Lock()  # lock game logic

        self.is_server_alive = True
        self.thread_watcher = Thread(target=self.ThreadWatcher)
        self.thread_watcher.start()

    def __del__(self) -> None:
        print('In server destructor')

        self.is_server_alive = False
        self.thread_watcher.join()

    def GetUniqueId(self) -> int:
        self.id_counter += 1
        return self.id_counter

    ############################### Notify ###############################

    def NotifyPlayer(self, pid: int, value: str) -> None:
        self.notify[pid].append(value)

    def NotifyPlayers(self, pid_list: list, value: str) -> None:
        for pid in pid_list:
            self.notify[pid].append(value)

    def NotifySession(self, sid: int, value: str) -> None:
        for pid in list(self.session_info[sid]['role'].keys()):
            self.notify[pid].append(value)

    def NotifyAllExcept(self, skip_pid: list, value: str) -> None:
        for pid in list(self.all_players.keys()):
            if pid not in skip_pid:
                self.notify[pid].append(value)

    # def NotifyAll(self, value: str) -> None:
    #     for pid in self.all_players.keys():
    #         self.notify[pid].append(value)

    ########################## Session Helpers ############################

    # Session state example
    # self.session_info[sid] = {
    #         'is_day': True,
    #         'night_check': [],
    #         'votes': {},
    #         'role' : {mafia_id: 'mafia', cop_id: 'cop', civil_1: 'civil', civil_2: 'civil'},
    #         'actions': {mafia_id: ['end_day'], cop_id: ['end_day'], civil_1: ['end_day'], civil_2: ['end_day']}
    #     }

    def GetSessionPids(self, sid: int) -> list:
        return list(self.session_info[sid]['role'].keys())

    def GetPidsByRole(self, sid: int, role: str) -> list:
        return [pid for pid, value in self.session_info[sid]['role'].items() if value == role]

    def GetRoleByPid(self, sid: int, pid: int) -> str:
        return self.session_info[sid]['role'][pid]

    def GetPidActions(self, sid: int, pid: int) -> list:
        return self.session_info[sid]['actions'][pid]

    def SetPidActions(self, sid: int, pid: int, new_actions: list):
        self.session_info[sid]['actions'][pid] = new_actions.copy()

    # def AddPidActions(self, sid: int, pid: int, add_actions: list):
    #     self.session_info[sid]['actions'][pid].append(add_actions.copy())

    def RemovePidActionsByPattern(self, sid: int, pid: int, start_with: str):
        self.session_info[sid]['actions'][pid] = list(
            filter(lambda x: not x.startswith(start_with), self.GetPidActions(sid, pid)))

    def GetPidsToKill(self, sid: int) -> list:
        skip_pids = self.GetPidsByRole(sid, 'mafia') + self.GetPidsByRole(sid, 'ghost')
        return [pid for pid in self.GetSessionPids(sid) if (pid not in skip_pids)]

    def GetPidsToCheck(self, sid: int) -> list:
        skip_pids = self.GetPidsByRole(sid, 'cop') + self.GetPidsByRole(sid, 'ghost')
        return [pid for pid in self.GetSessionPids(sid) if (pid not in skip_pids)]

    def GetPidsToVote(self, sid: int) -> list:
        skip_pids = self.GetPidsByRole(sid, 'ghost')
        return [pid for pid in self.GetSessionPids(sid) if (pid not in skip_pids)]

    def GetVotes(self, sid: int) -> dict:
        return self.session_info[sid]['votes'].copy()

    def ClearVotes(self, sid: int) -> None:
        self.session_info[sid]['votes'] = {}

    def AddVote(self, sid: int, pid: int) -> None:
        if pid in self.session_info[sid]['votes'].keys():
            self.session_info[sid]['votes'][pid] += 1
        else:
            self.session_info[sid]['votes'][pid] = 0

    def GetVoteLeaders(self, sid: int) -> list:
        if len(self.session_info[sid]['votes']) == 0:
            return []
        max_vote = max(self.session_info[sid]['votes'].values())
        return [pid for pid, vote in self.session_info[sid]['votes'].items() if vote == max_vote]

    def KillPlayer(self, sid: int, pid: int) -> None:
        self.session_info[sid]['role'][pid] = 'ghost'

    def GetNightCheckPids(self, sid: int) -> list:
        return self.session_info[sid]['night_check'].copy()

    def AddPidToNightCheck(self, sid: int, pid: int) -> None:
        if pid not in self.session_info[sid]['night_check']:
            self.session_info[sid]['night_check'].append(pid)

    def ClearNightCheckPids(self, sid: int) -> None:
        self.session_info[sid]['night_check'].clear()

    def IsAllActionsEmpty(self, sid: int) -> bool:
        for actions in self.session_info[sid]['actions'].values():
            if len(actions) != 0:
                return False
        return True

    def IsDayTime(self, sid: int) -> bool:
        return self.session_info[sid]['is_day']

    def SetDayTime(self, sid: int, is_day: bool) -> None:
        self.session_info[sid]['is_day'] = is_day

    def GetPlayerName(self, pid: int) -> str:
        return self.all_players[pid].player_name

    ########################## Session Core ###############################

    def TryChangeDayTime(self, sid: int, is_day: bool) -> bool:
        if is_day == self.IsDayTime(sid) or self.IsAllActionsEmpty(sid):
            self.SetDayTime(sid, is_day)
            return True
        return False

    def TryMoveToNightState(self, sid: int) -> bool:
        if not self.TryChangeDayTime(sid, False):
            return False

        # Kill player with most votes, clear votes
        victims = self.GetVoteLeaders(sid)
        if len(victims) == 1:
            self.KillPlayer(sid, victims[0])
            self.NotifySession(sid, f'Player {victims[0]} ({self.GetPlayerName(victims[0])}) was killed by votes')
        self.ClearVotes(sid)

        # Clear night checks (must be already empty)
        self.ClearNightCheckPids(sid)

        if self.TryEndSession(sid):
            return True

        # Update Cop night actions
        for cop_pid in self.GetPidsByRole(sid, 'cop'):
            self.SetPidActions(sid, cop_pid, ['check ' + str(pid) for pid in self.GetPidsToCheck(sid)])

        # Update Mafia night actions
        for mafia_pid in self.GetPidsByRole(sid, 'mafia'):
            self.SetPidActions(sid, mafia_pid, ['kill ' + str(pid) for pid in self.GetPidsToKill(sid)])

            # Update Civil night actions
        for civil_pid in self.GetPidsByRole(sid, 'civil'):
            self.SetPidActions(sid, civil_pid, [])

        self.NotifySession(sid, 'Night time starts')
        return True

    def TryMoveToDayState(self, sid: int) -> bool:
        if not self.TryChangeDayTime(sid, True):
            return False

        # Kill players with any votes, clear votes
        for victim in self.GetVotes(sid).keys():
            self.KillPlayer(sid, victim)
            self.NotifySession(sid, f'Player {victim} ({self.GetPlayerName(victim)}) was killed by mafia')
        self.ClearVotes(sid)

        if self.TryEndSession(sid):
            return True

        # Prepare vote actions and publish actions, clear night checks
        vote_actions = ['vote ' + str(pid) for pid in self.GetPidsToVote(sid)]
        publish_actions = ['publish ' + str(pid) for pid in self.GetNightCheckPids(sid)]
        self.ClearNightCheckPids(sid)

        # Update Cop day actions
        for cop_pid in self.GetPidsByRole(sid, 'cop'):
            self.SetPidActions(sid, cop_pid, ['end_day'] + publish_actions.copy() + vote_actions.copy())

        # Update Mafia day actions
        for mafia_pid in self.GetPidsByRole(sid, 'mafia'):
            self.SetPidActions(sid, mafia_pid, ['end_day'] + vote_actions.copy())

        # Update Civil day actions
        for civil_pid in self.GetPidsByRole(sid, 'civil'):
            self.SetPidActions(sid, civil_pid, ['end_day'] + vote_actions.copy())

        self.NotifySession(sid, 'Day time starts')
        return True

    ########################## Session Process ###############################

    def StartSession(self, pids: list) -> None:
        if len(pids) != 4:
            print("Cannot start session")
            return

        random.shuffle(pids)
        mafia_id, cop_id, civil_1, civil_2 = pids

        sid = self.GetUniqueId()

        self.session_info[sid] = {
            'is_day': True,
            'night_check': [],
            'votes': {},
            'role': {mafia_id: 'mafia', cop_id: 'cop', civil_1: 'civil', civil_2: 'civil'},
            'actions': {mafia_id: ['end_day'], cop_id: ['end_day'], civil_1: ['end_day'], civil_2: ['end_day']}
        }

        for pid in pids:
            self.all_players[pid].session_id = sid

        self.NotifySession(sid, f'New session with id {sid} starts')
        for pid in pids:
            pid_role = self.session_info[sid]['role'][pid]
            self.NotifyPlayer(pid, f'Your role is {pid_role}')

        print(f'Started new session {sid} with pids: {pids}')

    def EndSession(self, sid: int) -> None:
        for pid in self.GetSessionPids(sid):
            self.all_players[pid].session_id = -1
            self.NotifyPlayer(pid, 'Current session ends')

        self.session_info.pop(sid)
        print(f'End session {sid}')

    def TryEndSession(self, sid: int) -> bool:
        if not self.IsAllActionsEmpty(sid):
            return False

        mafia_pids = self.GetPidsByRole(sid, 'mafia')
        other_pids = self.GetPidsByRole(sid, 'civil') + self.GetPidsByRole(sid, 'cop')
        if 0 < len(mafia_pids) < len(other_pids):
            return False

        if len(mafia_pids) > 0:
            self.NotifySession(sid, 'Mafia wins')
        else:
            self.NotifySession(sid, 'Civil wins')

        self.EndSession(sid)
        return True

    def RemovePlayerFromSession(self, pid: int) -> None:
        sid = self.all_players[pid].session_id
        if sid == -1:
            return

        self.NotifySession(sid, f'Player {pid} ({self.GetPlayerName(pid)}) left this session')

        if self.GetRoleByPid(sid, pid) != 'ghost':
            self.EndSession(sid)
        else:
            self.session_info[sid]['role'].pop(pid)
            self.session_info[sid]['actions'].pop(pid)

    def UpdateSessionWithAction(self, pid: int, action: str) -> bool:
        sid = self.all_players[pid].session_id
        if sid == -1:
            return False

        valid_actions = self.GetPidActions(sid, pid)
        if action not in valid_actions:
            return False

        act, target = action, -1
        if action != 'end_day':
            act, target = action.split(' ')
            target = int(target)

        if act == 'end_day':
            self.SetPidActions(sid, pid, [])
            self.NotifySession(sid, f'Player {pid} ({self.GetPlayerName(pid)}) finished his day')
        elif act == 'vote':
            self.AddVote(sid, target)
            self.NotifySession(sid, f'Player {pid} ({self.GetPlayerName(pid)}) votes for {target}')
        elif act == 'check':
            if target in self.GetPidsByRole(sid, 'mafia'):
                self.NotifyPlayer(pid, f'Check: {target} ({self.GetPlayerName(target)}) is mafia')
                self.AddPidToNightCheck(sid, target)
            else:
                self.NotifyPlayer(pid, f'Check: {target} ({self.GetPlayerName(target)}) is civil')
        elif act == 'publish':
            self.NotifySession(sid, f'Cop reveals {target} ({self.GetPlayerName(target)}) is mafia')
        elif act == 'kill':
            self.AddVote(sid, target)
            self.NotifyPlayers(self.GetPidsByRole(sid, 'mafia'), f'Player {target} ({self.GetPlayerName(target)}) killed by mafia')

        self.RemovePidActionsByPattern(sid, pid, act)

        if self.IsDayTime(sid):
            self.TryMoveToNightState(sid)
        else:
            self.TryMoveToDayState(sid)

        return True

    ################################## Server Helpers ##################################

    def RemovePlayerFromServer(self, pid: int) -> None:
        player = self.all_players[pid]
        print(f'Player with Id {pid} ({player.player_name}) suspected to be dead')

        self.RemovePlayerFromSession(pid)

        self.notify.pop(pid)
        self.all_players.pop(pid)
        self.last_hb_time.pop(pid)

        skip_pid = [pid for pid, info in self.all_players.items() if info.session_id != -1]
        self.NotifyAllExcept(skip_pid, f'Player with Id {pid} ({player.player_name}) left the server')

    def ThreadWatcher(self) -> None:
        print('ThreadWatcher started')

        while True:
            time.sleep(0.1)

            if not self.is_server_alive:
                break

            with self.lock:
                # Check clients HB
                current_time = datetime.now()
                for pid, hb_time in list(self.last_hb_time.items()):
                    if (current_time - hb_time).total_seconds() > 3:
                        self.RemovePlayerFromServer(pid)

                # Try to create new session
                pids = [pid for pid, info in self.all_players.items() if info.session_id == -1]
                random.shuffle(pids)
                if len(pids) >= 4:
                    self.StartSession(pids[:4])

    def IsPidValid(self, pid: int) -> bool:
        return pid in self.all_players.keys()

    ################################## gRPC Functions ##################################

    def GetNonSessionPids(self, request, context):
        with self.lock:
            pids = [pid for pid, info in self.all_players.items() if info.session_id == -1]

        return grpc_tools_pb2.PidList(pids=pids)

    def GetLightSessionInfo(self, request, context):
        client_pid = request.player_id

        with self.lock:
            if not self.IsPidValid(client_pid):
                return grpc_tools_pb2.LightSessionInfo(session_id=-1, player_role='', is_pid_valid=False, is_day=True,
                                                       mafia_pids=[], other_pids=[])

            sid = self.all_players[client_pid].session_id

            is_day, mafia_pids, other_pids, player_role = True, [], [], ''
            if sid != -1:
                is_day = self.IsDayTime(sid)
                mafia_pids = self.GetPidsByRole(sid, 'mafia')
                other_pids = self.GetPidsByRole(sid, 'ghost') + self.GetPidsByRole(sid, 'cop') + self.GetPidsByRole(sid, 'civil')
                player_role = self.GetRoleByPid(sid, client_pid)

        return grpc_tools_pb2.LightSessionInfo(session_id=sid, player_role=player_role, is_pid_valid=True, is_day=is_day,
                                               mafia_pids=mafia_pids, other_pids=other_pids)

    def GetSessionInfo(self, request, context):
        client_pid = request.player_id

        with self.lock:
            if not self.IsPidValid(client_pid):
                return grpc_tools_pb2.SessionInfo(session_id=-1, is_day=True, players=[])

            sid = self.all_players[client_pid].session_id

            is_day, players = True, []
            if sid != -1:
                is_day = self.IsDayTime(sid)

                for pid in self.GetSessionPids(sid):
                    name = self.all_players[pid].player_name

                    role = self.GetRoleByPid(sid, pid)
                    if pid != client_pid and role != 'ghost':
                        role = '?'

                    players.append(grpc_tools_pb2.SessionPlayer(player_id=pid, player_name=name, player_role=role))

        return grpc_tools_pb2.SessionInfo(session_id=sid, is_day=is_day, players=players)

    def GetAllPlayers(self, request, context):
        with self.lock:
            players = list(self.all_players.values())

        return grpc_tools_pb2.PlayerList(all_players=players)

    def GetValidActions(self, request, context):
        pid = request.player_id
        valid_actions = []

        with self.lock:
            if not self.IsPidValid(pid):
                return grpc_tools_pb2.Actions(actions=[])

            sid = self.all_players[pid].session_id
            if sid != -1:
                valid_actions = self.GetPidActions(sid, pid)

        return grpc_tools_pb2.Actions(actions=valid_actions)

    def OnClientConnect(self, request, context):
        with self.lock:
            pid = self.GetUniqueId()
            player = grpc_tools_pb2.Player(
                player_name=request.player_name,
                player_id=pid,
                session_id=-1,
            )

            self.all_players[pid] = player
            self.notify[pid] = []
            self.last_hb_time[pid] = datetime.now()

            skip_pid = [pid for pid, info in self.all_players.items() if info.session_id != -1]
            self.NotifyAllExcept(skip_pid, f'Player with id {pid} ({request.player_name}) came to server')

            print(f'Player with id {pid} ({request.player_name}) came to server')

        return grpc_tools_pb2.PlayerId(player_id=player.player_id)

    def OnClientAction(self, request, context):
        with self.lock:
            if not self.IsPidValid(request.player_id):
                return grpc_tools_pb2.ActionResponse(is_success=False)

            success = self.UpdateSessionWithAction(request.player_id, request.action)

        return grpc_tools_pb2.ActionResponse(is_success=success)

    def OnClientHeartbeat(self, request, context):
        pid = request.player_id

        with self.lock:
            if not self.IsPidValid(pid):
                return grpc_tools_pb2.Actions(session_id=-1, actions=[])

            self.last_hb_time[pid] = datetime.now()
            actions = self.notify[pid].copy()
            self.notify[pid].clear()
            sid = self.all_players[pid].session_id

        return grpc_tools_pb2.Actions(session_id=sid, actions=actions)

    ####################################################################################


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grpc_tools_pb2_grpc.add_MafiaGameServicer_to_server(MafiaGameServicer(), server)

    addr = str(os.environ.get('SERVER_ADDR', '0.0.0.0:50051'))
    server.add_insecure_port(addr)

    server.start()
    print(f'Server start with addr {addr}')
    server.wait_for_termination()


if __name__ == "__main__":
    try:
        serve()
    except:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
