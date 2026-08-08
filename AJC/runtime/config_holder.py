# e.g. in AJC/runtime/config_holder.py  (new small file)
_RUNTIME_CONFIG: dict = {}

def set_runtime_config(cfg_dict: dict) -> None:
    global _RUNTIME_CONFIG
    _RUNTIME_CONFIG = cfg_dict

def get_runtime_config() -> dict:
    return _RUNTIME_CONFIG