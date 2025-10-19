class MidiEvent:
    """MIDI事件基类"""

    def __init__(self, timestamp: float, message: dict):
        self.timestamp = timestamp  # 事件发生的时间戳（秒）
        self.message = message  # MIDI消息对象


class NoteOnEvent(MidiEvent):
    """
    Note On（按下键）事件\n
    场景：当需要发出一个音符时\n
    作用：\n
    1. 触发音符开始发声\n
    2. 控制音符的力度（音量）\n
    事件信息示例 \n
    Note On: note = 60, velocity = 100, time = 1.23s\n
    这表示在1.23秒时，以100的力度按下中央C（MIDI音符编号60）\n
    实际应用：\n
    1. 钢琴：琴键被按下\n
    2. 吉他：拨动琴弦\n
    3. 鼓组：敲击鼓面\n
    """
    pass


class IgnoreNoteOnEvent(MidiEvent):
    """
    Note On（按下键）事件\n
    场景：当需要发出一个音符时\n
    作用：\n
    1. 触发音符开始发声\n
    2. 控制音符的力度（音量）\n
    事件信息示例 \n
    Note On: note = 60, velocity = 100, time = 1.23s\n
    这表示在1.23秒时，以100的力度按下中央C（MIDI音符编号60）\n
    实际应用：\n
    1. 钢琴：琴键被按下\n
    2. 吉他：拨动琴弦\n
    3. 鼓组：敲击鼓面\n
    """
    pass


class NoteOffEvent(MidiEvent):
    """
    Note Off（抬起键）事件\n
    场景：当需要停止一个音符时\n
    作用：\n
    1. 结束音符的发声\n
    2. 有些合成器也支持释放力度控制\n
    事件信息示例\n
    Note Off: note=60, time=2.45s\n
    这表示在2.45秒时，释放中央C键\n
    实际应用：\n
    1. 钢琴：琴键被释放\n
    2. 吉他：停止琴弦振动\n
    3. 控制音符的持续时间\n
    """
    pass


class IgnoreNoteOffEvent(MidiEvent):
    """
    Note On（按下键）事件\n
    场景：当需要发出一个音符时\n
    作用：\n
    1. 触发音符开始发声\n
    2. 控制音符的力度（音量）\n
    事件信息示例 \n
    Note On: note = 60, velocity = 100, time = 1.23s\n
    这表示在1.23秒时，以100的力度按下中央C（MIDI音符编号60）\n
    实际应用：\n
    1. 钢琴：琴键被按下\n
    2. 吉他：拨动琴弦\n
    3. 鼓组：敲击鼓面\n
    """
    pass


class ControlChangeEvent(MidiEvent):
    """
    Control Change（控制变更）事件\n
    场景：需要实时调整音色参数时\n
    作用：\n
    1. 调节音量、声像、表情等\n
    2. 控制效果器参数\n
    3. 调制音色特性
    事件信息示例\n
    Control Change: control=7, value=100, time=3.12s\n
    这表示在3.12秒时，将主音量设置为100\n
    常见控制编号：\n
    1:Modulation(颤音深度)\n
    7:Volume(主音量)\n
    10:Pan(声像定位)\n
    11:Expression(表情控制)\n
    64:Sustain(延音踏板)\n
    91:Reverb(混响效果)\n
    """
    pass


class ProgramChangeEvent(MidiEvent):
    """
    Program Change（程序变更）事件\n
    场景：需要切换乐器音色时\n
    作用：\n
    1. 改变当前通道的乐器\n
    2. 选择不同的音色库\n
    事件信息示例\n
    Program Change: program=1, time=0.5s\n
    这表示在0.5秒时，切换到1号音色（通常是钢琴）\n
    实际应用：\n
    1. 歌曲中不同段落使用不同乐器\n
    2. 实时音色切换\n
    3. GM标准音色表选择\n
    编码对照表可见：https://midiprog.com/program-numbers/
    """
    pass


class PitchWheelEvent(MidiEvent):
    """
    Pitch Wheel（弯音轮）事件\n
    场景：需要制造滑音效果时\n
    作用：\n
    1. 实时改变音高\n
    2. 创造滑音、颤音效果\n
    事件信息示例\n
    Pitch Wheel: pitch=8192, time=4.56s\n
    这表示在4.56秒时，将弯音轮设置到中间位置（无弯音）\n
    实际应用：\n
    1. 吉他推弦效果\n
    2. 小提琴滑音\n
    3. 电子音乐的特殊效果\n
    """
    pass
