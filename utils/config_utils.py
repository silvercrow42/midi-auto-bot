import logging
from enum import Enum


class ConfigField(Enum):
    """
    配置字段枚举类
    """
    MIDI_PATH = "midi.path"
    LOG_FILE = "log.file"
    LOG_LEVEL = "log.level"
    LOG_FORMAT = "log.format"


default_config = {
    ConfigField.MIDI_PATH: "./midis",
    ConfigField.LOG_FILE: "./app.log",
    ConfigField.LOG_LEVEL: logging.INFO,
    ConfigField.LOG_FORMAT: "text"
}
