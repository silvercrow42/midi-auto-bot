import threading
import time

from backend.api.event_bus_api import event_bus

progress_push_interval = 0.5

min_progress_push_interval = max(progress_push_interval - 0.2, 0.2)


class ProgressListener:
    def __init__(self):
        self._progress_listen_thread = None
        self._progress_listen_stop_event = threading.Event()
        self._current_time = 0
        self._max_time = 0

    def _listen_loop(self):
        """
        定时刷新当前播放时间的循环
        每次推送当前播放时间
        """
        last_time = time.time()
        while not self._progress_listen_stop_event.is_set():
            now = time.time()
            if now - last_time > 0.3:
                current_progress = self._current_time + time.time() - last_time
                last_time = now
                if current_progress > self._max_time:
                    self._current_time = self._max_time
                    event_bus.progress(self._current_time)
                    self.stop()
                self._current_time = current_progress
                event_bus.progress(self._current_time)
            # 短暂休眠以避免过度占用CPU
            time.sleep(0.5)

    def set_max_time(self, max_time):
        self._max_time = max_time

    def start(self):
        self._progress_listen_stop_event.clear()
        self._progress_listen_thread = threading.Thread(target=self._listen_loop)
        self._progress_listen_thread.daemon = True
        self._progress_listen_thread.start()

    def stop(self):
        self._progress_listen_stop_event.set()
        if self._progress_listen_thread and self._progress_listen_thread.is_alive():
            self._progress_listen_thread.join(timeout=1.0)

    def set_current_time(self, current_time):
        self._current_time = current_time

    def clear(self):
        self._current_time = 0
