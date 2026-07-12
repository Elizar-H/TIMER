"""Timer parsing, formatting and background refresh worker."""

from dataclasses import dataclass, field
import math
from queue import Queue
import re
import time


@dataclass
class TimerState:
    """Mutable timer values shared by the worker and UI updater."""

    queue: Queue = field(default_factory=Queue)
    base_seconds: float | None = None
    base_at: float | None = None
    remaining: float | None = None


def parse_timer(value):
    """Extracts the first one- or two-digit ``minutes:seconds`` value."""
    match = re.search(r"(\d{1,2}):(\d{2})", value)
    if not match:
        return "--:--", None

    minutes = int(match.group(1))
    seconds = int(match.group(2))
    return match.group(0), minutes * 60 + seconds


def format_seconds(seconds, show_milliseconds=True):
    """Formats seconds exactly as the current timer and Picker labels do."""
    safe_seconds = max(0, float(seconds))

    if show_milliseconds:
        minutes = int(safe_seconds // 60)
        whole_seconds = int(safe_seconds % 60)
        centiseconds = int((safe_seconds - int(safe_seconds)) * 100)
        return f"{minutes}:{whole_seconds:02d}.{centiseconds:02d}"

    display_seconds = max(0, math.ceil(safe_seconds))
    minutes = display_seconds // 60
    whole_seconds = display_seconds % 60
    return f"{minutes}:{whole_seconds:02d}"


def format_age(seconds):
    """Formats cache age using the current compact Russian suffixes."""
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}с"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}м"
    return f"{minutes // 60}ч"


def run_timer_worker(
    state,
    *,
    fetch_target_update,
    trigger_picker_fast_refresh,
    log_error,
    get_test_mode,
    get_test_alert_seconds,
    get_alert_start_seconds,
    get_alert_end_seconds,
    get_show_milliseconds=lambda: True,
    monotonic=time.monotonic,
    sleep=time.sleep,
):
    """Continuously fetches and publishes timer values for the UI thread.

    All application state and side effects are explicit dependencies.  The
    function intentionally remains an endless worker loop; the application can
    run it in the same daemon thread it uses today.
    """
    target_delta_ms = None
    fetched_at = monotonic()

    while True:
        if get_test_mode():
            seconds_left = get_test_alert_seconds()
            state.queue.put(
                (
                    format_seconds(
                        seconds_left,
                        show_milliseconds=get_show_milliseconds(),
                    ),
                    seconds_left,
                )
            )
            sleep(0.05)
            continue

        if target_delta_ms is None:
            try:
                target_delta_ms = fetch_target_update()
                if target_delta_ms is None:
                    raise ValueError("Timer timestamp not found")
                fetched_at = monotonic()
            except Exception as error:
                log_error("fetch", f"Timer fetch failed: {error}")
                state.queue.put("--:--")
                sleep(3)
                continue

        elapsed_ms = (monotonic() - fetched_at) * 1000
        seconds_left = (target_delta_ms - elapsed_ms) / 1000
        state.queue.put(
            (
                format_seconds(
                    seconds_left,
                    show_milliseconds=get_show_milliseconds(),
                ),
                seconds_left,
            )
        )

        alert_end_seconds = get_alert_end_seconds()
        if seconds_left <= alert_end_seconds:
            trigger_picker_fast_refresh()
            target_delta_ms = None
            sleep(1)
        else:
            in_alert_window = (
                alert_end_seconds
                < seconds_left
                <= get_alert_start_seconds()
            )
            sleep(0.05 if in_alert_window else 0.2)
