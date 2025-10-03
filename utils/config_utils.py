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
    WEB_SOCKET_URI = "websocket.uri"
    WEB_SOCKET_RETRY_MAX = "websocket.retry.max"
    WEB_SOCKET_RETRY_DELAY = "websocket.retry.delay"


default_config = {
    ConfigField.WEB_SOCKET_URI: "ws://localhost:8765",
    ConfigField.MIDI_PATH: "./midis",
    ConfigField.LOG_FILE: "./app.log",
    ConfigField.LOG_LEVEL: logging.INFO,
    ConfigField.LOG_FORMAT: "text",
    ConfigField.WEB_SOCKET_RETRY_MAX: 5,
    ConfigField.WEB_SOCKET_RETRY_DELAY: 5
}
