def expand_array(arr, i, n):
    """
    数组拓展的简化版本
    """
    if not arr or n <= 1:
        return arr[:]

    original_length = len(arr)

    # 构建拓展后的完整数组
    expanded = []

    # 处理索引i前的元素
    for idx in range(i):
        expanded.extend([arr[idx]] * n)  # 每个元素重复n次

    # 处理索引i及其后的元素
    for idx in range(i, original_length):
        expanded.extend([arr[idx]] * n)  # 每个元素重复n次
    return expanded


def shift_array_loop(arr, positions):
    """
    统一环形移动数组元素（溢出部分填入开头或结尾）

    Args:
        arr: 原始数组
        positions: 移动位置数（正数表示后移，负数表示前移）

    Returns:
        移动后的数组
    """
    if not arr or positions == 0:
        return arr[:]

    length = len(arr)
    positions = positions % length

    if positions > 0:
        # 后移
        return arr[-positions:] + arr[:-positions]
    else:
        # 前移
        positions = -positions
        return arr[positions:] + arr[:positions]


def shift_array(arr, positions, default_factory=None):
    """
    数组元素统一移动，无值部分通过默认值工厂方法构造

    Args:
        arr: 原始数组
        positions: 移动位置数（正数表示后移，负数表示前移）
        default_factory: 默认值构造工厂

    Returns:
        移动后的数组
    """
    if not arr:
        return arr[:]

    if default_factory is None:
        default_factory = lambda: None

    length = len(arr)
    result = [default_factory() for _ in range(length)]

    if positions >= 0:
        # 后移
        start_src = 0
        start_dst = positions
        count = max(0, min(length - positions, length))
    else:
        # 前移
        start_src = abs(positions)
        start_dst = 0
        count = max(0, min(length - abs(positions), length))

    # 复制有效数据
    for i in range(count):
        result[start_dst + i] = arr[start_src + i]

    return result
