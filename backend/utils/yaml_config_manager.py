import os
from typing import Any, Dict, Optional

import yaml

from backend.utils.config_utils import default_config, ConfigField


class YAMLConfigManager:
    def __init__(self, config_file: str, default_init_config: Optional[Dict[ConfigField, Any]] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
            default_init_config: 默认配置字典
        """
        self.config_file = config_file
        init_config = {}
        for key, value in default_init_config.items():
            _set_by_path(init_config, key, value)
        self.default_config = init_config
        self.config_data = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件到内存"""
        # 如果配置文件不存在，创建默认配置文件
        if not os.path.exists(self.config_file):
            self.save(self.default_config)

        # 读取配置文件
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                self.config_data = yaml.safe_load(file) or {}
        except Exception as e:
            print(f"读取配置文件失败: {e}")

    def get(self, key_path: str, default_value: Any = None) -> Any:
        """
        从配置中获取值，支持嵌套路径和默认值

        Args:
            key_path: 配置项路径，如 'database.host'
            default_value: 默认值

        Returns:
            配置项的值
        """
        config_value = _get_by_path(self.config_data, key_path, default_value)
        print(f"获取配置项: {key_path} = {config_value}")
        return config_value

    def set(self, key_path: str, value: Any):
        """
        设置配置项的值

        Args:
            key_path: 配置项路径，如 'database.host'
            value: 要设置的值
        """
        print(f"设置配置项: {key_path} = {value}")
        _set_by_path(self.config_data, key_path, value)

    def save(self, config_data):
        """保存配置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as file:
                yaml.dump(config_data, file, default_flow_style=False, allow_unicode=True)
            print(f"配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def reload(self):
        """重新加载配置文件"""
        self._load_config()

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config_data.copy()


def _set_by_path(config_data, key_path: str | ConfigField, value: Any):
    keys = _get_key_paths(key_path)
    # 遍历到倒数第二个键，创建必要的嵌套结构
    for key in keys[:-1]:
        if key not in config_data:
            config_data[key] = {}
        config_data = config_data[key]

    # 设置最终的值
    config_data[keys[-1]] = value


def _get_by_path(config_data, key_path: str | ConfigField, default_value: Any = None):
    keys = _get_key_paths(key_path)
    value = config_data

    try:
        # 遍历路径获取值
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        # 如果配置项不存在，使用默认值并更新配置
        _set_by_path(config_data, key_path, default_value)
        return default_value


def _get_key_paths(key_path: str | ConfigField):
    if isinstance(key_path, ConfigField):
        return key_path.value.split('.')
    return key_path.split('.')


# 配置项管理器
cm = YAMLConfigManager("./config/config.yaml", default_config)
