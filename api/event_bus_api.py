from api.simple_event_throttler import SimpleEventThrottler


class EventBus:

    def __init__(self):
        self._throttler = None

    # 这个方法由 pywebview 内部调用，用于注入 window 对象
    def load_window(self, window):
        self._throttler = SimpleEventThrottler(window)

    def progress(self, current_time):
        self._push_event("progress", current_time)

    def midi_note_on(self, key):
        self._push_event("noteOn", f'"{key}"')

    def midi_note_off(self, key):
        self._push_event("noteOff", f'"{key}"')

    def _push_event(self, event_name, data=None):
        self._throttler.push_event(event_name, data)

    def _push_event_throttled(self, event_name, data=None):
        self._throttler.push_event_throttled(event_name, data)


event_bus = EventBus()
