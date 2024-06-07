from typing import Type
from .base_engine import TTSEngine

__all_engine_classes_dict__ = {}


def register_engine(engine_name: str, engine_class: Type[TTSEngine]):
    global __all_engine_classes_dict__
    __all_engine_classes_dict__[engine_name] = engine_class


def get_all_engine_names():
    global __all_engine_classes_dict__
    return list(__all_engine_classes_dict__.keys())


def create_engine(engine_name: str, config: dict) -> TTSEngine:
    global __all_engine_classes_dict__
    engine_class = __all_engine_classes_dict__.get(engine_name)
    if engine_class is None:
        raise ValueError(f"Unknown engine: {engine_name}")
    return engine_class(config)
