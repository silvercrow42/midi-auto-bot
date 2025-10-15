import hashlib
import os

from request import get_session
from utils.config_utils import ConfigField
from utils.yaml_config_manager import cm


def url(path):
    return cm.get(ConfigField.HTTP_URI) + path


def get_ws_client():
    from websocket import ws_client
    return ws_client


def set_room_file(file_path):
    room_id = get_ws_client().room_id
    file_name = os.path.basename(file_path)
    # 打开文件并发送POST请求
    with open(file_path, 'rb') as f:
        # 读取文件内容计算哈希
        file_content = f.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        # 将文件指针重置到开头，因为前面已经读取到了末尾
        f.seek(0)
        # 文件字段（支持多个文件）
        files = {
            'file': (file_name, f, 'text/plain'),
        }
        data = {
            'size': len(file_content),  # 这里可以直接用读取的内容的长度，或者用os.path.getsize(file_path)
            'name': file_name,
            'hash': file_hash
        }
        get_session().post(url(f'/room/file/set/{room_id}'), files=files, data=data)


def get_room_file(file_hash):
    """下载文件到指定路径"""
    save_path = cm.get(ConfigField.MIDI_PATH) + '/remote.mid'
    room_id = get_ws_client().room_id
    response = get_session().get(url(f'/room/file/get/{room_id}'))
    response.raise_for_status()  # 检查请求是否成功
    # 保存文件
    with open(save_path, 'wb') as f:
        f.write(response.content)
    # 打开文件并发送POST请求
    with open(save_path, 'rb') as f:
        new_file_hash = hashlib.sha256(f.read()).hexdigest()
        if new_file_hash != file_hash:
            raise Exception('文件已损坏')
    return save_path
