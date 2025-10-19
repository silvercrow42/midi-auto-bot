# advanced_logger.py
import functools
import logging
import os
import json
from typing import Callable
import inspect
from datetime import datetime

from backend.utils.config_utils import ConfigField
from backend.utils.yaml_config_manager import cm


class GlobalLogger:
    """高级全局日志管理器"""
    _instance = None
    _logger = None
    _log_file = "app.log"
    _format = 'json'  # 支持 'text' 或 'json'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalLogger, cls).__new__(cls)
        return cls._instance

    def configure(self, log_file: str = "app.log", level: int = logging.INFO,
                  log_format: str = 'text'):
        """配置全局日志"""
        self._log_file = log_file
        self._format = log_format

        # 创建日志目录（如果不存在）
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 配置日志
        if log_format == 'json':
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # 设置日志处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        self._logger = logging.getLogger("AdvancedGlobalLogger")
        self._logger.setLevel(level)
        self._logger.addHandler(file_handler)
        self._logger.addHandler(stream_handler)

    @property
    def logger(self) -> logging.Logger:
        """获取全局日志记录器"""
        if self._logger is None:
            self.configure("./" + cm.get(ConfigField.LOG_FILE),
                           cm.get(ConfigField.LOG_LEVEL),
                           cm.get(ConfigField.LOG_FORMAT))
        return self._logger


class JsonFormatter(logging.Formatter):
    """JSON格式日志格式化器"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # 如果有额外的属性，也添加进去
        if hasattr(record, 'func_name'):
            log_entry['function'] = record.func_name
        if hasattr(record, 'params'):
            log_entry['params'] = record.params
        if hasattr(record, 'result'):
            log_entry['result'] = record.result

        return json.dumps(log_entry, ensure_ascii=False)


# 创建全局日志实例
global_logger = GlobalLogger()


def logger(
        log_params: bool = False,
        log_result: bool = False,
        log_level: int = logging.INFO,
        custom_message: str = None,
        include_caller: bool = False,
        mask_params: list = None
):
    """
    高级方法日志装饰器

    Args:
        log_params: 是否记录方法参数
        log_result: 是否记录返回值
        log_level: 日志级别
        custom_message: 自定义日志消息
        include_caller: 是否包含调用者信息
        mask_params: 需要掩码的参数名列表
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = global_logger.logger
            func_name = func.__name__

            # 获取方法签名
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 处理参数掩码
            logged_params = dict(bound_args.arguments)
            if mask_params:
                for param_name in mask_params:
                    if param_name in logged_params:
                        logged_params[param_name] = "***"

            # 构建日志记录的额外属性
            extra = {
                'func_name': func_name,
            }

            # 记录方法调用开始
            if custom_message:
                start_message = f"{custom_message} - 调用方法: {func_name}"
            else:
                start_message = f"调用方法: {func_name}"

            if log_params:
                params_str = ", ".join([f"{k}={repr(v)}" for k, v in logged_params.items()])
                start_message += f" 参数: ({params_str})"
                extra['params'] = logged_params

            # 添加调用者信息
            if include_caller:
                caller_frame = inspect.currentframe().f_back
                caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
                start_message += f" [调用者: {caller_info}]"

            logger.log(log_level, start_message, extra=extra)

            try:
                # 执行方法
                result = func(*args, **kwargs)

                # 记录方法执行成功
                end_message = f"方法执行成功: {func_name}"
                if log_result:
                    end_message += f" 返回值: {repr(result)}"
                    extra['result'] = result

                logger.log(log_level, end_message, extra=extra)
                return result

            except Exception as e:
                # 记录异常
                error_message = f"方法执行异常: {func_name} 异常信息: {str(e)}"
                logger.error(error_message, extra=extra)
                raise

        return wrapper

    return decorator


# 便捷函数
def configure_logger(log_file: str = "app.log", level: int = logging.INFO,
                     log_format: str = 'text'):
    """配置高级全局日志"""
    global_logger.configure(log_file, level, log_format)


def get_logger() -> logging.Logger:
    """获取高级全局日志记录器"""
    return global_logger.logger
