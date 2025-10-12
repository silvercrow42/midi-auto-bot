import time

import win32api
import win32con
import win32gui
import win32process

from api import event_bus
from utils.logger import get_logger


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


# 窗口按键控制器
class WindowController:
    def __init__(self, filter: callable = lambda a, b: enum_windows_callback(a, b)):
        self.hwnd = self.__init_window(filter)
        self.pressed_keys = set()

    # 检测游戏窗口
    def __init_window(self, filter):
        hwnds = []
        win32gui.EnumWindows(lambda a, b: filter(a, b), hwnds)

        if len(hwnds) == 0:
            get_logger().error('未找到游戏窗口。')
            time.sleep(5)
            return None

        return hwnds[0]

    # 关闭游戏窗口
    def close_window(self):
        try:
            win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
            get_logger().info("游戏窗口已关闭")
        except Exception as e:
            get_logger().error(f"关闭窗口失败: {e}")

    # 检测窗口是否最小化
    def is_window_minimized(self):
        placement = win32gui.GetWindowPlacement(self.hwnd)
        return placement[1] == win32con.SW_SHOWMINIMIZED

    # 后台模式按键输入
    def press(self, key='f', tm=0.1, keyupdown=3, push_event=True):
        old_key = key
        if not self.hwnd:
            return
        # 取消最小化
        if self.is_window_minimized():
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        if keyupdown & 2:
            self.__do_keydown(old_key, push_event)
        if keyupdown == 3:
            time.sleep(tm)
        if keyupdown & 1:
            self.__do_keyup(old_key, push_event)

    @staticmethod
    def __get_key_code(key):
        return 0x41 + ord(key) - ord('a')

    def __do_keydown(self, original_key, push_event=True):
        try:
            if original_key in self.pressed_keys:
                self.__do_keyup(original_key)
            self.pressed_keys.add(original_key)
            if push_event:
                event_bus.midi_note_on(original_key)
            win_key = WindowController.__get_key_code(original_key)
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, win_key, 0)
        except Exception as e:
            pass

    def __do_keyup(self, original_key, push_event=True):
        # 释放按键
        try:
            if original_key in self.pressed_keys:
                if push_event:
                    event_bus.midi_note_off(original_key)
                win_key = WindowController.__get_key_code(original_key)
                win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, win_key, 0)
                self.pressed_keys.remove(original_key)
        except Exception as e:
            pass

    def clear(self):
        for key in self.pressed_keys.copy():
            self.__do_keyup(key)

    # 获取所有窗口句柄
    def get_all_windows(self):
        """
        获取所有窗口句柄，不进行过滤

        Returns:
            list: 包含所有窗口句柄的列表
        """
        hwnds = []

        def enum_window_callback(hwnd, param):
            try:
                # 获取窗口标题
                title = win32gui.GetWindowText(hwnd)
                if not title:
                    return
                # 获取窗口类名
                class_name = win32gui.GetClassName(hwnd)

                # 获取窗口位置和大小
                rect = win32gui.GetWindowRect(hwnd)

                # 获取窗口状态
                visible = win32gui.IsWindowVisible(hwnd)
                enabled = win32gui.IsWindowEnabled(hwnd)

                # 获取窗口放置信息
                placement = win32gui.GetWindowPlacement(hwnd)
                minimized = placement[1] == win32con.SW_SHOWMINIMIZED
                maximized = placement[1] == win32con.SW_SHOWMAXIMIZED

                # 获取进程ID
                _, process_id = win32process.GetWindowThreadProcessId(hwnd)

                window_info = {
                    'hwnd': hwnd,
                    'title': title,
                    'class_name': class_name,
                    'rect': rect,
                    'visible': visible,
                    'enabled': enabled,
                    'minimized': minimized,
                    'maximized': maximized,
                    'process_id': process_id
                }

                param.append(window_info)
            except Exception as e:
                # 某些窗口可能无法获取信息，跳过它们
                pass

        win32gui.EnumWindows(enum_window_callback, hwnds)
        return hwnds

    # 设置目标窗口
    def set_target_window(self, hwnd):
        """
        设置目标窗口句柄

        Args:
            hwnd: 窗口句柄

        Returns:
            bool: 设置成功返回True，否则返回False
        """
        if win32gui.IsWindow(hwnd):
            self.hwnd = hwnd
            return True
        else:
            raise Exception(f"窗口句柄 {hwnd} 不存在或无效")

    def get_target_window(self):
        """
        获取当前目标窗口句柄

        Returns:
            int: 当前目标窗口句柄
        """
        return self.hwnd
