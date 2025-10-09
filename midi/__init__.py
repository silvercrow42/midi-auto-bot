from api import event_bus
from midi.mapper.deep_key_mapper import KeyboardMapper
from midi.player.basic_midi_player import BasicMidiPlayer
from midi.event.midi_events import NoteOnEvent, NoteOffEvent
from utils.logger import get_logger
from utils.window_controller import WindowController

# 创建映射器
mapper = KeyboardMapper()
# 配置基础映射（示例：C大调音阶映射到键盘第一行）
mapper.set_mapping(5, 0, key_str='z')  # C0 -> q
mapper.set_mapping(5, 2, key_str='x')  # D0 -> w
mapper.set_mapping(5, 4, key_str='c')  # E0 -> e
mapper.set_mapping(5, 5, key_str='v')  # E0 -> e
mapper.set_mapping(5, 7, key_str='b')  # E0 -> e
mapper.set_mapping(5, 9, key_str='n')  # E0 -> e
mapper.set_mapping(5, 11, key_str='m')  # E0 -> e

mapper.set_mapping(6, 0, key_str='a')  # C0 -> q
mapper.set_mapping(6, 2, key_str='s')  # D0 -> w
mapper.set_mapping(6, 4, key_str='d')  # E0 -> e
mapper.set_mapping(6, 5, key_str='f')  # E0 -> e
mapper.set_mapping(6, 7, key_str='g')  # E1 -> e
mapper.set_mapping(6, 9, key_str='h')  # E1 -> e
mapper.set_mapping(6, 11, key_str='j')  # E1 -> e

mapper.set_mapping(7, 0, key_str='q')  # C0 -> q
mapper.set_mapping(7, 2, key_str='w')  # D0 -> w
mapper.set_mapping(7, 4, key_str='e')  # E0 -> e
mapper.set_mapping(7, 5, key_str='r')  # E0 -> e
mapper.set_mapping(7, 7, key_str='t')  # E2 -> e
mapper.set_mapping(7, 9, key_str='y')  # E2 -> e
mapper.set_mapping(7, 11, key_str='u')  # E2 -> e
mapper.apply_strategies()

# 初始化midi文件播放器
midi_player = BasicMidiPlayer()

# 初始化窗口控制器，用于操作游戏窗口
window_controller = WindowController()
off_mode = False


def note_on_handler(event: NoteOnEvent):
    get_logger().debug(f"Note On: note={event.message.note}, time={event.timestamp:.2f}s")
    if mapper is None:
        raise Exception("请先初始化按键映射")
    key = mapper.map_note(event.message.note)
    if key is not None:
        if off_mode:
            window_controller.press(key, keyupdown=2)
        else:
            window_controller.press(key)


def note_off_handler(event: NoteOffEvent):
    get_logger().debug(f"Note Off: note={event.message.note}, time={event.timestamp:.2f}s")
    if mapper is None:
        raise Exception("请先初始化按键映射")
    key = mapper.map_note(event.message.note)
    if key is not None:
        window_controller.press(key, keyupdown=1)


midi_player.register_event_handler('note_on', note_on_handler)
midi_player.register_event_handler('note_off', note_off_handler)


def set_mapper(new_mapper: KeyboardMapper):
    global mapper
    mapper = new_mapper


from typing import Union


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


def set_channel(channel):
    summaries = midi_player.get_track_summaries()
    channels = set()
    for summary in summaries:
        channels.update(summary['channels'])
    channel_num = convert_to_number(channel)
    if channel_num in channels:
        midi_player.set_channels([channel_num])
        event_bus.set_channel(channel_num)
        return
    raise ValueError("音轨不存在")
