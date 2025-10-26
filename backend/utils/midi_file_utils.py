import os
from typing import List, Dict, Any, Optional
import chardet
import uuid

from mido import MidiFile

from backend.midi import KeyboardMapper
from backend.utils.config_utils import ConfigField
from backend.utils.logger import get_logger
from backend.utils.yaml_config_manager import cm


def ensure_path_exists(path: str) -> bool:
    """
    按照路径识别文件或文件夹，确保其父目录存在

    Args:
        path: 文件或文件夹路径

    Returns:
        bool: 操作是否成功
    """
    try:
        # 判断路径是文件还是文件夹
        if os.path.splitext(path)[1]:  # 有扩展名，认为是文件
            # 获取文件的父目录
            parent_dir = os.path.dirname(path)
            # 确保父目录存在
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
        else:  # 没有扩展名，认为是文件夹
            # 确保文件夹存在
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

        return True
    except Exception as e:
        print(f"创建路径失败: {e}")
        return False


def list_current_directory_midis():
    """
    基本方法遍历当前目录
    """
    midi_path = cm.get(ConfigField.MIDI_PATH)
    ensure_path_exists(midi_path)
    items = os.listdir(midi_path)  # '.' 表示当前目录
    index = 0
    result = []
    for item in items:
        target_file = handle_file(midi_path + "/" + item, index)
        if target_file is not None:
            result.append(target_file)
            index += 1
    return result


def handle_file(file_path, index):
    """
    处理文件
    """
    if file_path.endswith('.mid'):
        return {
            "index": index,
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "is_file": True
        }


def get_track_summaries(tracks, only_has_notes=True) -> List[Dict[str, Any]]:
    """
    获取 MIDI 文件中每个音轨的摘要信息

    :param only_has_notes: 是否只包含有音符的音轨
    :param file_path: MIDI 文件路径
    :return: 音轨摘要信息列表
    """
    tracks_summary = []

    tracks = enumerate(tracks)
    name_strs = []
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
        current_name = ''
        # 分析音轨内容
        for msg in track:
            if msg.type == 'track_name':
                current_name = msg.name
                summary['name'] = msg.name
            elif msg.type == 'note_on' and msg.velocity > 0:
                summary['has_notes'] = True
            elif msg.type == 'program_change':
                summary['instrument'] = msg.program
            elif hasattr(msg, 'channel'):
                summary['channels'].add(msg.channel)
        summary['channels'] = list(summary['channels'])
        name_strs.append(current_name)
        tracks_summary.append(summary)
    name_charset = detect_text_encoding(''.join(name_strs).encode('latin-1'), 'latin-1')
    result = []
    for i, summary in enumerate(tracks_summary):
        summary['name'] = name_strs[i].encode('latin-1').decode(name_charset)
        if not only_has_notes or summary['has_notes']:
            result.append(summary)
    return result


def extract_notes_from_track(midi_file: MidiFile, track_index: Optional[int] = None,
                             track_name: Optional[str] = None) -> List[int]:
    """
    解析MIDI文件中指定音轨的所有音符，返回音符编号数组

    Args:
        midi_file_path: MIDI文件路径
        track_index: 音轨索引（从0开始），与track_name二选一
        track_name: 音轨名称，与track_index二选一

    Returns:
        音符编号列表，每个元素为0-127之间的整数
    """

    # 确定要解析的音轨
    if track_index is not None:
        if track_index >= len(midi_file.tracks):
            raise ValueError(f"Track index {track_index} out of range. File has {len(midi_file.tracks)} tracks.")
        track = midi_file.tracks[track_index]
    elif track_name is not None:
        track = None
        for t in midi_file.tracks:
            # 查找音轨名称事件
            for msg in t:
                if msg.type == 'track_name' and msg.name == track_name:
                    track = t
                    break
            if track:
                break
        if track is None:
            raise ValueError(f"Track with name '{track_name}' not found.")
    else:
        raise ValueError("Either track_index or track_name must be specified.")

    # 存储音符
    notes = []

    # 遍历音轨中的所有消息
    for msg in track:
        # 检查是否为音符开始消息
        if msg.type == 'note_on' and msg.velocity > 0:
            # 添加音符编号到列表
            notes.append(msg.note)

    return sorted(list(set(notes)))


def get_tempos(tracks):
    tempo_times = []
    current_tick = 0  # 当前tick计数
    for track in tracks:
        for msg in track:
            current_tick += msg.time  # 累计ticks
            if msg.type == 'set_tempo':
                tempo_times.append((current_tick, msg.tempo))
    tempo_times.sort(key=lambda x: x[0])
    return tempo_times


def detect_text_encoding(text_bytes, default_encoding='utf-8', min_confidence=0.7):
    """
    检测文本字节的编码
    """
    if not text_bytes:
        return default_encoding
    # 使用chardet检测
    result = chardet.detect(text_bytes)
    if result['confidence'] > min_confidence:
        return result['encoding']
    # 尝试常见编码
    encodings = ['gbk', 'utf-8', 'latin-1', 'cp1252', 'shift_jis', 'big5']

    for encoding in encodings:
        try:
            text_bytes.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return default_encoding  # 默认回退


def extract_midi_messages(midi_file: MidiFile):
    ticks_per_beat = midi_file.ticks_per_beat
    result = []

    tracks = enumerate(midi_file.tracks)
    tempos = get_tempos(midi_file.tracks)
    for i, track in tracks:
        current_tick = 0  # 当前tick计数
        current_tempo_index = 0
        current_tempo = 5000000
        uuid_map = {}
        for msg in track:
            while current_tempo_index < len(tempos) and current_tick >= tempos[current_tempo_index][0]:
                current_tempo = tempos[current_tempo_index][1]
                current_tempo_index += 1
            current_tick += msg.time  # 累计ticks
            if not msg.is_meta:
                # 将ticks转换为秒 公式: (ticks / ticks_per_beat) * (tempo / 1,000,000)
                current_time_seconds = (current_tick / ticks_per_beat) * (current_tempo / 1000000.0)
                json_msg = msg.__dict__
                # 非严格场景下响度为0的note_on为note_off
                if json_msg['type'] == 'note_on':
                    if json_msg['velocity'] <= 0:
                        json_msg['type'] = 'note_off'
                if json_msg['type'] == 'note_on':
                    current_uuid = str(uuid.uuid4())
                    json_msg['uuid'] = current_uuid
                    uuid_map[json_msg['note']] = current_uuid
                elif json_msg['type'] == 'note_off':
                    msg_note = json_msg['note']
                    if msg_note in uuid_map:
                        json_msg['uuid'] = uuid_map[msg_note]
                        del uuid_map[msg_note]
                    else:
                        json_msg['uuid'] = str(uuid.uuid4())
                json_msg['track'] = i
                result.append([current_time_seconds, json_msg])
    result.sort(key=lambda x: x[0])
    return result


def mapping_notes(keyboard_mapper: KeyboardMapper, messages: List[any], min_spacing=0.05):
    """将音符映射为按键"""
    new_messages = messages.copy()
    for message_pair in new_messages:
        message: dict = message_pair[1]
        if 'note' in message:
            message.update({'key': keyboard_mapper.map_note(message.get('note'))})
    eliminate_crossing(new_messages, min_spacing)
    eliminate_nearing(new_messages, min_spacing)
    return new_messages


def eliminate_crossing(messages: List[any], min_spacing=0.05):
    for i in range(len(messages)):
        msg_pair = messages[i]
        message = msg_pair[1]
        msg_type = message['type']
        if msg_type == 'note_on':
            msg_key = message['key']
            msg_uuid = message['uuid']
            # 开始判断是否有按键交叉
            j = i + 1
            crossing_msg = None
            off_msg = None
            while crossing_msg is None and off_msg is None:
                cur_msg_pair = messages[j]
                cur_msg = cur_msg_pair[1]
                cur_msg_type = cur_msg['type']
                if cur_msg_type == 'note_off':
                    if cur_msg['uuid'] == msg_uuid:
                        off_msg = cur_msg_pair
                        break
                elif cur_msg_type == 'note_on' and crossing_msg is None:
                    if msg_key == cur_msg['key']:
                        crossing_msg = cur_msg_pair
                j += 1
            # 将抬起事件的时间尽量提前到交叉音符之前
            if crossing_msg is not None and off_msg is not None:
                set_key_to_before(msg_pair, off_msg, crossing_msg, min_spacing)
    messages.sort(key=lambda x: x[0])


def eliminate_nearing(messages: List[any], min_spacing=0.05):
    for i in range(len(messages)):
        msg_pair = messages[i]
        message = msg_pair[1]
        msg_type = message['type']
        if msg_type == 'note_on':
            msg_key = message['key']
            msg_uuid = message['uuid']
            # 开始判断是否有按键交叉
            j = i + 1
            nearing_msg = None
            off_msg = None
            while j < len(messages):
                cur_msg_pair = messages[j]
                cur_msg = cur_msg_pair[1]
                cur_msg_type = cur_msg['type']
                if cur_msg_type == 'note_off':
                    if cur_msg['uuid'] == msg_uuid:
                        off_msg = cur_msg_pair
                elif off_msg is not None and cur_msg_type == 'note_on':
                    if off_msg[0] == cur_msg_pair[0]:
                        if msg_key == cur_msg['key']:
                            nearing_msg = cur_msg_pair
                    else:
                        break
                j += 1
                # 将抬起事件的时间尽量提前到临近音符之前
            if nearing_msg is not None and off_msg is not None:
                set_key_to_before(msg_pair, off_msg, nearing_msg, min_spacing)
    messages.sort(key=lambda x: x[0])


def set_key_to_before(cur_msg: any, off_msg: any, next_msg: any, min_spacing=0.05):
    cur_msg_time = cur_msg[0]
    off_msg_old_time = off_msg[0]
    get_logger().warn(f'消除一处按键黏连，位于{off_msg_old_time}处。')
    nearing_msg_time = next_msg[0]
    off_msg_new_time = nearing_msg_time - min_spacing
    if off_msg_new_time > cur_msg_time:
        off_msg[0] = off_msg_new_time
    else:
        off_msg[0] = (cur_msg_time - off_msg_old_time) / 2 + off_msg_old_time
