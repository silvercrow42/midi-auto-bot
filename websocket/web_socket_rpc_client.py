import asyncio
import inspect
import json
import threading
import uuid
import websockets

from api import event_bus
from sqllite.common_config_sqls import query_common_config
from utils.config_utils import ConfigField
from utils.yaml_config_manager import cm

client_name_config = query_common_config("client_name")


class WebSocketRpcClient:
    def __init__(self, api_instance, server_uri="ws://localhost:8765"):
        self.api_instance = api_instance
        self.server_uri = server_uri
        self.websocket = None
        self.connected = False
        self.client_id = str(uuid.uuid4())  # 客户端唯一标识
        self.room_id = None

        # 添加重试配置
        self.max_retries = cm.get(ConfigField.WEB_SOCKET_RETRY_MAX)
        self.retry_delay = cm.get(ConfigField.WEB_SOCKET_RETRY_DELAY)  # 秒
        self.retry_count = 0

    async def send_message(self, message_type, data=None):
        """
        发送消息到服务端
        :param message_type: 消息类型
        :param data: 消息数据
        """
        if not self.connected or not self.websocket:
            print("WebSocket not connected, cannot send message")
            return False

        try:
            message = {
                "type": message_type,
                "client_id": self.client_id
            }
            if data:
                message.update(data)

            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False

    def _get_exposed_methods(self):
        """获取所有标记为暴露的方法"""
        methods = {}
        for name, method in inspect.getmembers(self.api_instance, predicate=inspect.ismethod):
            if hasattr(method, '_websocket_exposed') and method._websocket_exposed:
                methods[name] = method
        return methods

    async def connect_with_retry(self):
        """带重试机制的连接方法"""
        while self.retry_count < self.max_retries:
            try:
                self.websocket = await websockets.connect(self.server_uri)
                self.connected = True
                self.retry_count = 0  # 重置重试计数

                # 注册客户端
                register_msg = {
                    "type": "register",
                    "data": client_name_config.config
                }
                await self.websocket.send(json.dumps(register_msg))
                return True

            except Exception as e:
                self.retry_count += 1
                print(f"Connection attempt {self.retry_count} failed: {e}")

                if self.retry_count < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    print("Max retries reached. Giving up.")
                    return False
        return False

    async def _listen_for_messages(self):
        """监听来自服务端的消息"""
        exposed_methods = self._get_exposed_methods()

        async for message in self.websocket:
            try:
                data = json.loads(message)

                # 处理方法调用请求
                type = data.get("type")
                params = data.get("data")
                if type == "method_call":
                    method_name = data.get("method")
                    if method_name in exposed_methods:
                        method = exposed_methods[method_name]
                        # 调用本地方法
                        if params is not None:
                            method(params)
                        else:
                            method()
                elif type == "registered":
                    self.client_id = data.get("data")
                    event_bus.set_client_id(self.client_id)
            except json.JSONDecodeError:
                print("Invalid JSON received")
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed unexpectedly")
                self.connected = False
                # 触发重连
                await self.reconnect()
            except Exception as e:
                print(f"Error processing message: {e}")

    async def reconnect(self):
        """重新连接"""
        if not self.connected:
            print("Attempting to reconnect...")
            success = await self.connect_with_retry()
            if success:
                print("Reconnected successfully")
            else:
                print("Failed to reconnect")

    def start(self):
        """启动WebSocket客户端（非阻塞）"""

        def run_in_thread():
            async def main_loop():
                while True:
                    try:
                        print("Connecting to server...")
                        success = await self.connect_with_retry()
                        if success:
                            print("Connected to server")
                            await self._listen_for_messages()
                            # 如果_listen_for_messages退出，说明连接已断开
                            print("Connection lost, attempting to reconnect...")
                        else:
                            print("Failed to establish connection. Retrying...")
                    except Exception as e:
                        print(f"Error in main loop: {e}")
                        self.connected = False

                    # 确保在重试前检查连接状态
                    if not self.connected:
                        await asyncio.sleep(self.retry_delay)

            asyncio.run(main_loop())

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
