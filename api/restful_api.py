from functools import wraps

from api import midi_player, window_controller, playing_channel, set_channel, mapper
from utils.logger import get_logger, logger
from utils.midi_file_utils import list_current_directory_midis


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
    @logger(log_params=True)
    def load_midi_file(self, file_path="./flower_dance"):
        """
        供前端调用的方法：加载 MIDI 文件
        """
        # 播放器解析midi文件
        midi_player.load_midi_file(file_path, [0])
        duration = midi_player.get_duration()
        return {"message": f"MIDI 文件加载成功: {file_path}", "duration": duration}

    @api_response
    @logger()
    def start_playback(self):
        """
        供前端调用的方法：开始播放
        """
        midi_player.play()

    @api_response
    @logger()
    def stop_playback(self):
        """
        供前端调用的方法：停止播放
        """
        midi_player.stop()

    @api_response
    @logger()
    def pause_playback(self):
        """
        供前端调用的方法：暂停播放
        """
        midi_player.pause()

    @api_response
    @logger(log_params=True)
    def seek_playback(self, position):
        """
        供前端调用的方法：跳转到指定位置播放
        """
        midi_player.seek(position)

    @api_response
    @logger(log_result=True)
    def get_track_summaries(self):
        return midi_player.get_track_summaries()

    @api_response
    @logger(log_result=True)
    def get_channel(self):
        return playing_channel

    @api_response
    @logger(log_params=True)
    def set_channel(self, channel):
        set_channel(channel)

    @api_response
    @logger(log_result=True)
    def refresh_midi_list(self):
        return list_current_directory_midis()

    @api_response
    @logger(log_params=True)
    def keydown(self, key):
        return window_controller.keydown(key)

    @api_response
    @logger(log_params=True)
    def keyup(self, key):
        return window_controller.keyup(key)

    @api_response
    def get_key_map(self, key):
        return []

    @api_response
    def set_key_map(self, key, notes):
        pass

    @api_response
    @logger(log_params=True)
    def apply_strategies(self, level, octave, ratio):
        mapper.set_transpose(level)
        mapper.set_expand(octave, ratio)
        mapper.apply_strategies()
        window_controller.clear()

    @api_response
    @logger
    def get_all_windows(self):
        """获取所有进程窗口"""
        return window_controller.get_all_windows()

    @api_response
    @logger(log_params=True)
    def set_target_window(self, hwnd):
        """设置当前附加的进程窗口"""
        return window_controller.set_target_window(hwnd)
