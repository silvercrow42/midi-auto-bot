import bisect
import copy
import json
from enum import Enum
from functools import wraps
from typing import List, Dict, Optional

from utils.array_utils import expand_array, shift_array


class NoteStrategy(Enum):
    """音符映射策略"""
    NO_MAPPING = "no_mapping"  # 不映射
    NEAREST = "nearest"  # 取最近的key
    UPWARD = "upward"  # 向上取最近的key
    DOWNWARD = "downward"  # 向下取最近的key


class KeyMapping:
    """单个键的映射配置"""

    def __init__(self, key: str = None, sharp_strategy: bool = True,
                 normal_strategy: NoteStrategy = NoteStrategy.NO_MAPPING):
        self.key = key  # 映射的键盘按键
        self.sharp_strategy = sharp_strategy  # 是否启用升降音调策略
        self.normal_strategy = normal_strategy  # 普通策略

    def to_dict(self) -> Dict:
        """转换为字典用于序列化"""
        return {
            'key': self.key,
            'sharp_strategy': self.sharp_strategy,
            'normal_strategy': self.normal_strategy.value
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'KeyMapping':
        """从字典创建对象"""
        return cls(
            key=data.get('key'),
            sharp_strategy=data.get('sharp_strategy', True),
            normal_strategy=NoteStrategy(data.get('normal_strategy', NoteStrategy.NO_MAPPING.value))
        )


def mapping_matrix_to_json(mapping_matrix: List[List[KeyMapping]]):
    return [
        [mapping.to_dict() for mapping in octave]
        for octave in mapping_matrix
    ]


def refresh_remapping_matrix(func):
    """
    触发音阶映射的装饰器
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # 增加调用层级计数
        if not hasattr(self, '_refresh_counter'):
            self._refresh_counter = 0

        self._refresh_counter += 1
        try:
            result = func(self, *args, **kwargs)
            # 只在最外层调用时刷新
            if self._refresh_counter == 1:
                self.apply_strategies()
            return result
        finally:
            # 减少计数器
            self._refresh_counter -= 1

    return wrapper


def _find_nearest_key_in_octave(octave_mappings: [KeyMapping], note: int, strategy: NoteStrategy) -> Optional[
    KeyMapping]:
    """在当前音阶内按照策略寻找最近的按键"""
    if strategy == NoteStrategy.NO_MAPPING:
        return None

    available_notes = [i for i, mapping in enumerate(octave_mappings) if mapping.key is not None]

    if not available_notes:
        return None

    if strategy == NoteStrategy.NEAREST:
        # 找到最接近的音符
        pos = bisect.bisect_left(available_notes, note)
        if pos == 0:
            return octave_mappings[available_notes[0]]
        elif pos == len(available_notes):
            return octave_mappings[available_notes[-1]]
        else:
            before = available_notes[pos - 1]
            after = available_notes[pos]
            if note - before <= after - note:
                return octave_mappings[before]
            else:
                return octave_mappings[after]

    elif strategy == NoteStrategy.UPWARD:
        # 向上寻找
        pos = bisect.bisect_left(available_notes, note)
        if pos < len(available_notes):
            return octave_mappings[available_notes[pos]]

    elif strategy == NoteStrategy.DOWNWARD:
        # 向下寻找
        pos = bisect.bisect_right(available_notes, note) - 1
        if pos >= 0:
            return octave_mappings[available_notes[pos]]

    return None


def _apply_expansion(target_map, base_octave, ratio):
    """应用扩展策略"""
    # 扩展数组
    expanded = expand_array(target_map, base_octave, ratio)

    # 根据规则截取
    # 基准元素新位置
    original_length = len(target_map)
    new_base_pos = base_octave * ratio  # 原索引i元素在新数组中的最后位置

    # 截取范围：保留原来的前后元素数量
    start = new_base_pos - base_octave
    end = start + original_length

    # 返回截取结果
    return (expanded[start:end] + target_map)[:original_length]


def _apply_shift(current_map, shift):
    """应用升降调策略"""
    return shift_array(current_map, shift, lambda: [KeyMapping() for _ in range(12)])


class KeyboardMapper:
    """键盘映射器"""

    def __init__(self, mapping_matrix: List[List[KeyMapping]] = None):
        """
        初始化映射器

        Args:
            mapping_matrix: 二维映射矩阵，每行代表一个音阶，每列代表一个半音
        """
        target_array = []
        # 初始化128个音符
        if mapping_matrix is not None:
            target_array = copy.deepcopy(mapping_matrix)
        for current_note in range(0, 127):
            target_octave = current_note // 12
            target_semitone = current_note % 12
            if len(target_array) <= target_octave:
                target_array.append([])
            if target_array[target_octave] is None:
                target_array[target_octave] = []
            if len(target_array[target_octave]) <= target_semitone:
                target_array[target_octave].append(KeyMapping())
            if target_array[target_octave][target_semitone] is None:
                target_array[target_octave][target_semitone] = KeyMapping()
        self.mapping_matrix = target_array

        # 音域处理配置
        self.transpose_octaves = 0  # 升降调音阶数
        self.expand_base_octave = None  # 压缩基准音阶
        self.expand_ratio = 1  # 压缩倍率

        # 全局策略配置
        self.global_sharp_strategy = True  # 全局升降音调策略
        self.global_normal_strategy = NoteStrategy.NO_MAPPING  # 全局普通策略

        self.remapping_matrix = None

    def set_mapping_matrix(self, matrix: List[List[dict]]):
        self.mapping_matrix = [
            [KeyMapping.from_dict(mapping) for mapping in octave]
            for octave in matrix
        ]

    def set_mapping(self, octave: int, note: int, key_str: str, key_mapping: KeyMapping = None):
        """设置单个音符的映射"""
        if 0 <= octave < len(self.mapping_matrix) and 0 <= note < 12:
            if key_mapping is None:
                key_mapping = KeyMapping(key=key_str)
            self.mapping_matrix[octave][note] = key_mapping

    def get_mapping(self, octave: int, note: int) -> KeyMapping:
        """获取单个音符的映射"""
        if 0 <= octave < len(self.mapping_matrix) and 0 <= note < 12:
            return self.mapping_matrix[octave][note]
        return KeyMapping()

    @refresh_remapping_matrix
    def set_transpose(self, octaves: int):
        """设置升降调"""
        self.transpose_octaves = octaves

    @refresh_remapping_matrix
    def set_expand(self, base_octave: int, ratio: int):
        """设置压缩配置"""
        self.expand_base_octave = base_octave
        self.expand_ratio = ratio

    def map_note(self, midi_note: int) -> Optional[str]:
        """
        将MIDI音符映射到键盘按键

        Args:
            midi_note: MIDI音符编号（0-127）

        Returns:
            映射的键盘按键，如果无法映射返回None
        """
        if midi_note < 0 or midi_note > 127:
            return None

        final_octave = midi_note // 12
        final_note = midi_note % 12

        # 检查音阶范围
        if final_octave >= len(self.remapping_matrix):
            return None
        octave_mappings = self.remapping_matrix[final_octave]
        # 获取映射配置
        mapping = octave_mappings[final_note]

        # 3. 检查是否有直接映射
        if mapping.key is not None:
            return mapping.key

        # 4. 应用升降音调策略（如果启用）
        if (self.global_sharp_strategy and mapping.sharp_strategy and
                final_note not in [0, 2, 4, 5, 7, 9, 11]):  # 非自然音（升降音）
            # 尝试映射到自然音
            natural_note = final_note - 1 if final_note % 12 in [1, 3, 6, 8, 10] else final_note + 1
            natural_note = max(0, min(11, natural_note))

            natural_mapping = octave_mappings[natural_note]
            if natural_mapping.key is not None:
                return natural_mapping.key

        # 5. 应用普通策略
        strategy = mapping.normal_strategy if mapping.normal_strategy != NoteStrategy.NO_MAPPING else self.global_normal_strategy
        nearest_mapping = _find_nearest_key_in_octave(octave_mappings, final_note, strategy)

        return nearest_mapping.key if nearest_mapping else None

    def auto_configure(self, midi_notes: List[int]):
        """
        智能配置映射参数，使配置的键盘按键覆盖乐曲中出现的音符

        Args:
            midi_notes: 乐曲中出现的MIDI音符列表
        """
        if not midi_notes:
            return

        # 获取所有已配置按键的音符
        configured_notes = []
        for octave in range(len(self.mapping_matrix)):
            current_note_group = self.mapping_matrix[octave]
            for note in range(len(current_note_group)):
                if current_note_group[note].key is not None:
                    configured_notes.append(octave * 12 + note)

        if not configured_notes:
            # 如果没有配置任何按键，无法自动配置
            return

        configured_notes.sort()
        midi_notes_sorted = sorted(set(midi_notes))

        # 计算音符范围
        min_note = min(midi_notes_sorted)
        max_note = max(midi_notes_sorted)
        note_range = max_note - min_note

        # 计算已配置按键的音符范围
        min_configured = min(configured_notes)
        max_configured = max(configured_notes)
        configured_range = max_configured - min_configured

        # 策略1：优先尝试压缩
        if configured_range > 0 and note_range > configured_range:
            # 需要压缩
            expand_ratio = max(1, (note_range + configured_range - 1) // configured_range)
            # 以中间音阶为基准进行压缩
            base_octave = (min_note + max_note) // 2 // 12

            self.set_expand(base_octave, expand_ratio)
        else:
            # 策略2：只需要升降调
            self.set_expand(None, 1)  # 关闭压缩
        # 调整升降调使范围居中
        center_note = (min_note + max_note) // 2
        center_configured = (min_configured + max_configured) // 2
        transpose_octaves = (center_note - center_configured) // 12
        self.set_transpose(transpose_octaves)

    def to_json(self) -> str:
        """序列化为JSON字符串"""
        config = {
            'mapping_matrix': [
                [mapping.to_dict() for mapping in octave]
                for octave in self.mapping_matrix
            ],
            'transpose_octaves': self.transpose_octaves,
            'expand_base_octave': self.expand_base_octave,
            'expand_ratio': self.expand_ratio,
            'global_sharp_strategy': self.global_sharp_strategy,
            'global_normal_strategy': self.global_normal_strategy.value
        }
        return json.dumps(config, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'KeyboardMapper':
        """从JSON字符串创建映射器"""
        config = json.loads(json_str)

        mapping_matrix = [
            [KeyMapping.from_dict(mapping_dict) for mapping_dict in octave]
            for octave in config['mapping_matrix']
        ]
        mapper = cls(mapping_matrix)
        mapper.transpose_octaves = config['transpose_octaves']
        mapper.expand_base_octave = config['expand_base_octave']
        mapper.expand_ratio = config['expand_ratio']
        mapper.global_sharp_strategy = config['global_sharp_strategy']
        mapper.global_normal_strategy = NoteStrategy(config['global_normal_strategy'])
        return mapper

    def apply_strategies(self):
        """
        应用音域策略

        Returns:
            新的二维对象数组
        """
        # 第二步：应用升降调策略
        if self.transpose_octaves != 0:
            final_map = _apply_shift(self.mapping_matrix, self.transpose_octaves)
        else:
            final_map = self._copy_map(self.mapping_matrix)

        # 第一步：应用扩展策略
        if self.expand_base_octave is not None and self.expand_ratio > 0:
            final_map = _apply_expansion(final_map, self.expand_base_octave, self.expand_ratio)

        self.remapping_matrix = final_map
        return final_map

    @staticmethod
    def _copy_map(source_map):
        """深拷贝映射数组（但保持对象引用）"""
        new_map = []
        for octave_notes in source_map:
            new_octave = []
            for note_mapping in octave_notes:
                # 保持对象引用，不创建新对象
                new_octave.append(note_mapping)
            new_map.append(new_octave)
        return new_map


# 使用示例
if __name__ == "__main__":

    # 创建映射器
    mapper = KeyboardMapper()

    # 配置基础映射（示例：C大调音阶映射到键盘第一行）
    mapper.set_mapping(0, 0, key_str='z')  # C0 -> q
    mapper.set_mapping(0, 2, key_str='x')  # D0 -> w
    mapper.set_mapping(0, 4, key_str='c')  # E0 -> e
    mapper.set_mapping(0, 5, key_str='v')  # E0 -> e
    mapper.set_mapping(0, 7, key_str='b')  # E0 -> e
    mapper.set_mapping(0, 9, key_str='n')  # E0 -> e
    mapper.set_mapping(0, 11, key_str='m')  # E0 -> e

    mapper.set_mapping(1, 0, key_str='a')  # C0 -> q
    mapper.set_mapping(1, 2, key_str='s')  # D0 -> w
    mapper.set_mapping(1, 4, key_str='d')  # E0 -> e
    mapper.set_mapping(1, 5, key_str='f')  # E0 -> e
    mapper.set_mapping(1, 7, key_str='g')  # E1 -> e
    mapper.set_mapping(1, 9, key_str='h')  # E1 -> e
    mapper.set_mapping(1, 11, key_str='j')  # E1 -> e

    mapper.set_mapping(2, 0, key_str='q')  # C0 -> q
    mapper.set_mapping(2, 2, key_str='w')  # D0 -> w
    mapper.set_mapping(2, 4, key_str='e')  # E0 -> e
    mapper.set_mapping(2, 5, key_str='r')  # E0 -> e
    mapper.set_mapping(2, 7, key_str='t')  # E2 -> e
    mapper.set_mapping(2, 9, key_str='y')  # E2 -> e
    mapper.set_mapping(2, 11, key_str='u')  # E2 -> e

    # 测试映射
    test_notes = [60, 62, 64, 65, 67, 69, 71]  # 中央C附近的C大调音阶
    for note in test_notes:
        key = mapper.map_note(note)
        print(f"MIDI音符 {note} -> 键盘按键 {key}")

    # 自动配置
    song_notes = [58, 59, 61, 63, 64, 66, 67, 68, 70, 71, 73, 75, 76, 78, 79, 80, 82, 83, 84, 85, 87, 88, 90, 92, 94,
                  95, 97, 99]
    mapper.auto_configure(song_notes)
    print(
        f"\n自动配置后：升降调={mapper.transpose_octaves}, 压缩基准={mapper.expand_base_octave}, 压缩倍率={mapper.expand_ratio}")

    new_map = mapper.apply_strategies()
    print(mapper.map_note(60))
    print(mapper.map_note(61))
    print(mapper.map_note(62))
    print(mapper.map_note(63))
    print(mapper.map_note(64))

    # 序列化测试
    json_str = mapper.to_json()
    print(f"\n序列化结果长度: {len(json_str)} 字符")

    # 反序列化
    new_mapper = KeyboardMapper.from_json(json_str)
    print("反序列化成功!")
