import json
from typing import Dict, Any, Union


class JsonUtil:
    """
    JSON工具类，用于处理JSON字符串和文件的读写操作
    """

    @staticmethod
    def load_from_string(json_string: str) -> Dict[str, Any]:
        """
        从JSON字符串加载数据为字典

        Args:
            json_string (str): JSON格式的字符串

        Returns:
            Dict[str, Any]: 解析后的字典对象

        Raises:
            json.JSONDecodeError: 当JSON字符串格式不正确时抛出异常
        """
        return json.loads(json_string)

    @staticmethod
    def load_from_file(file_path: str) -> Dict[str, Any]:
        """
        从JSON文件加载数据为字典

        Args:
            file_path (str): JSON文件路径

        Returns:
            Dict[str, Any]: 解析后的字典对象

        Raises:
            FileNotFoundError: 当文件不存在时抛出异常
            json.JSONDecodeError: 当文件内容不是有效JSON格式时抛出异常
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    @staticmethod
    def dump_to_string(data: Dict[str, Any], indent: Union[int, str, None] = None) -> str:
        """
        将字典转换为JSON字符串

        Args:
            data (Dict[str, Any]): 要转换的字典对象
            indent (Union[int, str, None]): 缩进格式，None表示不格式化，int表示空格数

        Returns:
            str: 格式化后的JSON字符串
        """
        return json.dumps(data, ensure_ascii=False, indent=indent)

    @staticmethod
    def dump_to_file(data: Dict[str, Any], file_path: str, indent: Union[int, str, None] = None) -> None:
        """
        将字典保存为JSON文件

        Args:
            data (Dict[str, Any]): 要保存的字典对象
            file_path (str): 输出文件路径
            indent (Union[int, str, None]): 缩进格式，None表示不格式化，int表示空格数
        """
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=indent)
