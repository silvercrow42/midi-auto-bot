import json
from typing import List

from midi.player.basic_midi_player import BasicMidiPlayer
from utils.cached_key_mapper import CachedKeyMapper


class ZoomRemapPlayer(BasicMidiPlayer):
    def __init__(self):
        super().__init__()
        self._key_mapper = CachedKeyMapper()

    def get_key_by_note(self, channel: int, note: int, keys: List[str]):
        key = self._key_mapper.get_key_by_note(channel, note, keys)
        return key

    def load_midi_file(self, file_path: str, channels: List[int], max_note: int = 20):
        super().load_midi_file(file_path, channels)

        with open(file_path + '/config.json', 'r', encoding='utf-8') as file:
            midi_configs = json.load(file)
            for i in channels:
                midi_config = midi_configs[str(i)]
                base_note = 60
                zoom = 1
                if midi_config is not None:
                    base_note = midi_config.get('base_note', base_note)
                    zoom = midi_config.get('zoom', zoom)
                self._key_mapper.set_zoom(i, zoom)
                self._key_mapper.set_base_note(i, base_note)
                self._key_mapper.set_max_note(i, max_note)
