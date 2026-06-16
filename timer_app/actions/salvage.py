import time


def has_cursor_moved(expected_pos, current_pos, threshold_pixels):
    if expected_pos is None or current_pos is None:
        return False

    dx = abs(current_pos[0] - expected_pos[0])
    dy = abs(current_pos[1] - expected_pos[1])
    return dx > threshold_pixels or dy > threshold_pixels


def wait_while_mouse_button_held(
    seconds,
    stop_event=None,
    mouse_guard=False,
    cursor_moved=None,
    on_mouse_cancel=None,
):
    end_at = time.monotonic() + max(0, seconds)
    while time.monotonic() < end_at:
        if stop_event is not None and stop_event.is_set():
            return False
        if mouse_guard and cursor_moved is not None and cursor_moved():
            if on_mouse_cancel is not None:
                on_mouse_cancel()
            return False
        time.sleep(0.01)
    return True


def sleep_with_stop(
    seconds,
    stop_event,
    mouse_guard=False,
    cursor_moved=None,
    on_mouse_cancel=None,
):
    end_at = time.monotonic() + max(0, seconds)
    while time.monotonic() < end_at:
        if stop_event.is_set():
            return False
        if mouse_guard and cursor_moved is not None and cursor_moved():
            if on_mouse_cancel is not None:
                on_mouse_cancel()
            return False
        time.sleep(min(0.02, max(0, end_at - time.monotonic())))
    return not stop_event.is_set()


def remaining_cooldown_seconds(last_action_at, min_interval_seconds):
    since_last_action = time.monotonic() - last_action_at
    if since_last_action < min_interval_seconds:
        return min_interval_seconds - since_last_action
    return 0
