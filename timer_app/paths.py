from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = APP_ROOT / "settings.json"
LOG_PATH = APP_ROOT / "timer.log"
PICKER_CACHE_PATH = APP_ROOT / "timer_items_cache.json"
