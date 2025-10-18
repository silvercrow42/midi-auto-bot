from typing import Union, List

from api import event_bus
from midi.event.midi_events import NoteOnEvent, NoteOffEvent
from midi.mapper.deep_key_mapper import KeyboardMapper
from midi.player.basic_midi_player import BasicMidiPlayer
from sqllite.key_config_sqls import query_first_key_config, KeyConfigEntity
from utils.logger import get_logger
from utils.window_controller import WindowController


def set_mapper(config_entity: KeyConfigEntity):
    if config_entity is None:
        raise Exception("请选择按键映射")
    global mapper, mapper_config
    mapper_config = config_entity
    new_mapper = KeyboardMapper.from_json(mapper_config.config_json)
    new_mapper.apply_strategies()
    mapper = new_mapper
    window_controller.clear()


# 初始化窗口控制器，用于操作游戏窗口
window_controller = WindowController()

# 创建映射器
mapper_config: KeyConfigEntity | None = None
mapper: KeyboardMapper | None = None

set_mapper(query_first_key_config())

# 初始化midi文件播放器
midi_player = BasicMidiPlayer(window_controller)

off_mode = True


def note_on_handler(event: NoteOnEvent):
    note = event.message['note']
    get_logger().debug(f"Note On: note={note}, time={event.timestamp:.2f}s")
    if mapper is None:
        raise Exception("请先初始化按键映射")
    key = mapper.map_note(note)
    if key is not None:
        window_controller.press(key, keyupdown=2)


def note_off_handler(event: NoteOffEvent):
    note = event.message['note']
    get_logger().debug(f"Note Off: note={note}, time={event.timestamp:.2f}s")
    if mapper is None:
        raise Exception("请先初始化按键映射")
    key = mapper.map_note(note)
    if key is not None:
        window_controller.press(key, keyupdown=1)


midi_player.register_event_handler('note_on', note_on_handler)
midi_player.register_event_handler('note_off', note_off_handler)


def get_mapper():
    return mapper


def get_mapper_name():
    if mapper_config is None:
        raise Exception("请先初始化按键映射")
    return mapper_config.name


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
