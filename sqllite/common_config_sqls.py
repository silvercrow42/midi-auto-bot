from sqlalchemy import Column, Integer, String

from sqllite import Base
from sqllite.sql_utils import get_session, save


class CommonConfigEntity(Base):
    __tablename__ = "common_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String(200), nullable=False)
    config = Column(String(200), nullable=False)


def save_common_config(entities: list[CommonConfigEntity]):
    """
    保存通用配置
    """
    session = get_session()
    save(session, entities, model_class=CommonConfigEntity)
    session.commit()
    session.close()


def query_common_config(path: str = None):
    """
    查询通用配置
    """
    session = get_session()
    query_condition = session.query(CommonConfigEntity)
    if path:
        query_condition = query_condition.filter(CommonConfigEntity.path == path)
    result = query_condition.one()
    session.close()
    return result
