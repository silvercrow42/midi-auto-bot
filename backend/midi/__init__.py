from typing import Union, List

from backend.api.event_bus_api import event_bus
from backend.midi.event.midi_events import NoteOnEvent, NoteOffEvent
from backend.midi.mapper.deep_key_mapper import KeyboardMapper
from backend.midi.player.basic_midi_player import BasicMidiPlayer
from backend.sqllite.key_config_sqls import query_first_key_config, KeyConfigEntity
from backend.utils.window_controller import WindowController

# 初始化窗口控制器，用于操作游戏窗口
window_controller = WindowController()

# 初始化midi文件播放器
midi_player = BasicMidiPlayer(window_controller)
midi_player.set_mapper(query_first_key_config())


def note_on_handler(event: NoteOnEvent):
    cur_msg = event.message
    if cur_msg['key'] is None:
        return
    window_controller.press(cur_msg['key'], keyupdown=2)


def note_off_handler(event: NoteOffEvent):
    cur_msg = event.message
    if cur_msg['key'] is None:
        return
    window_controller.press(cur_msg['key'], keyupdown=1)


midi_player.register_event_handler('note_on', note_on_handler)
midi_player.register_event_handler('note_off', note_off_handler)


def convert_to_number(value: Union[str, int, float]) -> Union[str, int, float]:
    """
    如果是str则转化为数字，如果是数字则不变

    Args:
        value: 输入值，可以是字符串或数字

    Returns:
        转换后的值
    """
    # 如果已经是数字类型，直接返回
    if isinstance(value, (int, float)):
        return value

    # 如果是字符串，尝试转换
    if isinstance(value, str):
        try:
            # 判断是否为整数格式
            if '.' not in value and 'e' not in value.lower():
                # 检查是否为有效的整数格式
                int(value)  # 先测试是否能转换
                return int(value)
            else:
                return float(value)
        except ValueError:
            # 转换失败，返回原字符串
            return value

    # 其他类型直接返回
    return value


def set_programs(target_tracks: List[int]):
    summaries = midi_player.get_track_summaries()
    track_indexes = set()
    for summary in summaries:
        track_indexes.add(summary['track_index'])
    for target_track_num in target_tracks:
        if target_track_num not in track_indexes:
            raise ValueError("音轨不存在")
    midi_player.set_programs(target_tracks)
    event_bus.set_programs(target_tracks)
