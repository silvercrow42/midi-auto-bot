import yaml


def load_config(config_file):
    """加载 YAML 配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"配置文件 {config_file} 不存在")
        return None
    except yaml.YAMLError as e:
        print(f"YAML 解析错误: {e}")
        return None
