from api.simple_event_throttler import SimpleEventThrottler
from utils.config_utils import ConfigField
from utils.yaml_config_manager import cm


class EventBus:

    def __init__(self):
        self._throttler = None

    # 这个方法由 pywebview 内部调用，用于注入 window 对象
    def load_window(self, window):
        self._throttler = SimpleEventThrottler(window)

    def progress(self, current_time):
        self._push_event("progress", current_time)

    def midi_note_on(self, key):
        self._push_event("noteOn", f'"{key}"')

    def midi_note_off(self, key):
        self._push_event("noteOff", f'"{key}"')

    def room_id_changed(self, room_id):
        self._push_event("roomIdChanged", f'{room_id}')

    def refresh_remote_file(self):
        remote_midi = cm.get(ConfigField.MIDI_PATH) + '/remote.mid'
        file_info = {
            "file_path": remote_midi,
            "file_name": "remote.mid",
        }
        self._push_event("refreshRemoteFile", file_info)

    def set_is_play(self, is_play):
        if is_play:
            is_play_val = "true"
        else:
            is_play_val = "false"
        self._push_event("setIsPlaying", f'{is_play_val}')

    def set_channel(self, channel):
        self._push_event("setChannel", f'{channel}')

    def _push_event(self, event_name, data=None):
        self._throttler.push_event(event_name, data)

    def _push_event_throttled(self, event_name, data=None):
        self._throttler.push_event_throttled(event_name, data)


event_bus = EventBus()
