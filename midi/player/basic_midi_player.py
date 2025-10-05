import threading
import time

from datetime import datetime
from enum import Enum, auto
from typing import Callable, List, Any, Dict

import mido

from midi.event.midi_events import MidiEvent, NoteOnEvent, IgnoreNoteOnEvent, NoteOffEvent, IgnoreNoteOffEvent, \
    ControlChangeEvent, ProgramChangeEvent, PitchWheelEvent
from midi.player.progress_listener import ProgressListener


class PlayerState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class BasicMidiPlayer:
    def __init__(self):
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
            'all_events': []
        }
        self.midi_file = None
        self.messages = []
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._seek_event = threading.Event()
        self._seek_position = 0.0
        self._channels = []
        self._progress_listener = ProgressListener()

    def load_midi_file(self, file_path: str, channels: List[int]):
        """加载MIDI文件"""
        if self.state != PlayerState.STOPPED:
            self.stop()

        self.midi_file = mido.MidiFile(file_path)

        self.messages = []
        self.total_time = 0.0

        # 解析所有消息并计算时间戳
        current_time = 0.0
        for msg in self.midi_file:
            current_time += msg.time
            if not msg.is_meta:
                self.messages.append((current_time, msg))

        self.total_time = current_time
        self._set_current_time(0.0)
        self._channels = channels

        self._progress_listener.set_max_time(self.total_time)

    def get_track_summaries(self) -> List[Dict[str, Any]]:
        """
        获取 MIDI 文件中每个音轨的摘要信息

        :param file_path: MIDI 文件路径
        :return: 音轨摘要信息列表
        """
        tracks_summary = []

        tracks = enumerate(self.midi_file.tracks)
        for i, track in tracks:
            summary = {
                'track_index': i,
                'name': f'{i}',
                'length': len(track),
                'duration_ticks': sum(msg.time for msg in track),
                'has_notes': False,
                'instrument': None,
                'channels': set()
            }

            # 分析音轨内容
            for msg in track:
                if msg.type == 'track_name':
                    summary['name'] = msg.name
                elif msg.type == 'note_on' and msg.velocity > 0:
                    summary['has_notes'] = True
                elif msg.type == 'program_change':
                    summary['instrument'] = msg.program
                elif hasattr(msg, 'channel'):
                    summary['channels'].add(msg.channel)

            summary['channels'] = list(summary['channels'])
            tracks_summary.append(summary)

        return tracks_summary

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

    def _create_event(self, timestamp: float, message: mido.Message) -> MidiEvent:
        """根据MIDI消息类型创建相应的事件对象"""
        if message.type == 'note_on':
            if self._channels is not None and message.channel in self._channels:
                return IgnoreNoteOnEvent(timestamp, message)
            else:
                return NoteOnEvent(timestamp, message)
        elif message.type == 'note_off':
            if self._channels is not None and message.channel in self._channels:
                return IgnoreNoteOffEvent(timestamp, message)
            else:
                return NoteOffEvent(timestamp, message)
        elif message.type == 'control_change':
            return ControlChangeEvent(timestamp, message)
        elif message.type == 'program_change':
            return ProgramChangeEvent(timestamp, message)
        elif message.type == 'pitchwheel':
            return PitchWheelEvent(timestamp, message)
        else:
            return MidiEvent(timestamp, message)

    def _playback_loop(self):
        """播放循环"""
        start_time = time.time() - self.current_time
        message_index = 0

        # 找到当前时间对应的消息索引
        for i, (msg_time, msg) in enumerate(self.messages):
            if msg_time >= self.current_time:
                message_index = i
                break

        while not self._stop_event.is_set() and message_index < len(self.messages):
            # 处理暂停
            if self._pause_event.is_set() or self._stop_event.is_set():
                break

            # 处理跳转
            if self._seek_event.is_set():
                self._seek_event.clear()
                self._set_current_time(self._seek_position)
                start_time = time.time() - self.current_time

                # 重新找到当前时间对应的消息索引
                for i, (msg_time, msg) in enumerate(self.messages):
                    if msg_time >= self.current_time:
                        message_index = i
                        break
                continue

            # 获取下一条消息
            msg_time, msg = self.messages[message_index]

            # 计算应该触发消息的时间
            trigger_time = start_time + msg_time

            # 等待直到触发时间
            current_time = time.time()
            if current_time < trigger_time:
                time.sleep(trigger_time - current_time)

            # 触发事件
            event = self._create_event(msg_time, msg)
            self._dispatch_event(event)

            # 更新当前时间和消息索引
            self._set_current_time(msg_time)
            message_index += 1

        # 播放完成
        if message_index >= len(self.messages):
            self.state = PlayerState.STOPPED
            self._set_current_time(0.0)
            self._progress_listener.stop()

    def _set_current_time(self, time: float):
        """设置当前时间"""
        self.current_time = time
        self._progress_listener.set_current_time(time)

    def play(self):
        """开始播放"""
        if self.state == PlayerState.PLAYING:
            return

        if self.state == PlayerState.STOPPED or self.state == PlayerState.PAUSED:
            self._stop_event.clear()
            self._pause_event.clear()
            self._seek_event.clear()
            self.play_thread = threading.Thread(target=self._playback_loop)
            self.play_thread.daemon = True
            self.play_thread.start()
            self._progress_listener.start()

        self.state = PlayerState.PLAYING

    def play_sync(self, position: float, command_time):
        self.seek_sync(position, command_time)
        self.play()

    def pause(self):
        """暂停播放"""
        if self.state == PlayerState.PLAYING:
            self._pause_event.set()  # 设置暂停标志
            self.state = PlayerState.PAUSED
            self._progress_listener.stop()

    def pause_sync(self, position, command_time):
        self.pause()
        self.seek_sync(position, command_time)

    def stop(self):
        """停止播放"""
        if self.state != PlayerState.STOPPED:
            self._stop_event.set()
            self._pause_event.set()  # 确保暂停的线程也能退出
            if self.play_thread and self.play_thread.is_alive():
                self.play_thread.join(timeout=1.0)

            self.state = PlayerState.STOPPED
            self._set_current_time(0.0)
            self._progress_listener.stop()

    def seek(self, position: float):
        """跳转到指定位置（秒）"""
        if position < 0:
            position = 0
        if position > self.total_time:
            position = self.total_time

        self._seek_position = position
        self._seek_event.set()

        # 如果当前是暂停状态，也需要更新当前时间
        if self.state == PlayerState.PAUSED:
            self._set_current_time(position)

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
