from backend.utils.config_utils import ConfigField
from backend.utils.yaml_config_manager import cm
from backend.websocket.web_socket_rpc_client import WebSocketRpcClient
from backend.api import websocket_api


def init_websocket_client():
    if cm.get(ConfigField.WEB_SOCKET_ENABLE):
        server_url = 'ws://' + cm.get(ConfigField.SERVER_URI)
        ws_prefix = cm.get(ConfigField.WEB_SOCKET_PREFIX)
        if ws_prefix is not None:
            server_url = server_url + '/' + ws_prefix
        return WebSocketRpcClient(websocket_api, server_url)
    return None


ws_client = init_websocket_client()
