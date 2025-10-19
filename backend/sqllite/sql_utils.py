from sqlalchemy.inspection import inspect as sqlalchemy_inspect
from typing import Union, List, Any

from backend.sqllite import Session, Base, engine


def get_session():
    """获取数据库会话实例"""
    return Session()


def create_tables():
    """创建所有定义的表"""
    Base.metadata.create_all(engine)


def close_session(session):
    """关闭数据库会话"""
    session.close()


def save(session: Session, data: Union[object, List[object]], model_class=None):
    """
    智能保存方法，根据数据类型和主键自动选择保存策略

    Args:
        session: 数据库会话
        data: 单个对象或对象列表
        model_class: 模型类（可选，用于字典数据）
    """

    # 判断是否为批量操作
    if isinstance(data, list):
        return _batch_save(session, data, model_class)
    else:
        return _single_save(session, data, model_class)


def query_all(session: Session, model_class):
    """查询所有记录"""
    try:
        return session.query(model_class).all()
    finally:
        close_session(session)


def query_by_id(model_class, record_id, session: Session = None):
    """根据ID查询记录"""
    try:
        session = session or get_session()
        return session.query(model_class).filter_by(id=record_id).first()
    finally:
        close_session(session)


def _batch_save(session: Session, data_list: List[Any], model_class=None):
    """批量保存"""
    results = []
    for item in data_list:
        result = _single_save(session, item, model_class)
        results.append(result)
    return results


def _single_save(session: Session, data: Any, model_class=None):
    """单体保存"""
    # 处理字典数据
    if isinstance(data, dict):
        if model_class is None:
            raise ValueError("字典数据需要提供model_class参数")
        instance = model_class(**data)
        return _save_or_update(session, instance)

    # 处理模型对象
    elif hasattr(data, '__table__'):  # SQLAlchemy模型对象
        return _save_or_update(session, data)

    else:
        raise ValueError(f"不支持的数据类型: {type(data)}")


def _save_or_update(session: Session, instance: object):
    """根据主键判断执行保存还是更新"""
    # 获取模型的主键信息
    mapper = sqlalchemy_inspect(instance.__class__)
    primary_keys = [key.name for key in mapper.primary_key]

    # 检查是否有主键值
    has_primary_key_value = False
    for pk in primary_keys:
        if getattr(instance, pk, None) is not None:
            has_primary_key_value = True
            break

    if has_primary_key_value:
        # 主键存在，执行更新操作
        session.merge(instance)
    else:
        # 主键不存在，执行插入操作
        session.add(instance)

    return instance
