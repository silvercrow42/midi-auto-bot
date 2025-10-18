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
        get_session().post(url(f'/room/file/set'), files=files, data=data)


def get_room_file(file_hash):
    """下载文件到指定路径"""
    save_path = cm.get(ConfigField.MIDI_PATH) + '/remote.mid'
    response = get_session().get(url(f'/room/file/get'))
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


def room_start(position):
    get_session().get(cm.get(ConfigField.HTTP_URI) + '/room/play', params={"position": position})


def room_stop():
    get_session().get(cm.get(ConfigField.HTTP_URI) + '/room/stop')


def room_pause(position):
    get_session().get(cm.get(ConfigField.HTTP_URI) + '/room/pause', params={"position": position})


def room_seek(position):
    get_session().get(cm.get(ConfigField.HTTP_URI) + '/room/seek', params={"position": position})


def room_program_set(programs, client_ids=None):
    get_session().get(cm.get(ConfigField.HTTP_URI) + '/room/program/set',
                      params={
                          "clientIds": client_ids,
                          "programs": programs
                      })


def room_leave():
    get_session().get(cm.get(ConfigField.HTTP_URI) + '/room/leave')


def room_get():
    return get_session().get(cm.get(ConfigField.HTTP_URI) + '/room/get').json()["data"]


def room_join(room_id):
    return get_session().get(cm.get(ConfigField.HTTP_URI) + '/room/join', params={"roomId": room_id})


def room_create(room_name, secret=False):
    return get_session().get(cm.get(ConfigField.HTTP_URI) + '/room/create',
                             params={"name": room_name, 'secret': secret})
