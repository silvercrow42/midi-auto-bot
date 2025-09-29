def map_notes_to_keys_with_center(keys, notes, min_note, max_note, center_note=None, max_octave_shift=3):
    """
    将MIDI音符映射到键盘按键，通过八度移调来适应乐器的音域限制

    Args:
        keys: 键盘按键列表（连续的）
        notes: 原始键盘映射的MIDI音符列表（与keys一一对应）
        min_note: 目标乐曲的最低音符
        max_note: 目标乐曲的最高音符
        center_note: 指定的中间音调（如果不提供，则自动计算乐器中心）
        max_octave_shift: 允许的最大八度移调数

    Returns:
        dict: {note: key} 映射字典
    """

    # 创建原始映射字典
    original_mapping = dict(zip(notes, keys))

    # 确定乐器的音域范围
    instrument_min = min(notes)
    instrument_max = max(notes)

    # 如果乐器可以直接覆盖乐曲音域，直接映射
    if instrument_min <= min_note and instrument_max >= max_note:
        mapping = {}
        for note in range(min_note, max_note + 1):
            if note in original_mapping:
                mapping[note] = original_mapping[note]
        return mapping

    # 确定用于映射的中心音
    if center_note is None:
        # 如果未指定中心音，则使用乐器的中心音
        mapping_center = (instrument_min + instrument_max) // 2
    else:
        # 使用指定的中心音
        mapping_center = center_note

    # 计算乐曲的中心音
    required_center = (min_note + max_note) // 2

    # 计算最佳移调量（以12半音为一个八度）
    optimal_shift = mapping_center - required_center

    # 生成映射
    mapping = {}

    for note in range(min_note, max_note + 1):
        mapped = False

        # 首先尝试基础移调
        base_shifted_note = note + optimal_shift

        # 检查是否可以直接映射
        if instrument_min <= base_shifted_note <= instrument_max and base_shifted_note in original_mapping:
            mapping[note] = original_mapping[base_shifted_note]
            continue

        # 如果不能直接映射，尝试八度移调
        for octave_shift in range(0, max_octave_shift + 1):
            # 向上移调
            up_note = base_shifted_note + octave_shift * 12
            if instrument_min <= up_note <= instrument_max and up_note in original_mapping:
                mapping[note] = original_mapping[up_note]
                mapped = True
                break

            # 向下移调
            down_note = base_shifted_note - octave_shift * 12
            if instrument_min <= down_note <= instrument_max and down_note in original_mapping:
                mapping[note] = original_mapping[down_note]
                mapped = True
                break

        # 如果所有移调都无法映射，使用边界音符
        if not mapped:
            if base_shifted_note < instrument_min and instrument_min in original_mapping:
                mapping[note] = original_mapping[instrument_min]
            elif base_shifted_note > instrument_max and instrument_max in original_mapping:
                mapping[note] = original_mapping[instrument_max]
            # 如果在乐器范围内但没有对应键，则跳过该音符

    return mapping


def map_notes_to_keys_advanced(keys, notes, min_note, max_note, center_note=None, max_octave_shift=3):
    """
    高级版本：将MIDI音符映射到键盘按键，通过八度移调来适应乐器的音域限制

    Args:
        keys: 键盘按键列表（连续的）
        notes: 原始键盘映射的MIDI音符列表（与keys一一对应）
        min_note: 目标乐曲的最低音符
        max_note: 目标乐曲的最高音符
        center_note: 指定的中间音调（如果不提供，则自动计算乐器中心）
        max_octave_shift: 允许的最大八度移调数

    Returns:
        dict: {note: key} 映射字典
    """

    # 创建原始映射字典
    original_mapping = dict(zip(notes, keys))

    # 确定乐器的音域范围
    instrument_min = min(notes)
    instrument_max = max(notes)

    # 确定用于映射的中心音
    if center_note is None:
        # 如果未指定中心音，则使用乐器的中心音
        mapping_center = (instrument_min + instrument_max) // 2
    else:
        # 使用指定的中心音，但确保它在乐器范围内
        mapping_center = max(instrument_min, min(instrument_max, center_note))

    # 计算乐曲的中心音
    required_center = (min_note + max_note) // 2

    # 计算基础移调量
    base_shift = mapping_center - required_center

    # 生成映射
    mapping = {}

    # 首先处理可以直接映射的音符（无移调）
    for note in range(min_note, max_note + 1):
        shifted_note = note + base_shift
        if instrument_min <= shifted_note <= instrument_max and shifted_note in original_mapping:
            mapping[note] = original_mapping[shifted_note]

    # 处理需要八度移调的音符
    for note in range(min_note, max_note + 1):
        # 如果已经映射过了，跳过
        if note in mapping:
            continue

        shifted_note = note + base_shift
        mapped = False

        # 按照移调量从小到大尝试映射
        shift_attempts = []
        for octave_shift in range(0, max_octave_shift + 1):
            if octave_shift == 0:
                shift_attempts.append(0)
            else:
                shift_attempts.append(octave_shift * 12)
                shift_attempts.append(-octave_shift * 12)

        for shift in shift_attempts:
            adjusted_note = shifted_note + shift
            if instrument_min <= adjusted_note <= instrument_max and adjusted_note in original_mapping:
                mapping[note] = original_mapping[adjusted_note]
                mapped = True
                break

        # 如果所有移调都无法映射，使用边界音符
        if not mapped:
            if shifted_note < instrument_min and instrument_min in original_mapping:
                mapping[note] = original_mapping[instrument_min]
            elif shifted_note > instrument_max and instrument_max in original_mapping:
                mapping[note] = original_mapping[instrument_max]

    return mapping


if __name__ == '__main__':
    # 测试代码
    keys = ["z", "x", "c", "v", "b", "n", "m",
            "a", "s", "d", "f", "g", "h", "j",
            "q", "w", "e", "r", "t", "y", "u"]
    notes = [53, 54, 55, 56, 57, 58, 59,
             60, 61, 62, 63, 64, 65, 66,
             67, 68, 69, 70, 71, 72, 73]
    mapping = map_notes_to_keys_advanced(keys, notes, 58, 97)
    new_sys1 = sorted(mapping.items(), key=lambda d: d[0], reverse=False)
    print(new_sys1)
