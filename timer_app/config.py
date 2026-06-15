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
        "window_x_ratio": 0.292,
        "window_y_ratio": 0.147,
        "window_y_offset_pixels": 16,
        "click_x_ratio": 0.245,
        "click_y_ratio": 0.170,
    },
    "game_actions": {
        "open_card_x_ratio": 0.540,
        "open_card_y_ratio": 0.281,
        "buy_button_x_ratio": 0.069,
        "buy_button_y_ratio": 0.904,
        "order_button_x_ratio": 0.515,
        "order_button_y_ratio": 0.653,
        "quantity_plus_x_ratio": 0.523,
        "quantity_plus_y_ratio": 0.512,
        "quantity_minus_x_ratio": 0.469,
        "quantity_minus_y_ratio": 0.512,
        "sell_button_x_ratio": 0.366927,
        "sell_button_y_ratio": 0.906944,
        "sell_price_click_x_ratio": 0.494792,
        "sell_price_click_y_ratio": 0.376389,
        "sell_all_button_x_ratio": 0.577604,
        "sell_all_button_y_ratio": 0.550926,
        "sell_confirm_button_x_ratio": 0.517448,
        "sell_confirm_button_y_ratio": 0.694444,
        "sell_confirm_hold_seconds": 1.0,
        "sell_step_delay_seconds": 0.050,
        "order_to_sell_delay_seconds": 0.12,
        "open_to_buy_delay_seconds": 0.20,
        "buy_to_quantity_delay_seconds": 0.12,
        "market_tab_x_ratio": 0.383,
        "market_tab_y_ratio": 0.033,
        "details_tab_x_ratio": 0.421,
        "details_tab_y_ratio": 0.088,
        "section_click_delay_seconds": 0.045,
        "salvage_storage_tab_x_ratio": 0.430729,
        "salvage_storage_tab_y_ratio": 0.036574,
        "salvage_details_tab_x_ratio": 0.327083,
        "salvage_details_tab_y_ratio": 0.083796,
        "salvage_pre_decor_category_x_ratio": 0.423958,
        "salvage_pre_decor_category_y_ratio": 0.168519,
        "salvage_decor_category_x_ratio": 0.341406,
        "salvage_decor_category_y_ratio": 0.168519,
        "salvage_sort_dropdown_x_ratio": 0.890365,
        "salvage_sort_dropdown_y_ratio": 0.169907,
        "salvage_sort_new_option_x_ratio": 0.876563,
        "salvage_sort_new_option_y_ratio": 0.435185,
        "salvage_sort_type_option_x_ratio": 0.877865,
        "salvage_sort_type_option_y_ratio": 0.215278,
        "salvage_first_item_x_ratio": 0.066927,
        "salvage_first_item_y_ratio": 0.319907,
        "salvage_select_item_x_ratio": 0.066927,
        "salvage_select_item_y_ratio": 0.319907,
        "salvage_item_row_step_ratio": 0.233,
        "salvage_context_disassemble_x_ratio": 0.059896,
        "salvage_context_disassemble_y_ratio": 0.606481,
        "salvage_all_button_x_ratio": 0.503646,
        "salvage_all_button_y_ratio": 0.471759,
        "salvage_confirm_button_x_ratio": 0.500260,
        "salvage_confirm_button_y_ratio": 0.680093,
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
