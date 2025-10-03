from sqlalchemy import Column, Integer, String, JSON

from sqllite import Base
from sqllite.sql_utils import get_session, save, query_by_id
from utils.json_utils import to_dict


class KeyConfigEntity(Base):
    __tablename__ = "key_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    type = Column(String(200), nullable=False)
    config_json = Column(JSON, nullable=False)


def save_key_config(entities: list[KeyConfigEntity]):
    """
    保存按键配置
    """
    session = get_session()
    save(session, entities, model_class=KeyConfigEntity)
    session.commit()
    session.close()


def query_key_configs(name: str = None, type: str = None):
    """
    查询按键配置
    """
    session = get_session()
    query_condition = session.query(KeyConfigEntity)
    if name:
        query_condition = query_condition.filter(KeyConfigEntity.name == name)
    if type:
        query_condition = query_condition.filter(KeyConfigEntity.type == type)
    result = query_condition.all()
    session.close()
    return to_dict(result)


def query_key_config_by_id(record_id: int):
    return query_by_id(KeyConfigEntity, record_id)
