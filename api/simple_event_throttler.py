import threading
import time


# 事件节流器
class SimpleEventThrottler:
    def __init__(self, window):
        self._window = window
        self.last_sent = {}  # 记录每种事件最后发送时间
        self.pending_events = {}  # 记录待发送的事件
        self.lock = threading.Lock()

    def push_event_throttled(self, event_type, event_data, interval=0.6):
        """
        推送限流事件

        :param event_type: 事件类型
        :param event_data: 事件数据
        :param interval: 时间间隔（秒）
        """
        with self.lock:
            current_time = time.time()
            last_time = self.last_sent.get(event_type, 0)

            if current_time - last_time >= interval:
                # 立即发送
                self.push_event(event_type, event_data)
                self.last_sent[event_type] = current_time
                # 清除待发送事件
                if event_type in self.pending_events:
                    del self.pending_events[event_type]
            else:
                # 缓存事件，覆盖之前的同类型事件
                self.pending_events[event_type] = {
                    'data': event_data,
                    'scheduled_time': last_time + interval
                }
                # 启动定时器处理缓存事件
                delay = interval - (current_time - last_time)
                timer = threading.Timer(delay, self._send_pending_event, [event_type])
                timer.start()

    def push_event(self, event_name, data=None, is_async=False):
        script = f"sendEvent('{event_name}', {data})"

        def push():
            self._window.evaluate_js(script)

        if is_async:
            threading.Thread(target=push).start()
        else:
            push()

    def _send_pending_event(self, event_type):
        """
        发送缓存的事件
        """
        with self.lock:
            if event_type in self.pending_events:
                event_info = self.pending_events[event_type]
                self.push_event(event_type, event_info['data'])
                self.last_sent[event_type] = time.time()
                del self.pending_events[event_type]
