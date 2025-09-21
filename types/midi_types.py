import mido
from typing import List


class MidiTrackSummary:
    def __init__(self, i: int, name: str, length: int, duration_ticks: int, has_notes: bool):
        self.track_index = i
        self.name = f'{i}'
        self.length = len(track)
        self.duration_ticks = sum(msg.time for msg in track)
        self.has_notes = False
        self.instrument = None
        self.channels = set()
