from utils.config_utils import ConfigField
from utils.yaml_config_manager import cm
from websocket.web_socket_rpc_client import WebSocketRpcClient
from api import websocket_api


def init_websocket_client():
    if cm.get(ConfigField.WEB_SOCKET_ENABLE):
        return WebSocketRpcClient(websocket_api, cm.get(ConfigField.WEB_SOCKET_URI))
    return None


ws_client = init_websocket_client()
