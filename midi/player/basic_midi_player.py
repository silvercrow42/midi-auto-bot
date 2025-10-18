import threading
import time
from datetime import datetime
from enum import Enum, auto
from typing import Callable, List, Any, Dict

import mido

from api import event_bus
from midi.event.midi_events import MidiEvent, NoteOnEvent, IgnoreNoteOnEvent, NoteOffEvent, IgnoreNoteOffEvent, \
    ControlChangeEvent, ProgramChangeEvent, PitchWheelEvent
from midi.player.progress_listener import ProgressListener
from utils.interruptible_waiter import InterruptibleWaiter
from utils.midi_file_utils import get_track_summaries, get_tempos, extract_midi_messages
from utils.window_controller import WindowController


class PlayerState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class BasicMidiPlayer:
    def __init__(self, window_controller: WindowController):
        self.state = PlayerState.STOPPED
        self.current_time = 0.0  # 当前播放时间（秒）
        self.total_time = 0.0  # MIDI文件总时长（秒）
        self.play_thread = None
        self.event_handlers = {
            'note_on': [],
            'note_off': [],
            'control_change': [],
            'program_change': [],
            'pitchwheel': [],
            'all_events': [],
            'ignore_note_on': [],
            'ignore_note_off': [],
        }
        self.midi_file: mido.MidiFile | None = None
        self.messages = []
        self._programs = [0]
        self._progress_listener = ProgressListener()
        self._window_controller = window_controller
        self.interruptible_waiter = InterruptibleWaiter()

    @staticmethod
    def get_tempo(track):
        """从音轨中提取速度信息"""
        for msg in track:
            if msg.type == 'set_tempo':
                return msg.tempo  # 返回微秒每四分音符
        return None  # 默认速度 (120 BPM)

    def get_midi_file(self):
        if self.midi_file is None:
            raise Exception('请先选择一个MIDI文件！')
        return self.midi_file

    def load_midi_file(self, file_path: str):
        """加载MIDI文件"""
        if self.state != PlayerState.STOPPED:
            self.stop()

        self.midi_file = mido.MidiFile(file_path)

        self.total_time = 0.0

        # 解析所有消息并计算时间戳
        self.messages = extract_midi_messages(self.midi_file)
        self.total_time = self.messages[-1][0]
        self._set_current_time(0.0)
        self._progress_listener.set_max_time(self.total_time)

    def set_programs(self, programs: List[int]):
        """设置播放的通道"""
        self._programs = programs

    def get_programs(self) -> List[int]:
        """获取播放的通道"""
        return self._programs

    def get_track_summaries(self) -> List[Dict[str, Any]]:
        """
        获取 MIDI 文件中每个音轨的摘要信息

        :return: 音轨摘要信息列表
        """
        return get_track_summaries(self.get_midi_file().tracks)

    def register_event_handler(self, event_type: str, handler: Callable[[MidiEvent], None]):
        """注册事件处理器"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
        else:
            raise ValueError(f"未知的事件类型: {event_type}")

    def unregister_event_handler(self, event_type: str, handler: Callable[[MidiEvent], None]):
        """取消注册事件处理器"""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)

    def _dispatch_event(self, event: MidiEvent):
        """分发事件到所有注册的处理器"""
        # 分发到特定类型处理器
        if isinstance(event, NoteOnEvent):
            for handler in self.event_handlers['note_on']:
                handler(event)
        elif isinstance(event, IgnoreNoteOnEvent):
            for handler in self.event_handlers['ignore_note_on']:
                handler(event)
        elif isinstance(event, NoteOffEvent):
            for handler in self.event_handlers['note_off']:
                handler(event)
        elif isinstance(event, IgnoreNoteOffEvent):
            for handler in self.event_handlers['ignore_note_off']:
                handler(event)
        elif isinstance(event, ControlChangeEvent):
            for handler in self.event_handlers['control_change']:
                handler(event)
        elif isinstance(event, ProgramChangeEvent):
            for handler in self.event_handlers['program_change']:
                handler(event)
        elif isinstance(event, PitchWheelEvent):
            for handler in self.event_handlers['pitchwheel']:
                handler(event)

        # 分发到所有事件处理器
        for handler in self.event_handlers['all_events']:
            handler(event)

    def _create_event(self, timestamp: float, message: dict) -> MidiEvent:
        """根据MIDI消息类型创建相应的事件对象"""
        midi_msg_type = message['type']
        track_index = message['track']
        if track_index in self._programs:
            if midi_msg_type == 'note_on' and message['velocity'] <= 0:
                midi_msg_type = 'note_off'
            if midi_msg_type == 'note_on':
                if True:
                    return NoteOnEvent(timestamp, message)
                else:
                    return IgnoreNoteOnEvent(timestamp, message)
            elif midi_msg_type == 'note_off':
                if True:
                    return NoteOffEvent(timestamp, message)
                else:
                    return IgnoreNoteOffEvent(timestamp, message)
            elif midi_msg_type == 'control_change':
                return ControlChangeEvent(timestamp, message)
            elif midi_msg_type == 'program_change':
                return ProgramChangeEvent(timestamp, message)
            elif midi_msg_type == 'pitchwheel':
                return PitchWheelEvent(timestamp, message)
            else:
                return MidiEvent(timestamp, message)

    def _playback_loop(self):
        message_index = 0
        # 找到当前时间对应的消息索引
        for i, (msg_time, msg) in enumerate(self.messages):
            if msg_time >= self.current_time:
                message_index = i
                break
        while not self.interruptible_waiter.is_interrupted() and message_index < len(self.messages):
            # 获取下一条消息
            msg_time, msg = self.messages[message_index]

            # 计算应该触发消息的时间
            sleep_time = msg_time - self.current_time
            if sleep_time > 0:
                remainder = self.interruptible_waiter.wait(sleep_time)
                if remainder > 0:
                    # 当前时间被中断表示被暂停，设置进度条后退出循环
                    self._set_current_time(self.current_time + remainder)
                    break
            # 触发事件
            event = self._create_event(msg_time, msg)
            self._dispatch_event(event)

            # 更新当前时间和消息索引(不推送事件，由专门的进度条监听器推送)
            self._set_current_time(msg_time, push_event=False)
            message_index += 1

    def play(self):
        """开始播放"""
        if self.state == PlayerState.PLAYING:
            return

        if self.state == PlayerState.STOPPED or self.state == PlayerState.PAUSED:
            self.interruptible_waiter.clear_interrupt()
            self.play_thread = threading.Thread(target=self._playback_loop)
            self.play_thread.daemon = True
            self.play_thread.start()
            self._progress_listener.start()

        self.state = PlayerState.PLAYING
        event_bus.set_is_play(True)

    def stop(self):
        """停止播放"""
        if self.state != PlayerState.STOPPED:
            self.interruptible_waiter.interrupt()
            if self.play_thread and self.play_thread.is_alive():
                self.play_thread.join(timeout=1.0)
            self.state = PlayerState.STOPPED
            self._set_current_time(0.0)
            self._progress_listener.stop()
        self._window_controller.clear()
        event_bus.set_is_play(False)

    def pause(self):
        """暂停播放"""
        if self.state == PlayerState.PLAYING:
            self.interruptible_waiter.interrupt()
            if self.play_thread and self.play_thread.is_alive():
                self.play_thread.join(timeout=1.0)
            self.state = PlayerState.PAUSED
            self._progress_listener.stop()
        self._window_controller.clear()
        event_bus.set_is_play(False)

    def seek(self, position: float):
        """跳转到指定位置（秒）"""
        if position < 0:
            position = 0
        if position > self.total_time:
            position = self.total_time
        self.pause()
        # 如果当前是暂停状态，也需要更新当前时间
        self._set_current_time(position)
        self.play()

    def _set_current_time(self, time: float, push_event=True):
        """设置当前时间"""
        self.current_time = time
        self._progress_listener.set_current_time(time)
        if push_event:
            event_bus.set_current_time(time)

    def play_sync(self, position: float, command_time):
        self.seek_sync(position, command_time)
        self.play()

    def pause_sync(self, position, command_time):
        self.pause()
        self.seek_sync(position, command_time)

    def seek_sync(self, position: float, command_time):
        # 计算时间差
        command_time_obj = datetime.strptime(command_time, '%Y-%m-%d %H:%M:%S.%f')
        time_diff = datetime.now() - command_time_obj
        # 计算应该播放的位置
        target_position = position + time_diff.microseconds / 1000.0 / 1000.0
        # 跳转到目标位置
        self.seek(target_position)

    def get_position(self) -> float:
        """获取当前播放位置（秒）"""
        return self.current_time

    def get_duration(self) -> float:
        """获取MIDI文件总时长（秒）"""
        return self.total_time

    def get_state(self) -> PlayerState:
        """获取播放器状态"""
        return self.state
