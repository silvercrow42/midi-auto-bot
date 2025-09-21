class CustomKeyMapper:
    def __init__(self, base_note=None, zoom=None, keys=None, note_map=None):
        if keys is None:
            keys = []
        self.keys = keys
        self.base_note = base_note or 0
        self.zoom = zoom or 1
        if note_map:
            self.note_map = note_map
        else:
            self.build_note_map()

    def build_note_map(self):
        note_map = {}
        for note in range(0, 127):
            note_map[note] = self.__get_single_note(note, self.base_note, self.zoom, self.keys)
        self.note_map = note_map

    @staticmethod
    def __get_single_note(note, base_note, zoom, keys: list):
        if note < base_note:  # 小于基础键的键都被映射为基础键
            remap_key = keys[0]
        elif note > base_note + zoom * len(keys) + 1:  # 大于最大键的键都被映射为最大键
            remap_key = keys[len(keys) - 1]
        else:
            note_diff = note - base_note
            remap_key = keys[note_diff // zoom]
        return remap_key

    def set_base_note(self, base_note):
        self.base_note = base_note

    def set_keys(self, keys):
        self.keys = keys

    def set_zoom(self, zoom):
        self.zoom = zoom

    def set_note_map(self, notes: list, key):
        for note in notes:
            self.note_map[note] = key

    def get_note_map(self):
        return self.note_map

    def get_key_by_note(self, note):
        return self.note_map[note]

    def get_notes_by_key(self, key):
        return [note for note, k in self.note_map.items() if k == key]

    def get_note_map_by_keys(self, keys):
        return {note: self.get_key_by_note(note) for note in keys}
