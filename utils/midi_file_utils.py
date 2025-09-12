import os

from constants.global_variable import midi_index_suffix, midi_target_path


def list_current_directory_midis():
    """
    基本方法遍历当前目录
    """
    print("当前目录下的文件和文件夹：")
    items = os.listdir(midi_target_path)  # '.' 表示当前目录
    index = 0
    result = []
    for item in items:
        target_file = handle_file(item, index)
        if target_file is not None:
            result.append(target_file)
            index += 1
    return result


def handle_file(file_path, index):
    """
    处理文件
    """
    if os.path.isfile(file_path):
        if file_path.endswith('.mid'):
            return {
                "index": index,
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "is_file": True
            }
    if os.path.isdir(file_path):
        print(f"正在处理文件夹: {file_path}")
        target_file = f"{file_path}{midi_index_suffix}"
        if os.path.exists(target_file):
            return {
                "index": index,
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "is_file": False
            }
