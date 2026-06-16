from datetime import datetime
import json

from timer_app.paths import PICKER_CACHE_PATH
from timer_app.picker.items import has_real_picker_items


CACHE_VERSION = 14


def load_picker_cache(path=PICKER_CACHE_PATH):
    try:
        with path.open("r", encoding="utf-8") as cache_file:
            data = json.load(cache_file)
    except Exception:
        return None

    items = data.get("items")
    if not isinstance(items, list):
        return None
    if data.get("version") != CACHE_VERSION:
        return None
    if not has_real_picker_items(items):
        return None

    age_seconds = 0
    saved_at = data.get("saved_at")
    if isinstance(saved_at, str):
        try:
            saved_dt = datetime.fromisoformat(saved_at)
            age_seconds = max(0, (datetime.now() - saved_dt).total_seconds())
        except Exception:
            pass

    return items, age_seconds


def save_picker_cache(items, path=PICKER_CACHE_PATH):
    if not has_real_picker_items(items):
        return

    with path.open("w", encoding="utf-8") as cache_file:
        json.dump(
            {
                "version": CACHE_VERSION,
                "saved_at": datetime.now().isoformat(timespec="seconds"),
                "items": items,
            },
            cache_file,
            ensure_ascii=False,
        )
