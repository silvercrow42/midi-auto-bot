import os
import sys

import webview

from api.restful_api import RestfulApi
from api.event_bus_api import event_bus
from sqllite.sql_utils import create_tables
from utils.config_utils import ConfigField
from utils.web_socket_rpc_client import WebSocketRpcClient
from utils.yaml_config_manager import cm


# 判断是否是打包后的环境
def is_bundled():
    return getattr(sys, 'frozen', False)


# 获取资源文件的绝对路径
def get_resource_path(relative_path):
    if is_bundled():
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


if __name__ == '__main__':
    # 开发环境和生产环境加载不同的 URL
    if is_bundled():
        # 打包后加载构建的静态文件
        url = get_resource_path('dist/index.html')
        # 对于 PyInstaller 打包，html_file_path 可能需要调整
        # url = 'dist/index.html' # 或者直接使用相对路径，取决于打包数据的添加方式
    else:
        # 开发环境加载 Vue 开发服务器的地址
        url = 'http://localhost:5173'  # Vite 默认开发服务器地址
    restful_api = RestfulApi()
    ws_client = WebSocketRpcClient(restful_api, cm.get(ConfigField.WEB_SOCKET_URI))
    ws_client.start()
    window = webview.create_window(
        'MIDI 自动演奏器',
        url,
        js_api=restful_api,  # 将 api 实例暴露给前端 js
        width=1000,
        height=700,
        min_size=(800, 600)
    )
    event_bus.load_window(window)
    create_tables()
    webview.start(debug=True if not is_bundled() else False)  # 开发环境开启调试模式
