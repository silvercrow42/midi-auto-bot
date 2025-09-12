import json
import time

import keyboard
import win32api
import win32con
import win32gui

init_actions = [['f'], [2.4], ['f'], [0.5], ['s', 0.2, 3], [0.3], ['f'], [1.5], ['f'], [0.5], ['f'], [0.5], ['f'],
                [1.0]]
play_actions = [['f'], [5], ['w', 0.0, 2], [5], ['d', 0.7, 3], [0.65], ['d', 1.1, 3], [1.1], ['d', 0.5, 3], [0.3],
                ['d', 0.9, 3], [2], ['w', 0.0, 1]]
replay_actions = [[5], ['f'], [1.8], ['f'], [0.7], ['f'], [0.7], ['f'], [1.5], ['f'], [0.7], ['f'], [0.7], ['f'], [1.2]]


# 关闭游戏窗口
def close_window(hwnd):
    try:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        print("游戏窗口已关闭")
    except Exception as e:
        print(f"关闭窗口失败: {e}")


# 检测窗口是否最小化
def is_window_minimized(hwnd):
    placement = win32gui.GetWindowPlacement(hwnd)
    return placement[1] == win32con.SW_SHOWMINIMIZED


# 后台模式按键输入
def press(key='f', tm=0.2, keyupdown=3):
    global game_nd, stop
    hwnd = game_nd

    # 取消最小化
    if is_window_minimized(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    key = 0x41 + ord(key) - ord('a')
    if keyupdown & 2 and not stop:
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key, 0)
    if keyupdown == 3 and not stop:
        time.sleep(tm)
    if keyupdown & 1 and not stop:
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, key, 0)

    # 枚举所有窗口


def enum_windows_callback(hwnd, hwnds):
    try:
        class_name = win32gui.GetClassName(hwnd).strip()
        window_name = win32gui.GetWindowText(hwnd).strip()
        if (
                window_name == 'Infinity Nikki' or window_name == 'InfinityNikki' or window_name == '无限暖暖') and class_name == 'UnrealWindow':
            hwnds.append(hwnd)
    except:
        pass
    return True


# 检测游戏窗口
def init_window():
    hwnds = []
    win32gui.EnumWindows(lambda a, b: enum_windows_callback(a, b), hwnds)

    if len(hwnds) == 0:
        print('未找到游戏窗口。')
        time.sleep(5)
        return None

    game_nd = hwnds[0]
    return game_nd


# 检测手动暂停
def on_key_press(event):
    if event.name == "f8":
        global stop
        print("F8 已被按下，尝试停止运行")
        stop = True


# 读取用户选择数据
def load_info():
    try:
        with open('info.txt', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# 保存用户选择数据
def save_info(info):
    with open('info.txt', 'w') as f:
        json.dump(info, f)


# 询问用户选择
def ask_user_choice():
    global closure, remember_cls

    # 关闭选择
    if remember_cls != 1:  # 0 or 2
        while True:
            try:
                print("\n请选择结束时是否自动关闭游戏：0 为否，1 为是。")
                closure = int(input("输入您的选择："))
                if closure in [0, 1]:
                    break
            except ValueError:
                pass
            print("无效输入，请输入 0 或 1。")

        if remember_cls == 0:
            while True:
                try:
                    print("是否记住自动关闭选择？0 为否，1 为记住选择，2 为否且不再询问。")
                    remember_cls = int(input("输入您的选择："))
                    if remember_cls in [0, 1, 2]:
                        break
                except ValueError:
                    pass
                print("无效输入，请输入 0、1 或 2。")
        else:
            print("关闭选择已不再询问，请删除 info.txt 进行重新设置。")


def do_actions(actions):
    global stop
    for a in actions:
        if stop: break
        if type(a[0]) in [int, float]:
            time.sleep(a[0])
        elif type(a[0]) == str:
            if a[0] == 'f':
                press(a[0])
            else:
                press(a[0], a[1], a[2])


if __name__ == "__main__":
    stop = False

    # 初始化用户信息文件
    info = load_info()
    closure = info.get("closure")
    remember_cls = info.get("remember_closure", 0)

    if remember_cls != 1:
        ask_user_choice()

        # 更新并保存选择
        info["closure"] = closure
        info["remember_closure"] = remember_cls
        save_info(info)

    keyboard.on_press(on_key_press)
    game_nd = init_window()
    nums = 267

    if game_nd is not None:
        tm = time.time()
        end_time = tm + 31.18 * nums
        print("游戏窗口已找到，开始运行。")
        print(
            f"运行时间：{int(31.18 * nums // 60)} 分钟，预计结束时刻：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}。")

        do_actions(init_actions)
        for _ in range(nums):
            ttm = time.time()
            do_actions(play_actions)
            do_actions(replay_actions)
            if stop: break
            print(f"第 {_ + 1} 次运行，耗时 {time.time() - ttm:.2f} s。")
        if stop:
            print("运行已停止。")
        else:
            print(f"运行次数已达 {nums}，运行自动停止。")
            if closure == 1:
                print("准备自动关闭游戏窗口...")
                close_window(game_nd)
