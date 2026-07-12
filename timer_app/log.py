from datetime import datetime
import threading
import time

from timer_app.paths import LOG_PATH


LOG_MAX_BYTES = 512 * 1024

_LOG_LOCK = threading.RLock()
last_log_times = {}


def rotate_log_if_needed():
    try:
        with _LOG_LOCK:
            if not LOG_PATH.exists() or LOG_PATH.stat().st_size <= LOG_MAX_BYTES:
                return

            LOG_PATH.unlink()
    except Exception:
        pass


def append_log_line(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with _LOG_LOCK:
            rotate_log_if_needed()
            with LOG_PATH.open("a", encoding="utf-8") as log_file:
                log_file.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def log_error(key, message):
    now = time.monotonic()
    with _LOG_LOCK:
        if now - last_log_times.get(key, 0) < 30:
            return

        last_log_times[key] = now
        append_log_line(message)
