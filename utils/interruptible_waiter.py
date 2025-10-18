import time
import threading
from typing import Union


class InterruptibleWaiter:
    """
    支持中断的等待器
    - 如果等待被中断，返回已经等待的时间
    - 如果等待自然完成，返回0
    """

    def __init__(self):
        self._interrupt_event = threading.Event()
        self._start_time = 0
        self._waiting = False

    def wait(self, seconds: float) -> float:
        """
        等待指定时间

        Args:
            seconds: 要等待的秒数

        Returns:
            float: 如果被中断则返回已等待时间，否则返回0
        """
        if self._waiting:
            raise RuntimeError("Already waiting, cannot start a new wait")

        self._waiting = True
        self._interrupt_event.clear()
        self._start_time = time.time()

        try:
            # 等待指定时间或被中断
            interrupted = self._interrupt_event.wait(seconds)

            if interrupted:
                # 被中断，计算已等待时间
                elapsed = time.time() - self._start_time
                return elapsed
            else:
                # 自然完成
                return 0.0
        finally:
            self._waiting = False

    def interrupt(self) -> bool:
        """
        中断当前的等待

        Returns:
            bool: 是否成功中断（True表示有等待被中断）
        """
        if self._waiting:
            self._interrupt_event.set()
            return True
        return False

    def is_waiting(self) -> bool:
        """检查是否正在等待"""
        return self._waiting

    def is_interrupted(self) -> bool:
        """检查是否被中断"""
        return self._interrupt_event.is_set()

    def clear_interrupt(self):
        """清除中断状态"""
        self._interrupt_event.clear()
