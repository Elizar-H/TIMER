import json
from copy import deepcopy


def merge_settings(defaults, overrides):
    if not isinstance(overrides, dict):
        return deepcopy(defaults)

    result = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_settings(result[key], value)
        else:
            result[key] = value
    return result


def load_settings(path, defaults):
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as settings_file:
                return merge_settings(defaults, json.load(settings_file))

        with path.open("w", encoding="utf-8") as settings_file:
            json.dump(defaults, settings_file, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return deepcopy(defaults)


def setting(settings, path, default=None):
    current = settings
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current
