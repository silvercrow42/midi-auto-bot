import requests
from functools import wraps

from api import remote_api, event_bus
from midi import midi_player, mapper, window_controller, set_mapper, set_channel, get_mapper, get_mapper_name
from midi.mapper.deep_key_mapper import mapping_matrix_to_json, KeyboardMapper
from midi.mapper.mapper_utils import apply_strategy, key_config_entity_to_dict
from sqllite.common_config_sqls import query_common_config, save_common_config
from sqllite.key_config_sqls import save_key_config, KeyConfigEntity, query_key_configs, query_key_config_by_id
from utils.config_utils import ConfigField
from utils.logger import get_logger
from utils.midi_file_utils import list_current_directory_midis
from utils.yaml_config_manager import cm


def get_ws_client():
    from websocket import ws_client
    return ws_client


def api_response(func):
    """
    统一API响应格式和异常处理的装饰器
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            if isinstance(result, dict) and 'success' in result:
                return result
            return {"success": True, "message": "操作成功", "data": result}
        except Exception as e:
            get_logger().error(f"API调用失败 - {func.__name__}: {str(e)}", exc_info=True)
            return {"success": False, "message": f"操作失败: {str(e)}"}

    return wrapper


class RestfulApi:
    def __init__(self):
        super().__init__()

    @api_response
    # @logger(log_params=True)
    def load_midi_file(self, file_path="./flower_dance"):
        """
        供前端调用的方法：加载 MIDI 文件
        """
        # 播放器解析midi文件
        midi_player.load_midi_file(file_path)
        summaries = midi_player.get_track_summaries()
        channel = None
        for summary in summaries:
            if summary['channels']:
                channel = summary['channels'][0]
                break
        set_channel(channel)
        duration = midi_player.get_duration()
        return {"message": f"MIDI 文件加载成功: {file_path}", "duration": duration}

    @api_response
    def start_cmd(self, position=None):
        """
        供前端调用的方法：开始播放
        """
        if position is not None:
            requests.get(cm.get(ConfigField.HTTP_URI) + '/room/play',
                         params={"roomId": get_ws_client().room_id, "position": position})
        else:
            midi_player.play()

    @api_response
    def stop_cmd(self, is_sync=False):
        """
        供前端调用的方法：停止播放
        """
        if is_sync:
            requests.get(cm.get(ConfigField.HTTP_URI) + '/room/stop',
                         params={"roomId": get_ws_client().room_id})
        else:
            midi_player.stop()

    @api_response
    def pause_cmd(self, position=None):
        """
        供前端调用的方法：暂停播放
        """
        if position is not None:
            requests.get(cm.get(ConfigField.HTTP_URI) + '/room/pause',
                         params={"roomId": get_ws_client().room_id, "position": position})
        else:
            midi_player.pause()

    @api_response
    def seek_cmd(self, position, is_sync=False):
        """
        供前端调用的方法：跳转到指定位置播放
        """
        if is_sync:
            requests.get(cm.get(ConfigField.HTTP_URI) + '/room/seek',
                         params={"roomId": get_ws_client().room_id, "position": position})
        else:
            midi_player.seek(position)

    @api_response
    # @logger(log_result=True)
    def get_track_summaries(self):
        return midi_player.get_track_summaries()

    @api_response
    # @logger(log_result=True)
    def get_channel(self):
        return midi_player.get_channels()[0]

    @api_response
    def set_channel_cmd(self, channel, client_ids=None):
        if client_ids is not None:
            requests.get(cm.get(ConfigField.HTTP_URI) + '/room/channel/set',
                         params={
                             "roomId": get_ws_client().room_id,
                             "clientIds": client_ids,
                             "channel": channel
                         })
        else:
            set_channel(channel)

    @api_response
    def refresh_midi_list(self):
        return list_current_directory_midis()

    @api_response
    # @logger(log_params=True)
    def keydown(self, key):
        return window_controller.press(key, keyupdown=2, push_event=False)

    @api_response
    # @logger(log_params=True)
    def keyup(self, key):
        return window_controller.press(key, keyupdown=1, push_event=False)

    @api_response
    # @logger
    def get_all_windows(self):
        """获取所有进程窗口"""
        return window_controller.get_all_windows()

    @api_response
    # @logger(log_params=True)
    def set_target_window(self, hwnd):
        """设置当前附加的进程窗口"""
        return window_controller.set_target_window(hwnd)

    @api_response
    def get_target_window(self):
        """获取当前附加的进程窗口"""
        return window_controller.get_target_window()

    @api_response
    def get_mapping_matrix(self):
        return mapping_matrix_to_json(mapper.mapping_matrix)

    @api_response
    def apply_strategy(self, config_json):
        return apply_strategy(config_json)

    @api_response
    def get_strategy(self, id):
        key_config_entity = query_key_config_by_id(id)
        return key_config_entity_to_dict(key_config_entity)

    @api_response
    def save_strategy(self, name, type, mapper_json, id=None):
        new_mapper = KeyboardMapper.from_json(mapper_json)
        config_entity = KeyConfigEntity(name=name, type=type, config_json=new_mapper.to_json())
        if id:
            config_entity.id = id
        save_key_config([config_entity])

    @api_response
    def get_strategy_list(self, name=None, type=None):
        return query_key_configs(name, type)

    @api_response
    def use_strategy(self, id):
        set_mapper(query_key_config_by_id(id))
        return get_mapper_name()

    @api_response
    def get_strategy_name(self):
        return get_mapper_name()

    @api_response
    def change_transpose_octaves(self, octaves):
        mapper = get_mapper()
        mapper.set_transpose(octaves)
        mapper.apply_strategies()
        window_controller.clear()

    # 合奏相关功能
    @api_response
    def join_room(self, room_id=None, room_name=None):
        response = requests.get(cm.get(ConfigField.HTTP_URI) + '/room/join',
                                params={"roomId": room_id, "name": room_name,
                                        "clientId": get_ws_client().client_id})
        if response.status_code == 200:
            res = response.json()
            get_ws_client().room_id = res["data"]
            return res["data"]
        raise Exception(response.text)

    @api_response
    def get_room(self, room_id=None):
        response = requests.get(cm.get(ConfigField.HTTP_URI) + '/room/get',
                                params={"roomId": room_id})
        if response.status_code == 200:
            res = response.json()
            return res["data"]
        raise Exception(response.text)

    @api_response
    def leave_room(self):
        response = requests.get(cm.get(ConfigField.HTTP_URI) + '/room/leave',
                                params={"clientId": get_ws_client().client_id})
        if response.status_code != 200:
            raise Exception(response.text)

    @api_response
    def list_rooms(self):
        response = requests.get(cm.get(ConfigField.HTTP_URI) + '/room/list')
        return response.json()

    @api_response
    def set_room_file(self, file_path):
        remote_api.set_room_file(file_path)

    @api_response
    def refresh_remote_file(self, sha256):
        remote_api.get_room_file(sha256)
        event_bus.refresh_remote_file()

    @api_response
    def change_username(self, username):
        client_name_config = query_common_config("client_name")
        client_name_config.config = username
        save_common_config([client_name_config])
        return username

    @api_response
    def get_username(self):
        client_name_config = query_common_config("client_name")
        return client_name_config.config
