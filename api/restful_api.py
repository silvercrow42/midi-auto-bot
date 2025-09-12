from midi.controller.basic_controller import BasicController

controller = BasicController()


class RestfulApi:
    def __init__(self):
        super().__init__()

    def load_midi_file(self, file_path="./flower_dance"):
        """
        供前端调用的方法：加载 MIDI 文件
        """
        try:
            controller.load_midi(file_path)
            duration = controller.get_duration()
            return {"success": True, "message": f"MIDI 文件加载成功: {file_path}", "duration": duration}  # 示例数据
        except Exception as e:
            return {"success": False, "message": f"加载失败: {str(e)}"}

    def start_playback(self):
        """
        供前端调用的方法：开始播放
        """
        try:
            controller.play()
            return {"success": True, "message": "开始播放"}
        except Exception as e:
            return {"success": False, "message": f"播放失败: {str(e)}"}

    def stop_playback(self):
        """
        供前端调用的方法：停止播放
        """
        try:
            controller.stop()
            return {"success": True, "message": "停止播放"}
        except Exception as e:
            return {"success": False, "message": f"停止失败: {str(e)}"}

    def pause_playback(self):
        """
        供前端调用的方法：暂停播放
        """
        try:
            controller.pause()
            return {"success": True, "message": "暂停播放"}
        except Exception as e:
            return {"success": False, "message": f"暂停失败: {str(e)}"}

    def seek_playback(self, position):
        """
        供前端调用的方法：跳转到指定位置播放
        """
        try:
            controller.seek(position)
            return {"success": True, "message": f"跳转到指定位置播放: {position}"}
        except Exception as e:
            return {"success": False, "message": f"跳转失败: {str(e)}"}

    def get_track_summaries(self):
        return controller.get_track_summaries()

    def get_channels(self):
        return controller.get_channels()

    def set_channels(self, channels):
        return controller.set_channels(channels)

    def refresh_midi_list(self):
        return controller.refresh_midi_list()

    def keydown(self, key):
        return controller.keydown(key)

    def keyup(self, key):
        return controller.keyup(key)
