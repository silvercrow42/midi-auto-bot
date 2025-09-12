import json
import time

import keyboard
import win32api
import win32con
import win32gui

from utils.main import enum_windows_callback


# 窗口按键控制器
class WindowController:
    def __init__(self, filter: callable = lambda a, b: enum_windows_callback(a, b)):
        self.hwnd = self.__init_window(filter)
        self.pressed_keys = set()
        if self.hwnd is None:
            raise Exception("未找到游戏窗口。")

    # 检测游戏窗口
    def __init_window(self, filter):
        hwnds = []
        win32gui.EnumWindows(lambda a, b: filter(a, b), hwnds)

        if len(hwnds) == 0:
            print('未找到游戏窗口。')
            time.sleep(5)
            return None

        return hwnds[0]

    # 关闭游戏窗口
    def close_window(self):
        try:
            win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
            print("游戏窗口已关闭")
        except Exception as e:
            print(f"关闭窗口失败: {e}")

    # 检测窗口是否最小化
    def is_window_minimized(self):
        placement = win32gui.GetWindowPlacement(self.hwnd)
        return placement[1] == win32con.SW_SHOWMINIMIZED

    # 后台模式按键输入
    def press(self, key='f', tm=0.2, keyupdown=3):

        # 取消最小化
        if self.is_window_minimized():
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        key = 0x41 + ord(key) - ord('a')
        if keyupdown & 2:
            self.pressed_keys.add(key)
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, key, 0)
        if keyupdown == 3:
            time.sleep(tm)
        if keyupdown & 1:
            if key in self.pressed_keys:
                self.pressed_keys.remove(key)
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, key, 0)

    def keydown(self, key='f'):
        self.press(key, keyupdown=2)

    def keyup(self, key='f'):
        self.press(key, keyupdown=1)

    def clear(self):
        for key in self.pressed_keys:
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, key, 0)
