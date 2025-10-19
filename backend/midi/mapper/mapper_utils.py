from backend.midi.mapper.deep_key_mapper import KeyboardMapper, mapping_matrix_to_json
from backend.sqllite.key_config_sqls import KeyConfigEntity


def apply_strategy(config_json):
    key_mapper = KeyboardMapper.from_json(config_json)
    key_mapper.apply_strategies()
    key_mapper_dict = key_mapper.to_dict()
    if key_mapper.remapping_matrix is not None:
        key_mapper_dict["remapping_matrix"] = mapping_matrix_to_json(key_mapper.remapping_matrix)
    return key_mapper_dict


def key_config_entity_to_dict(entity: KeyConfigEntity):
    return {
        "id": entity.id,
        "name": entity.name,
        "type": entity.type,
        "config_json": apply_strategy(entity.config_json)
    }
