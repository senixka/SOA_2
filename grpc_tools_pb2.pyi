from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ActionRequest(_message.Message):
    __slots__ = ["action", "player_id"]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    action: str
    player_id: int
    def __init__(self, player_id: _Optional[int] = ..., action: _Optional[str] = ...) -> None: ...

class ActionResponse(_message.Message):
    __slots__ = ["is_success"]
    IS_SUCCESS_FIELD_NUMBER: _ClassVar[int]
    is_success: bool
    def __init__(self, is_success: bool = ...) -> None: ...

class Actions(_message.Message):
    __slots__ = ["actions", "session_id"]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    actions: _containers.RepeatedScalarFieldContainer[str]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ..., actions: _Optional[_Iterable[str]] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class LightSessionInfo(_message.Message):
    __slots__ = ["is_day", "is_pid_valid", "mafia_pids", "other_pids", "player_role", "session_id"]
    IS_DAY_FIELD_NUMBER: _ClassVar[int]
    IS_PID_VALID_FIELD_NUMBER: _ClassVar[int]
    MAFIA_PIDS_FIELD_NUMBER: _ClassVar[int]
    OTHER_PIDS_FIELD_NUMBER: _ClassVar[int]
    PLAYER_ROLE_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    is_day: bool
    is_pid_valid: bool
    mafia_pids: _containers.RepeatedScalarFieldContainer[int]
    other_pids: _containers.RepeatedScalarFieldContainer[int]
    player_role: str
    session_id: int
    def __init__(self, session_id: _Optional[int] = ..., player_role: _Optional[str] = ..., is_pid_valid: bool = ..., is_day: bool = ..., mafia_pids: _Optional[_Iterable[int]] = ..., other_pids: _Optional[_Iterable[int]] = ...) -> None: ...

class PidList(_message.Message):
    __slots__ = ["pids"]
    PIDS_FIELD_NUMBER: _ClassVar[int]
    pids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, pids: _Optional[_Iterable[int]] = ...) -> None: ...

class Player(_message.Message):
    __slots__ = ["player_id", "player_name", "session_id"]
    PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    PLAYER_NAME_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    player_id: int
    player_name: str
    session_id: int
    def __init__(self, player_id: _Optional[int] = ..., session_id: _Optional[int] = ..., player_name: _Optional[str] = ...) -> None: ...

class PlayerId(_message.Message):
    __slots__ = ["player_id"]
    PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    player_id: int
    def __init__(self, player_id: _Optional[int] = ...) -> None: ...

class PlayerList(_message.Message):
    __slots__ = ["all_players"]
    ALL_PLAYERS_FIELD_NUMBER: _ClassVar[int]
    all_players: _containers.RepeatedCompositeFieldContainer[Player]
    def __init__(self, all_players: _Optional[_Iterable[_Union[Player, _Mapping]]] = ...) -> None: ...

class PlayerName(_message.Message):
    __slots__ = ["player_name"]
    PLAYER_NAME_FIELD_NUMBER: _ClassVar[int]
    player_name: str
    def __init__(self, player_name: _Optional[str] = ...) -> None: ...

class SessionInfo(_message.Message):
    __slots__ = ["is_day", "players", "session_id"]
    IS_DAY_FIELD_NUMBER: _ClassVar[int]
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    is_day: bool
    players: _containers.RepeatedCompositeFieldContainer[SessionPlayer]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ..., is_day: bool = ..., players: _Optional[_Iterable[_Union[SessionPlayer, _Mapping]]] = ...) -> None: ...

class SessionPlayer(_message.Message):
    __slots__ = ["player_id", "player_name", "player_role"]
    PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    PLAYER_NAME_FIELD_NUMBER: _ClassVar[int]
    PLAYER_ROLE_FIELD_NUMBER: _ClassVar[int]
    player_id: int
    player_name: str
    player_role: str
    def __init__(self, player_id: _Optional[int] = ..., player_name: _Optional[str] = ..., player_role: _Optional[str] = ...) -> None: ...
