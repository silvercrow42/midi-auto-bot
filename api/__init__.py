from api.event_bus_api import event_bus
from midi.event.midi_events import NoteOnEvent, NoteOffEvent
from midi.player.basic_midi_player import BasicMidiPlayer
from midi.mapper.deep_key_mapper import KeyboardMapper
from utils.window_controller import WindowController

# 初始化窗口控制器，用于操作游戏窗口
window_controller = WindowController()
# 初始化midi文件播放器
midi_player = BasicMidiPlayer()
key_layouts = [
    {
        "name": "小提琴21",
        "keys": ["z", "x", "c", "v", "b", "n", "m", "a", "s", "d", "f",
                 "g", "h", "j", "q", "w", "e", "r", "t", "y", "u"]
    }
]
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
playing_channel = 0
mapper.apply_strategies()

def set_channel(channel):
    global playing_channel
    summaries = midi_player.get_track_summaries()
    channels = set()
    for summary in summaries:
        channels.update(summary['channels'])
    if channel in channels:
        playing_channel = channel
        return
    raise ValueError("音轨不存在")


def note_on_handler(event: NoteOnEvent):
    if event.message.channel == playing_channel:
        # todo 实现全局控制日志打印
        print(f"Note On: note={event.message.note}, time={event.timestamp:.2f}s")
        if mapper is None:
            raise Exception("请先初始化按键映射")
        # note = event.message.note
        key = mapper.map_note(event.message.note)
        if key is not None:
            print(f"映射到按键: {key}")
            event_bus.midi_note_on(key)
            window_controller.keydown(key)


def note_off_handler(event: NoteOffEvent):
    if event.message.channel == playing_channel:
        print(f"Note Off: note={event.message.note}, time={event.timestamp:.2f}s")
        if mapper is None:
            raise Exception("请先初始化按键映射")
        key = mapper.map_note(event.message.note)
        if key is not None:
            event_bus.midi_note_off(key)
            window_controller.keyup(key)


midi_player.register_event_handler('note_on', note_on_handler)
midi_player.register_event_handler('note_off', note_off_handler)
