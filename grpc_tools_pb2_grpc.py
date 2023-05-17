# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import grpc_tools_pb2 as grpc__tools__pb2


class MafiaGameStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.OnClientConnect = channel.unary_unary(
                '/mafia_game.MafiaGame/OnClientConnect',
                request_serializer=grpc__tools__pb2.PlayerName.SerializeToString,
                response_deserializer=grpc__tools__pb2.PlayerId.FromString,
                )
        self.OnClientAction = channel.unary_unary(
                '/mafia_game.MafiaGame/OnClientAction',
                request_serializer=grpc__tools__pb2.ActionRequest.SerializeToString,
                response_deserializer=grpc__tools__pb2.ActionResponse.FromString,
                )
        self.OnClientHeartbeat = channel.unary_unary(
                '/mafia_game.MafiaGame/OnClientHeartbeat',
                request_serializer=grpc__tools__pb2.PlayerId.SerializeToString,
                response_deserializer=grpc__tools__pb2.Actions.FromString,
                )
        self.GetAllPlayers = channel.unary_unary(
                '/mafia_game.MafiaGame/GetAllPlayers',
                request_serializer=grpc__tools__pb2.Empty.SerializeToString,
                response_deserializer=grpc__tools__pb2.PlayerList.FromString,
                )
        self.GetValidActions = channel.unary_unary(
                '/mafia_game.MafiaGame/GetValidActions',
                request_serializer=grpc__tools__pb2.PlayerId.SerializeToString,
                response_deserializer=grpc__tools__pb2.Actions.FromString,
                )
        self.GetSessionInfo = channel.unary_unary(
                '/mafia_game.MafiaGame/GetSessionInfo',
                request_serializer=grpc__tools__pb2.PlayerId.SerializeToString,
                response_deserializer=grpc__tools__pb2.SessionInfo.FromString,
                )


class MafiaGameServicer(object):
    """Missing associated documentation comment in .proto file."""

    def OnClientConnect(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def OnClientAction(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def OnClientHeartbeat(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAllPlayers(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetValidActions(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetSessionInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_MafiaGameServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'OnClientConnect': grpc.unary_unary_rpc_method_handler(
                    servicer.OnClientConnect,
                    request_deserializer=grpc__tools__pb2.PlayerName.FromString,
                    response_serializer=grpc__tools__pb2.PlayerId.SerializeToString,
            ),
            'OnClientAction': grpc.unary_unary_rpc_method_handler(
                    servicer.OnClientAction,
                    request_deserializer=grpc__tools__pb2.ActionRequest.FromString,
                    response_serializer=grpc__tools__pb2.ActionResponse.SerializeToString,
            ),
            'OnClientHeartbeat': grpc.unary_unary_rpc_method_handler(
                    servicer.OnClientHeartbeat,
                    request_deserializer=grpc__tools__pb2.PlayerId.FromString,
                    response_serializer=grpc__tools__pb2.Actions.SerializeToString,
            ),
            'GetAllPlayers': grpc.unary_unary_rpc_method_handler(
                    servicer.GetAllPlayers,
                    request_deserializer=grpc__tools__pb2.Empty.FromString,
                    response_serializer=grpc__tools__pb2.PlayerList.SerializeToString,
            ),
            'GetValidActions': grpc.unary_unary_rpc_method_handler(
                    servicer.GetValidActions,
                    request_deserializer=grpc__tools__pb2.PlayerId.FromString,
                    response_serializer=grpc__tools__pb2.Actions.SerializeToString,
            ),
            'GetSessionInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.GetSessionInfo,
                    request_deserializer=grpc__tools__pb2.PlayerId.FromString,
                    response_serializer=grpc__tools__pb2.SessionInfo.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'mafia_game.MafiaGame', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class MafiaGame(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def OnClientConnect(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mafia_game.MafiaGame/OnClientConnect',
            grpc__tools__pb2.PlayerName.SerializeToString,
            grpc__tools__pb2.PlayerId.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def OnClientAction(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mafia_game.MafiaGame/OnClientAction',
            grpc__tools__pb2.ActionRequest.SerializeToString,
            grpc__tools__pb2.ActionResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def OnClientHeartbeat(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mafia_game.MafiaGame/OnClientHeartbeat',
            grpc__tools__pb2.PlayerId.SerializeToString,
            grpc__tools__pb2.Actions.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetAllPlayers(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mafia_game.MafiaGame/GetAllPlayers',
            grpc__tools__pb2.Empty.SerializeToString,
            grpc__tools__pb2.PlayerList.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetValidActions(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mafia_game.MafiaGame/GetValidActions',
            grpc__tools__pb2.PlayerId.SerializeToString,
            grpc__tools__pb2.Actions.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetSessionInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mafia_game.MafiaGame/GetSessionInfo',
            grpc__tools__pb2.PlayerId.SerializeToString,
            grpc__tools__pb2.SessionInfo.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
