import json
from copy import deepcopy


DEFAULT_SETTINGS = {
    "test_mode": False,
    "test_alert_seconds": 0.5,
    "alert": {
        "start_seconds": 0,
        "end_seconds": -2,
        "update_ms": 16,
        "monitor_index": 2,
        "pulse_pattern": (
            ("rise", 0.070, 1.00),
            ("fall", 0.105, 1.00),
            ("off", 0.060, 0.00),
            ("rise", 0.050, 0.86),
            ("fall", 0.125, 0.86),
            ("off", 0.310, 0.00),
        ),
        "color": "#f0cf23",
        "min_alpha": 0.24,
        "max_alpha": 1.00,
        "primary_min_alpha": 0.28,
        "primary_max_alpha": 1.00,
        "primary_border_thickness": 42,
        "second_min_alpha": 0.30,
        "second_max_alpha": 1.00,
        "second_border_thickness": 30,
    },
    "notch": {
        "width": 100,
        "height": 24,
        "radius": 7,
        "font_pixels": 13,
        "normal_alpha": 0.21,
        "normal_bg": "#111111",
        "normal_fg": "#505050",
    },
    "picker": {
        "width": 860,
        "max_height": 760,
        "row_height": 42,
        "refresh_seconds": 30,
        "background_refresh_seconds": 10,
        "fast_refresh_attempts": 5,
        "fast_refresh_delay_seconds": 0.35,
        "empty_retry_attempts": 3,
        "empty_retry_delay_seconds": 0.22,
        "show_status": True,
        "status_alpha_color": "#56606b",
        "profile_refresh": True,
    },
    "game_search": {
        "window_y_offset_pixels": 16,
    },
    "game_actions": {
        "sell_confirm_hold_seconds": 1.0,
        "sell_step_delay_seconds": 0.050,
        "order_to_sell_delay_seconds": 0.12,
        "open_to_buy_delay_seconds": 0.20,
        "buy_to_quantity_delay_seconds": 0.12,
        "section_click_delay_seconds": 0.045,
        "salvage_item_row_step_ratio": 0.233,
        "salvage_confirm_hold_seconds": 0.564,
        "salvage_confirm_wait_seconds": 0.25,
        "salvage_after_confirm_seconds": 0.12,
        "salvage_step_delay_seconds": 0.035,
        "salvage_item_hover_delay_seconds": 0.03,
        "salvage_item_right_click_min_interval_seconds": 0.18,
        "salvage_post_right_click_delay_seconds": 0.08,
        "salvage_post_menu_click_delay_seconds": 0.08,
        "salvage_post_all_click_delay_seconds": 0.04,
        "salvage_mouse_cancel_threshold_pixels": 12,
        "picker_open_hold_seconds": 0.14,
        "picker_end_release_grace_seconds": 0.05,
        "right_arrow_hold_seconds": 0.09,
        "market_action_stage_max_age_seconds": 1.10,
        "right_shift_poll_seconds": 0.010,
    },
    "paste": {
        "before_click_delay": 0.002,
        "hover_before_click_delay": 0.010,
        "after_click_delay": 0.020,
        "after_clear_delay": 0.004,
        "between_keys_delay": 0.002,
        "before_enter_delay": 0.040,
        "enter_key_delay": 0.005,
        "search_clicks": 2,
        "mouse_click_delay": 0.003,
    },
}


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
