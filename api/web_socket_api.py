from api import event_bus
from api.remote_api import get_room_file
from midi import midi_player, set_channel


def websocket_expose(func):
    """
    装饰器：标记需要暴露给服务端调用的方法
    """
    func._websocket_exposed = True
    return func


class WebSocketApi:
    def __init__(self):
        super().__init__()

    @websocket_expose
    def start_playback(self, params):
        """
        供前端调用的方法：开始播放
        """
        midi_player.play_sync(params['position'], params['command_time'])

    @websocket_expose
    def stop_playback(self):
        """
        供前端调用的方法：暂停播放
        """
        midi_player.stop()

    @websocket_expose
    def pause_playback(self, params):
        """
        供前端调用的方法：暂停播放
        """
        midi_player.pause_sync(params['position'], params['command_time'])

    @websocket_expose
    def seek_playback(self, params):
        """
        供前端调用的方法：跳转到指定位置播放
        """
        midi_player.seek_sync(params['position'], params['command_time'])

    @websocket_expose
    def set_channel(self, channel):
        set_channel(channel)

    @websocket_expose
    def refresh_file(self, sha256):
        get_room_file(sha256)
        event_bus.refresh_remote_file()

    @websocket_expose
    def refresh_info(self, room_info):
        event_bus.refresh_room_info(room_info)
