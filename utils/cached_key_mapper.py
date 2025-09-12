class CachedKeyMapper:
    def __init__(self, base_notes=None, zooms=None, max_notes=None):
        self.base_notes = base_notes or {}
        self.zooms = zooms or {}
        self.max_notes = max_notes or {}
        self.note_maps = {}

    def _get_base_note(self, channel):
        if channel not in self.base_notes:
            self.base_notes[channel] = 0
        return self.base_notes[channel]

    def _get_zoom(self, channel):
        if channel not in self.zooms:
            self.zooms[channel] = 1
        return self.zooms[channel]

    def _get_max_note(self, channel):
        if channel not in self.max_notes:
            self.max_notes[channel] = 20
        return self.max_notes[channel]

    def get_mapped_note(self, channel, note):
        base_note = self._get_base_note(channel)
        zoom = self._get_zoom(channel)
        max_note = self._get_max_note(channel)
        if channel not in self.note_maps:
            self.note_maps[channel] = {}
        note_map = self.note_maps[channel]
        if note not in note_map:
            if note < base_note:  # 小于基础键的键都被映射为基础键
                note_map[note] = base_note
            elif note > base_note + zoom * max_note + 1:  # 大于最大键的键都被映射为最大键
                note_map[note] = base_note + max_note
            else:
                note_diff = note - base_note
                note_map[note] = base_note + note_diff // zoom
        return note_map[note]

    def get_key_by_note(self, channel, note, keys):
        mapped_key_index = self.get_mapped_note(channel, note) - self.base_notes[channel]
        return keys[mapped_key_index]

    def set_base_note(self, channel, base_note):
        self.base_notes[channel] = base_note
        self.clear(channel)

    def set_zoom(self, channel, zoom):
        self.zooms[channel] = zoom
        self.clear(channel)

    def set_max_note(self, channel, max_note):
        self.max_notes[channel] = max_note
        self.clear(channel)

    def clear(self, channel):
        if channel in self.note_maps:
            del self.note_maps[channel]
