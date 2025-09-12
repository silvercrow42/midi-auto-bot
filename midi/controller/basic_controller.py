from api.event_bus_api import event_bus
from midi.event.midi_events import NoteOnEvent, NoteOffEvent
from midi.player.zoom_remap_player import ZoomRemapPlayer
from utils.midi_file_utils import list_current_directory_midis
from utils.window_controller import WindowController


class BasicController:
    def __init__(self):
        self.window_controller = WindowController()
        self.midi_player = ZoomRemapPlayer()
        self.keys = ["z", "x", "c", "v", "b", "n", "m", "a", "s", "d", "f",
                     "g", "h", "j", "q", "w", "e", "r", "t", "y", "u"]
        self.channels = [0]
        self.midi_files = []

        def note_on_handler(event: NoteOnEvent):
            if event.message.channel in self.channels:
                # todo 实现全局控制日志打印
                print(f"Note On: note={event.message.note}, time={event.timestamp:.2f}s")
                key = self.midi_player.get_key_by_note(event.message.channel, event.message.note, self.keys)
                event_bus.midi_note_on(key)
                self.window_controller.keydown(key)

        def note_off_handler(event: NoteOffEvent):
            if event.message.channel in self.channels:
                print(f"Note Off: note={event.message.note}, time={event.timestamp:.2f}s")
                key = self.midi_player.get_key_by_note(event.message.channel, event.message.note, self.keys)
                event_bus.midi_note_off(key)
                self.window_controller.keyup(key)

        self.midi_player.register_event_handler('note_on', note_on_handler)
        self.midi_player.register_event_handler('note_off', note_off_handler)

    ##### MIDI PLAYER METHODS
    def load_midi(self, file_path):
        self.midi_player.load_midi_file(file_path, self.channels, len(self.keys) - 1)

    def play(self):
        self.midi_player.play()

    def stop(self):
        self.midi_player.stop()

    def pause(self):
        self.midi_player.pause()

    def seek(self, position):
        self.midi_player.seek(position)

    def get_state(self):
        return self.midi_player.get_state()

    def get_duration(self):
        return self.midi_player.get_duration()

    def get_position(self):
        return self.midi_player.get_position()

    def get_track_summaries(self):
        return self.midi_player.get_track_summaries()

    def get_channels(self):
        return self.channels

    def set_channels(self, channels):
        self.channels = channels

    def set_keys(self, keys):
        self.keys = keys

    def refresh_midi_list(self):
        self.midi_files = list_current_directory_midis()
        return self.midi_files

    ##### WINDOW CONTROLLER METHODS
    def keydown(self, key):
        if key in self.keys:
            self.window_controller.keydown(key)

    def keyup(self, key):
        if key in self.keys:
            self.window_controller.keyup(key)
