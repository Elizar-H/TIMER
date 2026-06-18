import ctypes
from ctypes import wintypes

import threading
import queue
import math
import os
from concurrent.futures import ThreadPoolExecutor
import re
import time
import tkinter as tk
import tkinter.font as tkfont
from timer_app.actions.market import (
    MarketActionState,
    STAGE_BUY,
    STAGE_OPEN_CARD,
    STAGE_OPENING_BUY_DIALOG,
    STAGE_OPENING_CARD,
    STAGE_QUANTITY,
)
from timer_app.actions.salvage import (
    has_cursor_moved,
    remaining_cooldown_seconds,
    sleep_with_stop as salvage_sleep_with_stop,
    wait_while_mouse_button_held,
)
from timer_app.config import DEFAULT_SETTINGS, load_settings, setting
from timer_app.coordinates import (
    DEFAULT_COORDINATES,
    apply_legacy_coordinate_settings,
    load_coordinates,
)
from timer_app.crossout import (
    FLASH_URL,
    RECYCLING_URL,
    build_flash_items,
    build_recycling_items,
    build_recycling_sale_prices,
    fetch_market_minutes,
    fetch_page_html,
    fetch_target_update,
    parse_crossout_data,
    read_crossoutcore_filters_cached,
)
from timer_app.game import GameActions
from timer_app.hotkeys import HotkeyWorker
from timer_app.log import append_log_line, log_error
from timer_app.overlays import (
    apply_window_region as apply_overlay_window_region,
    calculate_alert_pulse,
    configure_notch_dpi_sizes,
    configure_task_manager_app,
    create_monitor_alert_window,
    create_notch_items,
    get_pulse_alpha,
    set_canvas_items_fill,
    show_overlay_window,
)
from timer_app.paths import COORDINATES_PATH, SETTINGS_PATH
from timer_app.picker.cache import (
    load_picker_cache as load_picker_cache_file,
    save_picker_cache as save_picker_cache_file,
)
from timer_app.picker.items import (
    build_picker_display_rows as build_picker_display_rows_data,
    count_real_picker_items,
    format_picker_number,
    get_picker_canvas_row_at as get_picker_canvas_row_at_data,
    get_picker_item_cell_values,
    get_picker_item_kind,
    get_picker_item_row_indices as get_picker_item_row_indices_data,
    get_picker_rarity_color,
    get_price_for_rarity,
    get_rarity_style,
    has_real_picker_items,
)
from timer_app.picker.paste import normalize_game_search_text
from timer_app.winapi import (
    MOUSEEVENTF_LEFTDOWN,
    MOUSEEVENTF_LEFTUP,
    POINT,
    SWP_NOACTIVATE,
    SWP_NOMOVE,
    SWP_NOSIZE,
    SWP_SHOWWINDOW,
    SW_SHOWNOACTIVATE,
    VK_A,
    VK_BACK,
    VK_DELETE,
    VK_DOWN,
    VK_END,
    VK_ESCAPE,
    VK_RCONTROL,
    VK_RETURN,
    VK_RIGHT,
    VK_UP,
    VK_V,
    enable_dpi_awareness,
    get_cursor_pos,
    get_screen_pixel_rgb,
    hide_console,
    is_virtual_key_down,
    send_ctrl_key,
    send_mouse_button,
    send_mouse_click,
    send_mouse_right_click,
    tap_key,
    tap_key_scancode,
)
from timer_app.windows import (
    apply_no_activate,
    apply_no_focus_clickthrough,
    find_game_window,
    force_foreground_window,
    get_foreground_hwnd,
    get_hwnd_pixel_rgb,
    get_hwnd_ratio_point,
    get_hwnd_rect,
    get_primary_monitor_rect,
    get_second_monitor_rect,
    get_window_hwnd,
    get_window_info,
    get_window_process_path,
    is_game_foreground,
    is_game_window,
    is_live_game_window,
    is_live_window,
    is_window_on_primary_monitor,
    minimize_window,
    restore_game_window,
    show_tk_window_no_activate,
    show_tk_window_on_rect_no_activate,
)


# Настройки
APP_ID = "CrossoutCore.Timer"
INSTANCE_MUTEX_NAME = f"Local\\{APP_ID}.Singleton"
ERROR_ALREADY_EXISTS = 183
TEST_MODE = False
TEST_ALERT_SECONDS = 0.5
ALERT_START_SECONDS = 0
ALERT_END_SECONDS = -2
ALERT_PULSE_PATTERN = (
    ("rise", 0.070, 1.00),
    ("fall", 0.105, 1.00),
    ("off", 0.060, 0.00),
    ("rise", 0.050, 0.86),
    ("fall", 0.125, 0.86),
    ("off", 0.310, 0.00),
)
ALERT_UPDATE_MS = 16
SHOW_MILLISECONDS_ALWAYS = True
SHOW_NOTCH_OVERLAY = False
ALERT_MONITOR_INDEX = 2
PICKER_REFRESH_SECONDS = 30
PICKER_BACKGROUND_REFRESH_SECONDS = 10
PICKER_FAST_REFRESH_ATTEMPTS = 5
PICKER_FAST_REFRESH_DELAY_SECONDS = 0.35
PICKER_CACHE_MAX_AGE_SECONDS = 45
PICKER_WIDTH = 860
PICKER_MAX_HEIGHT = 760
PICKER_MIN_ROWS = 4
PICKER_LEFT_EXPAND_PIXELS = 70
PICKER_BOTTOM_MARGIN_PIXELS = 36
PICKER_TIMER_HEIGHT = 34
PICKER_ROW_HEIGHT = 42
PICKER_HEADER_HEIGHT = 30
PICKER_NAME_COL_WIDTH = 230
PICKER_FLASH_HISTORY_COL_WIDTH = 90
PICKER_FLASH_PRICE_COL_WIDTH = 82
PICKER_FLASH_ORDER_COL_WIDTH = 64
PICKER_FLASH_ROI_COL_WIDTH = 72
PICKER_PROFIT_COL_WIDTH = 92
PICKER_DECOR_NAME_COL_WIDTH = 440
PICKER_DECOR_VALUE_COL_WIDTH = 110
PICKER_GAME_SEARCH_GAP_PIXELS = 0
PICKER_GAME_SEARCH_Y_OFFSET_PIXELS = 16
GAME_SELL_CONFIRM_HOLD_SECONDS = 1.0
GAME_SELL_STEP_DELAY_SECONDS = 0.050
GAME_ORDER_TO_SELL_DELAY_SECONDS = 0.12
GAME_OPEN_TO_BUY_DELAY_SECONDS = 0.20
GAME_BUY_TO_QUANTITY_DELAY_SECONDS = 0.12
GAME_SECTION_CLICK_DELAY_SECONDS = 0.010
SALVAGE_ITEM_ROW_STEP_RATIO = 0.233
SALVAGE_CONFIRM_HOLD_SECONDS = 0.564
SALVAGE_CONFIRM_WAIT_SECONDS = 0.25
SALVAGE_CONFIRM_POLL_SECONDS = 0.01
SALVAGE_AFTER_CONFIRM_SECONDS = 0.12
SALVAGE_STEP_DELAY_SECONDS = 0.035
SALVAGE_ITEM_HOVER_DELAY_SECONDS = 0.03
SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS = 0.18
SALVAGE_POST_RIGHT_CLICK_DELAY_SECONDS = 0.08
SALVAGE_CONTEXT_PROBE_WAIT_SECONDS = 0.12
SALVAGE_CONTEXT_PROBE_POLL_SECONDS = 0.01
SALVAGE_POST_MENU_CLICK_DELAY_SECONDS = 0.0
SALVAGE_POST_ALL_CLICK_DELAY_SECONDS = 0.04
SALVAGE_MOUSE_CANCEL_THRESHOLD_PIXELS = 12
PICKER_OPEN_HOLD_SECONDS = 0.14
PICKER_END_RELEASE_GRACE_SECONDS = 0.05
RIGHT_ARROW_HOLD_SECONDS = 0.09
PICKER_ARROW_EDGE_HOLD_SECONDS = 0.20
MARKET_ACTION_STAGE_MAX_AGE_SECONDS = 1.10
MARKET_ORDER_COMPLETE_PROBE_WAIT_SECONDS = 2.0
MARKET_ORDER_COMPLETE_PROBE_POLL_SECONDS = 0.005
MARKET_ORDER_COMPLETE_ORANGE_RGB = (0xB5, 0x4A, 0x03)
MARKET_ORDER_COMPLETE_ORANGE_TOLERANCE = 45
MARKET_ORDER_COMPLETE_ESC_REPEAT_DELAY_SECONDS = 0.020
MARKET_TAB_ACTIVE_RGB = (0xFF, 0x99, 0x00)
MARKET_TAB_ACTIVE_TOLERANCE = 55
MARKET_SUBTAB_DETAILS = "details"
MARKET_SUBTAB_LOTS = "lots"
GAME_BUTTON_SAMPLE_OFFSETS = (
    (-70, -10),
    (-45, 12),
    (-25, 18),
    (25, 18),
    (45, 12),
    (70, -10),
)
GAME_BUTTON_SAMPLE_REQUIRED_HITS = 1
GAME_BUTTON_ORANGE_MIN_R = 110
GAME_BUTTON_ORANGE_MIN_G = 35
GAME_BUTTON_ORANGE_MAX_B = 80
GAME_BUTTON_ORANGE_MIN_RG_DIFF = 20
WHITE_PIXEL_MIN_CHANNEL = 220
WHITE_PIXEL_MAX_CHANNEL_SPREAD = 35
WHITE_PIXEL_SAMPLE_OFFSETS = (
    (0, 0),
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
)
SALVAGE_CONTEXT_DISASSEMBLE_CHOICES = (
    (
        "salvage.context_disassemble_probe_top",
        "salvage.context_disassemble_option_top",
    ),
    (
        "salvage.context_disassemble_probe_bottom",
        "salvage.context_disassemble_option_bottom",
    ),
)
RIGHT_SHIFT_POLL_SECONDS = 0.010
# Скорость вставки. Если игра иногда не успевает сфокусировать поле, увеличь PASTE_AFTER_CLICK_DELAY до 0.03-0.05.
PASTE_BEFORE_CLICK_DELAY = 0.002
PASTE_HOVER_BEFORE_CLICK_DELAY = 0.010
PASTE_AFTER_CLICK_DELAY = 0.020
PASTE_AFTER_CLEAR_DELAY = 0.004
PASTE_BETWEEN_KEYS_DELAY = 0.002
PASTE_BEFORE_ENTER_DELAY = 0.040
PASTE_ENTER_KEY_DELAY = 0.005
PASTE_SEARCH_CLICKS = 2
MOUSE_CLICK_DELAY = 0.003
ITEM_PICKER_TITLE = "Crossout Item Picker"
# Вид основной "челки"
BASE_NOTCH_WIDTH = 100
BASE_NOTCH_HEIGHT = 24
BASE_NOTCH_RADIUS = 7
BASE_FONT_PIXELS = 13
GAME_WINDOW_KEYWORDS = ("crossout",)
TRANSPARENT_BG = "#ff00ff"
NORMAL_BG = "#111111"
NORMAL_FG = "#505050"
NORMAL_ALPHA = 0.21
ALERT_BG = "#f0cf23"
ALERT_FG = "#111111"
ALERT_MIN_ALPHA = 0.24
ALERT_ALPHA = 1.00
PRIMARY_MONITOR_MIN_ALPHA = 0.28
PRIMARY_MONITOR_ALPHA = 1.00
PRIMARY_MONITOR_BORDER_THICKNESS = 42
SECOND_MONITOR_MIN_ALPHA = 0.30
SECOND_MONITOR_ALPHA = 1.00
SECOND_MONITOR_BORDER_THICKNESS = 30
PICKER_EMPTY_RETRY_ATTEMPTS = 3
PICKER_EMPTY_RETRY_DELAY_SECONDS = 0.22
PICKER_SHOW_STATUS = True
PICKER_STATUS_FG = "#56606b"
PICKER_PROFILE_REFRESH = True

game = GameActions(
    DEFAULT_COORDINATES,
    get_action_hwnd=lambda: get_picker_action_hwnd(),
    get_hover_delay=lambda: PASTE_HOVER_BEFORE_CLICK_DELAY,
    get_mouse_click_delay=lambda: MOUSE_CLICK_DELAY,
    send_click=send_mouse_click,
    send_right_click=send_mouse_right_click,
    hold_left_mouse=lambda seconds, stop_event=None, mouse_guard=False: hold_left_mouse(
        seconds,
        stop_event=stop_event,
        mouse_guard=mouse_guard,
    ),
)


def apply_settings():
    global TEST_MODE, TEST_ALERT_SECONDS, ALERT_START_SECONDS, ALERT_END_SECONDS
    global ALERT_UPDATE_MS, ALERT_MONITOR_INDEX, ALERT_PULSE_PATTERN
    global BASE_NOTCH_WIDTH, BASE_NOTCH_HEIGHT, BASE_NOTCH_RADIUS, BASE_FONT_PIXELS
    global NORMAL_BG, NORMAL_FG, NORMAL_ALPHA, ALERT_BG, ALERT_MIN_ALPHA, ALERT_ALPHA
    global PRIMARY_MONITOR_MIN_ALPHA, PRIMARY_MONITOR_ALPHA, PRIMARY_MONITOR_BORDER_THICKNESS
    global SECOND_MONITOR_MIN_ALPHA, SECOND_MONITOR_ALPHA, SECOND_MONITOR_BORDER_THICKNESS
    global PICKER_WIDTH, PICKER_MAX_HEIGHT, PICKER_ROW_HEIGHT
    global PICKER_REFRESH_SECONDS, PICKER_BACKGROUND_REFRESH_SECONDS
    global PICKER_FAST_REFRESH_ATTEMPTS, PICKER_FAST_REFRESH_DELAY_SECONDS
    global PICKER_EMPTY_RETRY_ATTEMPTS, PICKER_EMPTY_RETRY_DELAY_SECONDS
    global PICKER_SHOW_STATUS, PICKER_STATUS_FG, PICKER_PROFILE_REFRESH
    global PICKER_GAME_SEARCH_Y_OFFSET_PIXELS
    global GAME_SELL_CONFIRM_HOLD_SECONDS, GAME_SELL_STEP_DELAY_SECONDS
    global GAME_ORDER_TO_SELL_DELAY_SECONDS
    global GAME_OPEN_TO_BUY_DELAY_SECONDS, GAME_BUY_TO_QUANTITY_DELAY_SECONDS
    global GAME_SECTION_CLICK_DELAY_SECONDS, PICKER_OPEN_HOLD_SECONDS
    global SALVAGE_ITEM_ROW_STEP_RATIO
    global SALVAGE_CONFIRM_HOLD_SECONDS, SALVAGE_CONFIRM_WAIT_SECONDS
    global SALVAGE_AFTER_CONFIRM_SECONDS, SALVAGE_STEP_DELAY_SECONDS
    global SALVAGE_ITEM_HOVER_DELAY_SECONDS, SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS
    global SALVAGE_POST_RIGHT_CLICK_DELAY_SECONDS
    global SALVAGE_CONTEXT_PROBE_WAIT_SECONDS, SALVAGE_CONTEXT_PROBE_POLL_SECONDS
    global SALVAGE_POST_MENU_CLICK_DELAY_SECONDS, SALVAGE_POST_ALL_CLICK_DELAY_SECONDS
    global SALVAGE_MOUSE_CANCEL_THRESHOLD_PIXELS
    global PICKER_END_RELEASE_GRACE_SECONDS
    global RIGHT_ARROW_HOLD_SECONDS
    global MARKET_ACTION_STAGE_MAX_AGE_SECONDS
    global RIGHT_SHIFT_POLL_SECONDS
    global PASTE_BEFORE_CLICK_DELAY, PASTE_HOVER_BEFORE_CLICK_DELAY
    global PASTE_AFTER_CLICK_DELAY, PASTE_AFTER_CLEAR_DELAY, PASTE_BETWEEN_KEYS_DELAY
    global PASTE_BEFORE_ENTER_DELAY, PASTE_ENTER_KEY_DELAY, PASTE_SEARCH_CLICKS
    global MOUSE_CLICK_DELAY

    settings = load_settings(SETTINGS_PATH, DEFAULT_SETTINGS)
    coordinates = apply_legacy_coordinate_settings(
        load_coordinates(COORDINATES_PATH, DEFAULT_COORDINATES),
        SETTINGS_PATH,
    )
    game.set_coordinates(coordinates)
    TEST_MODE = bool(setting(settings, "test_mode", TEST_MODE))
    TEST_ALERT_SECONDS = float(setting(settings, "test_alert_seconds", TEST_ALERT_SECONDS))
    ALERT_START_SECONDS = float(setting(settings, "alert.start_seconds", ALERT_START_SECONDS))
    ALERT_END_SECONDS = float(setting(settings, "alert.end_seconds", ALERT_END_SECONDS))
    ALERT_UPDATE_MS = int(setting(settings, "alert.update_ms", ALERT_UPDATE_MS))
    ALERT_MONITOR_INDEX = int(setting(settings, "alert.monitor_index", ALERT_MONITOR_INDEX))
    ALERT_PULSE_PATTERN = tuple(
        tuple(item) for item in setting(settings, "alert.pulse_pattern", ALERT_PULSE_PATTERN)
    )
    ALERT_BG = str(setting(settings, "alert.color", ALERT_BG))
    ALERT_MIN_ALPHA = float(setting(settings, "alert.min_alpha", ALERT_MIN_ALPHA))
    ALERT_ALPHA = float(setting(settings, "alert.max_alpha", ALERT_ALPHA))
    PRIMARY_MONITOR_MIN_ALPHA = float(
        setting(settings, "alert.primary_min_alpha", PRIMARY_MONITOR_MIN_ALPHA)
    )
    PRIMARY_MONITOR_ALPHA = float(setting(settings, "alert.primary_max_alpha", PRIMARY_MONITOR_ALPHA))
    PRIMARY_MONITOR_BORDER_THICKNESS = int(
        setting(settings, "alert.primary_border_thickness", PRIMARY_MONITOR_BORDER_THICKNESS)
    )
    SECOND_MONITOR_MIN_ALPHA = float(
        setting(settings, "alert.second_min_alpha", SECOND_MONITOR_MIN_ALPHA)
    )
    SECOND_MONITOR_ALPHA = float(setting(settings, "alert.second_max_alpha", SECOND_MONITOR_ALPHA))
    SECOND_MONITOR_BORDER_THICKNESS = int(
        setting(settings, "alert.second_border_thickness", SECOND_MONITOR_BORDER_THICKNESS)
    )

    BASE_NOTCH_WIDTH = int(setting(settings, "notch.width", BASE_NOTCH_WIDTH))
    BASE_NOTCH_HEIGHT = int(setting(settings, "notch.height", BASE_NOTCH_HEIGHT))
    BASE_NOTCH_RADIUS = int(setting(settings, "notch.radius", BASE_NOTCH_RADIUS))
    BASE_FONT_PIXELS = int(setting(settings, "notch.font_pixels", BASE_FONT_PIXELS))
    NORMAL_ALPHA = float(setting(settings, "notch.normal_alpha", NORMAL_ALPHA))
    NORMAL_BG = str(setting(settings, "notch.normal_bg", NORMAL_BG))
    NORMAL_FG = str(setting(settings, "notch.normal_fg", NORMAL_FG))

    PICKER_WIDTH = int(setting(settings, "picker.width", PICKER_WIDTH))
    PICKER_MAX_HEIGHT = int(setting(settings, "picker.max_height", PICKER_MAX_HEIGHT))
    PICKER_ROW_HEIGHT = int(setting(settings, "picker.row_height", PICKER_ROW_HEIGHT))
    PICKER_REFRESH_SECONDS = float(setting(settings, "picker.refresh_seconds", PICKER_REFRESH_SECONDS))
    PICKER_BACKGROUND_REFRESH_SECONDS = float(
        setting(settings, "picker.background_refresh_seconds", PICKER_BACKGROUND_REFRESH_SECONDS)
    )
    PICKER_FAST_REFRESH_ATTEMPTS = int(
        setting(settings, "picker.fast_refresh_attempts", PICKER_FAST_REFRESH_ATTEMPTS)
    )
    PICKER_FAST_REFRESH_DELAY_SECONDS = float(
        setting(settings, "picker.fast_refresh_delay_seconds", PICKER_FAST_REFRESH_DELAY_SECONDS)
    )
    PICKER_EMPTY_RETRY_ATTEMPTS = int(
        setting(settings, "picker.empty_retry_attempts", PICKER_EMPTY_RETRY_ATTEMPTS)
    )
    PICKER_EMPTY_RETRY_DELAY_SECONDS = float(
        setting(settings, "picker.empty_retry_delay_seconds", PICKER_EMPTY_RETRY_DELAY_SECONDS)
    )
    PICKER_SHOW_STATUS = bool(setting(settings, "picker.show_status", PICKER_SHOW_STATUS))
    PICKER_STATUS_FG = str(setting(settings, "picker.status_alpha_color", PICKER_STATUS_FG))
    PICKER_PROFILE_REFRESH = bool(setting(settings, "picker.profile_refresh", PICKER_PROFILE_REFRESH))

    PICKER_GAME_SEARCH_Y_OFFSET_PIXELS = int(
        setting(settings, "game_search.window_y_offset_pixels", PICKER_GAME_SEARCH_Y_OFFSET_PIXELS)
    )
    GAME_SELL_CONFIRM_HOLD_SECONDS = float(
        setting(settings, "game_actions.sell_confirm_hold_seconds", GAME_SELL_CONFIRM_HOLD_SECONDS)
    )
    GAME_SELL_STEP_DELAY_SECONDS = float(
        setting(settings, "game_actions.sell_step_delay_seconds", GAME_SELL_STEP_DELAY_SECONDS)
    )
    GAME_ORDER_TO_SELL_DELAY_SECONDS = float(
        setting(settings, "game_actions.order_to_sell_delay_seconds", GAME_ORDER_TO_SELL_DELAY_SECONDS)
    )
    GAME_OPEN_TO_BUY_DELAY_SECONDS = float(
        setting(settings, "game_actions.open_to_buy_delay_seconds", GAME_OPEN_TO_BUY_DELAY_SECONDS)
    )
    GAME_BUY_TO_QUANTITY_DELAY_SECONDS = float(
        setting(settings, "game_actions.buy_to_quantity_delay_seconds", GAME_BUY_TO_QUANTITY_DELAY_SECONDS)
    )
    GAME_SECTION_CLICK_DELAY_SECONDS = float(
        setting(settings, "game_actions.section_click_delay_seconds", GAME_SECTION_CLICK_DELAY_SECONDS)
    )
    SALVAGE_ITEM_ROW_STEP_RATIO = float(
        setting(settings, "game_actions.salvage_item_row_step_ratio", SALVAGE_ITEM_ROW_STEP_RATIO)
    )
    SALVAGE_CONFIRM_HOLD_SECONDS = float(
        setting(settings, "game_actions.salvage_confirm_hold_seconds", SALVAGE_CONFIRM_HOLD_SECONDS)
    )
    SALVAGE_CONFIRM_WAIT_SECONDS = float(
        setting(settings, "game_actions.salvage_confirm_wait_seconds", SALVAGE_CONFIRM_WAIT_SECONDS)
    )
    SALVAGE_AFTER_CONFIRM_SECONDS = float(
        setting(settings, "game_actions.salvage_after_confirm_seconds", SALVAGE_AFTER_CONFIRM_SECONDS)
    )
    SALVAGE_STEP_DELAY_SECONDS = float(
        setting(settings, "game_actions.salvage_step_delay_seconds", SALVAGE_STEP_DELAY_SECONDS)
    )
    SALVAGE_ITEM_HOVER_DELAY_SECONDS = float(
        setting(
            settings,
            "game_actions.salvage_item_hover_delay_seconds",
            SALVAGE_ITEM_HOVER_DELAY_SECONDS,
        )
    )
    SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS = float(
        setting(
            settings,
            "game_actions.salvage_item_right_click_min_interval_seconds",
            SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS,
        )
    )
    SALVAGE_POST_RIGHT_CLICK_DELAY_SECONDS = float(
        setting(
            settings,
            "game_actions.salvage_post_right_click_delay_seconds",
            SALVAGE_POST_RIGHT_CLICK_DELAY_SECONDS,
        )
    )
    SALVAGE_CONTEXT_PROBE_WAIT_SECONDS = float(
        setting(
            settings,
            "game_actions.salvage_context_probe_wait_seconds",
            SALVAGE_CONTEXT_PROBE_WAIT_SECONDS,
        )
    )
    SALVAGE_CONTEXT_PROBE_POLL_SECONDS = float(
        setting(
            settings,
            "game_actions.salvage_context_probe_poll_seconds",
            SALVAGE_CONTEXT_PROBE_POLL_SECONDS,
        )
    )
    SALVAGE_POST_MENU_CLICK_DELAY_SECONDS = float(
        setting(
            settings,
            "game_actions.salvage_post_menu_click_delay_seconds",
            SALVAGE_POST_MENU_CLICK_DELAY_SECONDS,
        )
    )
    SALVAGE_POST_ALL_CLICK_DELAY_SECONDS = float(
        setting(
            settings,
            "game_actions.salvage_post_all_click_delay_seconds",
            SALVAGE_POST_ALL_CLICK_DELAY_SECONDS,
        )
    )
    SALVAGE_MOUSE_CANCEL_THRESHOLD_PIXELS = int(
        setting(
            settings,
            "game_actions.salvage_mouse_cancel_threshold_pixels",
            SALVAGE_MOUSE_CANCEL_THRESHOLD_PIXELS,
        )
    )
    PICKER_OPEN_HOLD_SECONDS = float(
        setting(settings, "game_actions.picker_open_hold_seconds", PICKER_OPEN_HOLD_SECONDS)
    )
    PICKER_END_RELEASE_GRACE_SECONDS = float(
        setting(
            settings,
            "game_actions.picker_end_release_grace_seconds",
            PICKER_END_RELEASE_GRACE_SECONDS,
        )
    )
    RIGHT_ARROW_HOLD_SECONDS = float(
        setting(settings, "game_actions.right_arrow_hold_seconds", RIGHT_ARROW_HOLD_SECONDS)
    )
    MARKET_ACTION_STAGE_MAX_AGE_SECONDS = float(
        setting(
            settings,
            "game_actions.market_action_stage_max_age_seconds",
            MARKET_ACTION_STAGE_MAX_AGE_SECONDS,
        )
    )
    RIGHT_SHIFT_POLL_SECONDS = float(
        setting(settings, "game_actions.right_shift_poll_seconds", RIGHT_SHIFT_POLL_SECONDS)
    )

    PASTE_BEFORE_CLICK_DELAY = float(setting(settings, "paste.before_click_delay", PASTE_BEFORE_CLICK_DELAY))
    PASTE_HOVER_BEFORE_CLICK_DELAY = float(
        setting(settings, "paste.hover_before_click_delay", PASTE_HOVER_BEFORE_CLICK_DELAY)
    )
    PASTE_AFTER_CLICK_DELAY = float(setting(settings, "paste.after_click_delay", PASTE_AFTER_CLICK_DELAY))
    PASTE_AFTER_CLEAR_DELAY = float(setting(settings, "paste.after_clear_delay", PASTE_AFTER_CLEAR_DELAY))
    PASTE_BETWEEN_KEYS_DELAY = float(setting(settings, "paste.between_keys_delay", PASTE_BETWEEN_KEYS_DELAY))
    PASTE_BEFORE_ENTER_DELAY = float(setting(settings, "paste.before_enter_delay", PASTE_BEFORE_ENTER_DELAY))
    PASTE_ENTER_KEY_DELAY = float(setting(settings, "paste.enter_key_delay", PASTE_ENTER_KEY_DELAY))
    PASTE_SEARCH_CLICKS = int(setting(settings, "paste.search_clicks", PASTE_SEARCH_CLICKS))
    MOUSE_CLICK_DELAY = float(setting(settings, "paste.mouse_click_delay", MOUSE_CLICK_DELAY))


apply_settings()

q = queue.Queue()
hotkeys = HotkeyWorker(log_error)
root = None
canvas = None
timer_text = None
remaining_seconds = None
timer_base_seconds = None
timer_base_at = None
notch_items = []
alert_strip = None
primary_monitor_alert = None
primary_monitor_canvas = None
primary_monitor_border_items = []
primary_monitor_rect = None
second_monitor_alert = None
second_monitor_canvas = None
second_monitor_border_items = []
second_monitor_rect = None
picker_items = []
picker_window = None
picker_hwnd = None
picker_canvas = None
picker_canvas_window = None
picker_inner = None
picker_status = None
picker_timer_label = None
picker_status_label = None
picker_target_hwnd = None
picker_display_rows = []
picker_total_content_height = 0
picker_hover_row_index = None
picker_selected_row_index = None
picker_pending_row_index = None
picker_pending_selection_token = 0
picker_font_cache = {}
picker_columns_cache = {}
picker_current_width = PICKER_WIDTH
picker_last_refresh = 0
picker_last_success_at = None
picker_last_refresh_ms = None
picker_last_item_count = 0
picker_last_refresh_note = "кэш"
picker_refresh_lock = threading.Lock()
picker_fast_refresh_lock = threading.Lock()
picker_refreshing = False
picker_actions_enabled = False
right_shift_order_down = False
right_ctrl_was_down = False
right_arrow_was_down = False
right_arrow_press_at = 0
right_arrow_hold_active = False
right_arrow_hold_compensated = False
right_arrow_last_action_stage = None
market_order_complete_probe_running = False
market_order_complete_probe_lock = threading.Lock()
market_order_complete_probe_done = threading.Event()
market_order_complete_probe_done.set()
market_current_subtab = MARKET_SUBTAB_DETAILS
up_arrow_was_down = False
up_arrow_press_at = 0
up_arrow_hold_triggered = False
down_arrow_was_down = False
down_arrow_press_at = 0
down_arrow_hold_triggered = False
picker_end_hold_pending = False
picker_end_hold_consumed = False
picker_end_press_active = False
picker_end_press_was_open = False
picker_end_started_in_game = False
picker_end_hold_triggered = False
picker_end_background_hold_triggered = False
picker_end_latched = False
picker_end_press_at = 0
picker_end_ignore_until = 0
picker_end_previous_hwnd = 0
salvage_running = False
salvage_stop_event = threading.Event()
salvage_expected_cursor_pos = None
salvage_last_item_right_click_at = 0
salvage_delete_was_down = False
salvage_last_delete_handled_at = 0
salvage_pair_armed = False
salvage_cleanup_requested = False
salvage_restart_after_stop = False
salvage_arm_after_restart = False
salvage_finish_current_cycle_requested = False
salvage_action_hwnd = 0
salvage_pair_hwnd = 0
market_action_state = MarketActionState(MARKET_ACTION_STAGE_MAX_AGE_SECONDS)
picker_render_signature = None
last_picker_paste_at = 0
last_picker_paste_name = None
last_alert_context_hwnd = None
single_instance_mutex = None
overlay_width = BASE_NOTCH_WIDTH
notch_x = 0
notch_width = BASE_NOTCH_WIDTH
notch_height = BASE_NOTCH_HEIGHT
notch_radius = BASE_NOTCH_RADIUS
font_pixels = BASE_FONT_PIXELS

TODO_EXTRACT_LATER = (
    "clear_dead_picker_targets",
    "close_picker_if_target_gone",
    "is_own_overlay_hwnd",
    "is_picker_open",
    "is_picker_window_visible_fast",
    "get_alert_context_hwnd",
    "get_or_restore_game_hwnd",
    "keep_picker_on_top",
    "keep_on_top",
)


def acquire_single_instance():
    global single_instance_mutex

    try:
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, INSTANCE_MUTEX_NAME)
        if not mutex:
            return

        single_instance_mutex = mutex
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            os._exit(0)
    except Exception as e:
        log_error("single_instance", f"Single instance guard failed: {e}")


def parse_timer(value):
    match = re.search(r"(\d{1,2}):(\d{2})", value)
    if not match:
        return "--:--", None

    minutes = int(match.group(1))
    seconds = int(match.group(2))
    return match.group(0), minutes * 60 + seconds


def is_alert_window(seconds):
    return seconds is not None and ALERT_END_SECONDS < seconds <= ALERT_START_SECONDS


def format_seconds(seconds):
    safe_seconds = max(0, float(seconds))

    if SHOW_MILLISECONDS_ALWAYS:
        minutes = int(safe_seconds // 60)
        whole_seconds = int(safe_seconds % 60)
        centiseconds = int((safe_seconds - int(safe_seconds)) * 100)
        return f"{minutes}:{whole_seconds:02d}.{centiseconds:02d}"

    display_seconds = max(0, math.ceil(safe_seconds))
    minutes = display_seconds // 60
    whole_seconds = display_seconds % 60
    return f"{minutes}:{whole_seconds:02d}"


def format_age(seconds):
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}с"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}м"
    return f"{minutes // 60}ч"


def get_picker_status_text():
    if not PICKER_SHOW_STATUS:
        return ""

    if picker_refreshing:
        return "обновляю..."

    if picker_last_success_at is None:
        return picker_last_refresh_note

    age = format_age(time.monotonic() - picker_last_success_at)
    timing = f"{int(picker_last_refresh_ms)}мс" if picker_last_refresh_ms is not None else "--"
    return f"{picker_last_item_count} · {age} · {timing}"


def update_picker_timer_label():
    if picker_timer_label is None:
        return

    if remaining_seconds is None:
        text = "До обновления: --:--"
    else:
        text = f"До обновления: {format_seconds(remaining_seconds)}"

    picker_timer_label.configure(text=text)
    if picker_status_label is not None:
        picker_status_label.configure(text=get_picker_status_text())


def timed_call(label, timings, func, *args):
    started = time.perf_counter()
    try:
        return func(*args)
    finally:
        timings[label] = (time.perf_counter() - started) * 1000


def fetch_picker_sources():
    timings = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        flash_future = executor.submit(timed_call, "flash_fetch_ms", timings, fetch_page_html, FLASH_URL)
        recycling_future = executor.submit(
            timed_call,
            "recycling_fetch_ms",
            timings,
            fetch_page_html,
            RECYCLING_URL,
        )
        market_minutes_future = executor.submit(
            timed_call,
            "minutes_fetch_ms",
            timings,
            fetch_market_minutes,
        )

        filters_started = time.perf_counter()
        filters = read_crossoutcore_filters_cached()
        timings["filters_ms"] = (time.perf_counter() - filters_started) * 1000
        flash_html = flash_future.result()

        try:
            recycling_html = recycling_future.result()
        except Exception as e:
            log_error("picker_recycling_fetch", f"Recycling page fetch failed: {e}")
            recycling_html = None

        try:
            market_minutes = market_minutes_future.result()
        except Exception as e:
            log_error("picker_market_minutes_fetch", f"Market minutes fetch failed: {e}")
            market_minutes = {}

    return filters, flash_html, recycling_html, market_minutes, timings


def parse_market_source(source_name, html):
    items_by_id, market_data = parse_crossout_data(html)
    if not items_by_id or not market_data:
        raise ValueError(f"No {source_name} data parsed")
    return items_by_id, market_data


def merge_market_sources(primary_items, primary_market, secondary_items, secondary_market):
    merged_items = dict(primary_items)
    merged_items.update(secondary_items)

    merged_market = dict(primary_market)
    merged_market.update(secondary_market)

    return merged_items, merged_market


def log_picker_performance(timings, result):
    if not PICKER_PROFILE_REFRESH:
        return

    parts = [
        f"total={timings.get('total_ms', 0):.0f}ms",
        f"flash={timings.get('flash_fetch_ms', 0):.0f}ms",
        f"recycling={timings.get('recycling_fetch_ms', 0):.0f}ms",
        f"minutes={timings.get('minutes_fetch_ms', 0):.0f}ms",
        f"filters={timings.get('filters_ms', 0):.0f}ms",
        f"build={timings.get('build_ms', 0):.0f}ms",
        f"items={count_real_picker_items(result)}",
    ]
    append_log_line("picker_refresh " + " ".join(parts))


def build_picker_items():
    build_started = time.perf_counter()
    filters, flash_html, recycling_html, market_minutes, timings = fetch_picker_sources()
    parse_started = time.perf_counter()
    items_by_id, market_data = parse_market_source("flash", flash_html)
    timings["parse_flash_ms"] = (time.perf_counter() - parse_started) * 1000

    try:
        if recycling_html is None:
            raise ValueError("Recycling page was not fetched")
        parse_started = time.perf_counter()
        recycling_items_by_id, recycling_market_data = parse_market_source(
            "recycling",
            recycling_html,
        )
        timings["parse_recycling_ms"] = (time.perf_counter() - parse_started) * 1000
    except Exception as e:
        log_error("picker_recycling_parse", f"Recycling page parse failed: {e}")
        recycling_items_by_id = items_by_id
        recycling_market_data = market_data

    merged_recycling_items_by_id, merged_recycling_market_data = merge_market_sources(
        items_by_id,
        market_data,
        recycling_items_by_id,
        recycling_market_data,
    )

    items_started = time.perf_counter()
    flash_items = build_flash_items(items_by_id, market_data, market_minutes, filters)
    decor_items = build_recycling_items(
        merged_recycling_items_by_id,
        merged_recycling_market_data,
        filters,
    )

    decor_sale_prices = build_recycling_sale_prices(
        merged_recycling_market_data,
        filters["recycling_rarities"],
    )
    timings["build_ms"] = (time.perf_counter() - items_started) * 1000

    result = (
        flash_items
        + ([{"separator": True, "section": "Декор"}] if decor_items else [])
        + ([{"decor_prices": True, "prices": decor_sale_prices}] if decor_items else [])
        + decor_items
    )
    if not has_real_picker_items(result):
        result = [{"separator": True, "section": "Предметы не найдены"}]

    timings["total_ms"] = (time.perf_counter() - build_started) * 1000
    log_picker_performance(timings, result)
    return result, timings


def build_picker_items_with_retries():
    last_items = []
    last_timings = {}
    attempts = max(1, PICKER_EMPTY_RETRY_ATTEMPTS)

    for attempt in range(attempts):
        items, timings = build_picker_items()
        last_items = items
        last_timings = timings
        if has_real_picker_items(items):
            return items, timings, None

        if attempt + 1 < attempts:
            time.sleep(PICKER_EMPTY_RETRY_DELAY_SECONDS)

    return last_items, last_timings, "empty"


def refresh_picker_items(force=False):
    global picker_items, picker_last_refresh, picker_refreshing
    global picker_last_success_at, picker_last_refresh_ms, picker_last_item_count
    global picker_last_refresh_note

    now = time.monotonic()
    if not force and picker_items and now - picker_last_refresh < PICKER_REFRESH_SECONDS:
        return

    if not picker_refresh_lock.acquire(blocking=False):
        return

    picker_refreshing = True
    if root is not None:
        root.after(0, update_picker_timer_label)
    try:
        fresh_items, timings, warning = build_picker_items_with_retries()
        if warning and has_real_picker_items(picker_items):
            picker_last_refresh_note = "сайт пусто"
            return

        picker_items = fresh_items
        picker_last_refresh = now
        picker_last_refresh_ms = timings.get("total_ms")
        picker_last_item_count = count_real_picker_items(fresh_items)
        if has_real_picker_items(fresh_items):
            picker_last_success_at = time.monotonic()
            picker_last_refresh_note = "свежие"
            save_picker_cache()
        else:
            picker_last_refresh_note = "нет данных"
    except Exception as e:
        log_error("picker_fetch", f"Picker item fetch failed: {e}")
        picker_last_refresh_note = "ошибка"
        if not has_real_picker_items(picker_items):
            picker_items = [{"separator": True, "section": "Не удалось загрузить предметы"}]
    finally:
        picker_refreshing = False
        if root is not None:
            root.after(0, update_picker_timer_label)
        picker_refresh_lock.release()


def load_picker_cache():
    global picker_items, picker_last_refresh, picker_last_success_at, picker_last_item_count
    global picker_last_refresh_note

    cached = load_picker_cache_file()
    if cached is None:
        return

    items, age_seconds = cached
    picker_items = items
    picker_last_refresh = time.monotonic() - age_seconds
    picker_last_success_at = time.monotonic() - age_seconds
    picker_last_item_count = count_real_picker_items(items)
    picker_last_refresh_note = "кэш"


def save_picker_cache():
    if not has_real_picker_items(picker_items):
        return

    try:
        save_picker_cache_file(picker_items)
    except Exception as e:
        log_error("picker_cache", f"Picker cache save failed: {e}")


def repaint_picker_if_visible():
    if picker_window is not None:
        populate_picker()


def refresh_picker_and_repaint(force=False):
    refresh_picker_items(force=force)
    root.after(0, repaint_picker_if_visible)


def picker_refresh_worker():
    while True:
        refresh_picker_and_repaint(force=True)
        time.sleep(PICKER_BACKGROUND_REFRESH_SECONDS)


def picker_fast_refresh_worker():
    if not picker_fast_refresh_lock.acquire(blocking=False):
        return

    try:
        for attempt in range(PICKER_FAST_REFRESH_ATTEMPTS):
            refresh_picker_and_repaint(force=True)
            if attempt + 1 < PICKER_FAST_REFRESH_ATTEMPTS:
                time.sleep(PICKER_FAST_REFRESH_DELAY_SECONDS)
    finally:
        picker_fast_refresh_lock.release()


def trigger_picker_fast_refresh():
    threading.Thread(target=picker_fast_refresh_worker, daemon=True).start()


def timer_worker():
    target_delta_ms = None
    fetched_at = time.monotonic()

    while True:
        if TEST_MODE:
            seconds_left = TEST_ALERT_SECONDS
            q.put((format_seconds(seconds_left), seconds_left))
            time.sleep(0.05)
            continue

        if target_delta_ms is None:
            try:
                target_delta_ms = fetch_target_update()
                if target_delta_ms is None:
                    raise ValueError("Timer timestamp not found")
                fetched_at = time.monotonic()
            except Exception as e:
                log_error("fetch", f"Timer fetch failed: {e}")
                q.put("--:--")
                time.sleep(3)
                continue

        elapsed_ms = (time.monotonic() - fetched_at) * 1000
        seconds_left = (target_delta_ms - elapsed_ms) / 1000
        q.put((format_seconds(seconds_left), seconds_left))

        if seconds_left <= ALERT_END_SECONDS:
            trigger_picker_fast_refresh()
            target_delta_ms = None
            time.sleep(1)
        else:
            time.sleep(0.05 if is_alert_window(seconds_left) else 0.2)


def update_label():
    global remaining_seconds, timer_base_at, timer_base_seconds

    while not q.empty():
        value = q.get()
        if isinstance(value, tuple):
            _, seconds_left = value
            timer_base_seconds = float(seconds_left)
            timer_base_at = time.monotonic()
        else:
            display_value, seconds_left = parse_timer(value)
            timer_base_seconds = seconds_left
            timer_base_at = None
            if SHOW_NOTCH_OVERLAY and canvas is not None and timer_text is not None:
                canvas.itemconfig(timer_text, text=display_value)

    if timer_base_seconds is not None:
        if timer_base_at is None:
            smooth_seconds = timer_base_seconds
        elif TEST_MODE:
            smooth_seconds = timer_base_seconds
        else:
            smooth_seconds = timer_base_seconds - (time.monotonic() - timer_base_at)

        remaining_seconds = smooth_seconds
        if SHOW_NOTCH_OVERLAY and canvas is not None and timer_text is not None:
            canvas.itemconfig(timer_text, text=format_seconds(smooth_seconds))

    update_colors()
    update_picker_timer_label()

    root.after(ALERT_UPDATE_MS, update_label)


def update_colors():
    foreground_hwnd = get_foreground_hwnd()
    game_foreground = is_game_window(foreground_hwnd)

    if not is_alert_window(remaining_seconds):
        set_notch_visible(False)
        set_alert_visible(False)
        set_primary_monitor_alert(False)
        set_second_monitor_alert(False)
        return

    pulse = get_alert_pulse()
    if pulse <= 0:
        set_notch_visible(False)
        set_alert_visible(False)
        set_primary_monitor_alert(False)
        set_second_monitor_alert(False)
        return

    primary_active = is_window_on_primary_monitor(foreground_hwnd, primary_monitor_rect)

    if game_foreground:
        set_notch_visible(False)
        set_alert_visible(False)
        set_primary_monitor_alert(False)
        set_second_monitor_alert(True, pulse)
    elif TEST_MODE or primary_active:
        set_notch_visible(False)
        set_alert_visible(False)
        set_primary_monitor_alert(True, pulse)
        set_second_monitor_alert(False)
    else:
        set_notch_visible(False)
        set_alert_visible(False)
        set_primary_monitor_alert(False)
        set_second_monitor_alert(False)


def get_alert_pulse():
    return calculate_alert_pulse(ALERT_PULSE_PATTERN)


def set_notch_colors(bg, fg, alpha):
    if not SHOW_NOTCH_OVERLAY or canvas is None or timer_text is None:
        return

    root.attributes("-alpha", alpha)
    for item in notch_items:
        canvas.itemconfig(item, fill=bg)
    canvas.itemconfig(timer_text, fill=fg)


def set_notch_visible(is_visible):
    if not SHOW_NOTCH_OVERLAY:
        if root.state() != "withdrawn":
            root.withdraw()
        return

    if is_visible:
        if root.state() == "withdrawn":
            show_overlay()
    elif root.state() != "withdrawn":
        root.withdraw()


def set_alert_visible(is_visible, pulse=0):
    if not SHOW_NOTCH_OVERLAY or canvas is None or alert_strip is None or timer_text is None:
        if root.state() != "withdrawn":
            root.withdraw()
        return

    if is_visible:
        root.attributes("-alpha", get_pulse_alpha(ALERT_MIN_ALPHA, ALERT_ALPHA, pulse))
        canvas.itemconfig(alert_strip, state="normal", fill=ALERT_BG)
        for item in notch_items:
            canvas.itemconfig(item, fill=ALERT_BG)
        canvas.itemconfig(timer_text, fill=ALERT_FG)
    else:
        root.attributes("-alpha", NORMAL_ALPHA)
        canvas.itemconfig(alert_strip, state="hidden")
        for item in notch_items:
            canvas.itemconfig(item, fill=NORMAL_BG)
        canvas.itemconfig(timer_text, fill=NORMAL_FG)


def set_primary_monitor_alert(is_visible, pulse=0):
    if primary_monitor_alert is None:
        return

    if is_visible:
        primary_monitor_alert.attributes("-topmost", True)
        primary_monitor_alert.attributes(
            "-alpha",
            get_pulse_alpha(PRIMARY_MONITOR_MIN_ALPHA, PRIMARY_MONITOR_ALPHA, pulse),
        )
        try:
            apply_no_focus_clickthrough(primary_monitor_alert)
        except Exception:
            pass
        show_tk_window_on_rect_no_activate(primary_monitor_alert, primary_monitor_rect)
    else:
        primary_monitor_alert.withdraw()


def set_second_monitor_alert(is_visible, pulse=0):
    if second_monitor_alert is None:
        return

    if is_visible:
        second_monitor_alert.attributes(
            "-alpha",
            get_pulse_alpha(SECOND_MONITOR_MIN_ALPHA, SECOND_MONITOR_ALPHA, pulse),
        )
        try:
            apply_no_focus_clickthrough(second_monitor_alert)
        except Exception:
            pass
        show_tk_window_on_rect_no_activate(second_monitor_alert, second_monitor_rect)
    else:
        second_monitor_alert.withdraw()


def set_second_monitor_border_color(color):
    if second_monitor_canvas is None:
        return

    set_canvas_items_fill(second_monitor_canvas, second_monitor_border_items, color)


def clear_dead_picker_targets():
    global picker_target_hwnd, last_alert_context_hwnd

    if picker_target_hwnd and not is_live_game_window(picker_target_hwnd):
        picker_target_hwnd = None

    if last_alert_context_hwnd and not is_live_window(last_alert_context_hwnd):
        last_alert_context_hwnd = None


def close_picker_if_target_gone():
    global picker_target_hwnd

    if not picker_target_hwnd:
        if is_picker_open():
            hide_picker()
            return True
        return False

    if is_live_game_window(picker_target_hwnd):
        foreground_hwnd = get_foreground_hwnd()
        if is_picker_open() and (
            not foreground_hwnd or not is_game_window(foreground_hwnd)
        ):
            hide_picker()
            return True
        return False

    picker_target_hwnd = None
    if is_picker_open():
        hide_picker()
    return True


def is_own_overlay_hwnd(hwnd):
    if not hwnd:
        return False

    windows = [root, picker_window, primary_monitor_alert, second_monitor_alert]
    for window in windows:
        if window is None:
            continue
        try:
            if get_window_hwnd(window) == hwnd:
                return True
        except Exception:
            continue

    return False


def is_picker_open():
    if picker_window is None:
        return False

    try:
        if picker_window.state() == "withdrawn":
            return False
        return is_picker_window_visible_fast()
    except Exception:
        return False


def is_picker_window_visible_fast():
    if not picker_hwnd:
        return False

    try:
        return bool(ctypes.windll.user32.IsWindowVisible(picker_hwnd))
    except Exception:
        return False


def get_alert_context_hwnd():
    global last_alert_context_hwnd

    foreground_hwnd = get_foreground_hwnd()

    if is_picker_open() and picker_target_hwnd and not is_own_overlay_hwnd(picker_target_hwnd):
        last_alert_context_hwnd = picker_target_hwnd
        return picker_target_hwnd

    if foreground_hwnd and not is_own_overlay_hwnd(foreground_hwnd):
        last_alert_context_hwnd = foreground_hwnd
        return foreground_hwnd

    if last_alert_context_hwnd:
        return last_alert_context_hwnd

    return foreground_hwnd


def get_or_restore_game_hwnd():
    global picker_target_hwnd, last_alert_context_hwnd

    foreground_hwnd = get_picker_action_hwnd()
    if foreground_hwnd:
        return foreground_hwnd

    candidates = []
    for hwnd in (picker_target_hwnd, last_alert_context_hwnd, find_game_window()):
        if hwnd and hwnd not in candidates and is_game_window(hwnd):
            candidates.append(hwnd)

    for hwnd in candidates:
        if restore_game_window(hwnd):
            active_hwnd = get_foreground_hwnd()
            if active_hwnd and is_game_window(active_hwnd):
                picker_target_hwnd = active_hwnd
                last_alert_context_hwnd = active_hwnd
                return active_hwnd

            picker_target_hwnd = hwnd
            last_alert_context_hwnd = hwnd
            return hwnd

    return 0


def find_known_game_hwnd():
    candidates = (
        get_foreground_hwnd(),
        picker_target_hwnd,
        last_alert_context_hwnd,
        find_game_window(),
    )
    for hwnd in candidates:
        if hwnd and is_live_game_window(hwnd):
            return hwnd
    return 0


def send_game_to_background():
    game_hwnd = find_known_game_hwnd()
    if not game_hwnd:
        return False

    hide_picker()
    minimized = minimize_window(game_hwnd)
    if (
        picker_end_previous_hwnd
        and is_live_window(picker_end_previous_hwnd)
        and not is_own_overlay_hwnd(picker_end_previous_hwnd)
        and not is_game_window(picker_end_previous_hwnd)
    ):
        force_foreground_window(picker_end_previous_hwnd)
    return minimized


def note_salvage_cursor_pos():
    global salvage_expected_cursor_pos

    salvage_expected_cursor_pos = get_cursor_pos()


def mark_salvage_mouse_cancel(stop_event):
    global salvage_cleanup_requested, salvage_finish_current_cycle_requested

    reset_salvage_del_pair("mouse moved")
    salvage_cleanup_requested = False
    salvage_finish_current_cycle_requested = False
    append_log_line("salvage stopped: mouse moved")
    if stop_event is not None:
        stop_event.set()


def salvage_cursor_moved_by_user():
    if salvage_expected_cursor_pos is None:
        note_salvage_cursor_pos()
        return False

    current_pos = get_cursor_pos()
    if current_pos is None:
        return False

    return has_cursor_moved(
        salvage_expected_cursor_pos,
        current_pos,
        SALVAGE_MOUSE_CANCEL_THRESHOLD_PIXELS,
    )


def hold_left_mouse(seconds, stop_event=None, mouse_guard=False):
    if not send_mouse_button(MOUSEEVENTF_LEFTDOWN):
        return False

    try:
        return wait_while_mouse_button_held(
            seconds,
            stop_event=stop_event,
            mouse_guard=mouse_guard,
            cursor_moved=salvage_cursor_moved_by_user,
            on_mouse_cancel=lambda: mark_salvage_mouse_cancel(stop_event),
        )
    finally:
        send_mouse_button(MOUSEEVENTF_LEFTUP)


def click_game_search_field(hwnd, clicks=1):
    rect = get_hwnd_rect(hwnd)
    if rect is None:
        return False

    left, top, right, bottom = rect
    width = max(1, right - left)
    height = max(1, bottom - top)
    x_ratio, y_ratio = game.point("picker.search_field")
    x = left + round(width * x_ratio)
    y = top + round(height * y_ratio)

    user32 = ctypes.windll.user32
    user32.SetCursorPos(x, y)
    time.sleep(PASTE_HOVER_BEFORE_CLICK_DELAY)

    clicked = False
    for _ in range(max(1, clicks)):
        user32.SetCursorPos(x, y)
        if not send_mouse_click(MOUSE_CLICK_DELAY):
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(MOUSE_CLICK_DELAY)
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        clicked = True
        time.sleep(MOUSE_CLICK_DELAY)

    user32.SetCursorPos(x, y)
    return clicked


def get_picker_action_hwnd():
    foreground_hwnd = get_foreground_hwnd()
    if foreground_hwnd and is_game_window(foreground_hwnd):
        return foreground_hwnd

    return 0


def get_salvage_action_hwnd():
    global picker_target_hwnd, last_alert_context_hwnd

    foreground_hwnd = get_picker_action_hwnd()
    if foreground_hwnd:
        picker_target_hwnd = foreground_hwnd
        last_alert_context_hwnd = foreground_hwnd
        return foreground_hwnd

    if not is_picker_open():
        append_log_line("salvage desktop start skipped: picker is closed")
        return 0

    target_hwnd = 0
    for hwnd in (picker_target_hwnd, last_alert_context_hwnd):
        if hwnd and is_live_game_window(hwnd):
            target_hwnd = hwnd
            break

    if not target_hwnd:
        target_hwnd = find_game_window()
        if not target_hwnd:
            append_log_line("salvage desktop start skipped: game window not found")
            return 0

    if restore_game_window(target_hwnd):
        foreground_hwnd = get_foreground_hwnd()
        if foreground_hwnd and is_game_window(foreground_hwnd):
            picker_target_hwnd = foreground_hwnd
            last_alert_context_hwnd = foreground_hwnd
            return foreground_hwnd
        picker_target_hwnd = target_hwnd
        last_alert_context_hwnd = target_hwnd
        return target_hwnd

    append_log_line("salvage desktop start skipped: game restore failed")
    return 0


def is_orange_button_pixel(rgb):
    if rgb is None:
        return False

    r, g, b = rgb
    return (
        r >= GAME_BUTTON_ORANGE_MIN_R
        and g >= GAME_BUTTON_ORANGE_MIN_G
        and b <= GAME_BUTTON_ORANGE_MAX_B
        and r > g + GAME_BUTTON_ORANGE_MIN_RG_DIFF
        and r > b + 50
    )


def is_white_pixel(rgb):
    if rgb is None:
        return False

    return (
        min(rgb) >= WHITE_PIXEL_MIN_CHANNEL
        and max(rgb) - min(rgb) <= WHITE_PIXEL_MAX_CHANNEL_SPREAD
    )


def count_orange_button_samples(x_ratio, y_ratio, hwnd=None):
    hwnd = hwnd if hwnd is not None else get_picker_action_hwnd()
    if not hwnd:
        return 0

    point = get_hwnd_ratio_point(hwnd, x_ratio, y_ratio)
    if point is None:
        return 0

    hits = 0
    base_x, base_y = point
    for offset_x, offset_y in GAME_BUTTON_SAMPLE_OFFSETS:
        x = base_x + offset_x
        y = base_y + offset_y
        rgb = get_hwnd_pixel_rgb(hwnd, x, y)
        if rgb is None or not is_orange_button_pixel(rgb):
            rgb = get_screen_pixel_rgb(x, y)
        if is_orange_button_pixel(rgb):
            hits += 1
            if hits >= GAME_BUTTON_SAMPLE_REQUIRED_HITS:
                break
    return hits


def is_game_button_visible(x_ratio, y_ratio, hwnd=None):
    return count_orange_button_samples(
        x_ratio,
        y_ratio,
        hwnd=hwnd,
    ) >= GAME_BUTTON_SAMPLE_REQUIRED_HITS


def is_game_point_visible(point_name, hwnd=None):
    return is_game_button_visible(*game.point(point_name), hwnd=hwnd)


def detect_market_action_stage():
    if is_game_point_visible("market.order_button"):
        return STAGE_QUANTITY
    if is_game_point_visible("market.buy_button"):
        return STAGE_BUY
    return None


def open_selected_market_card():
    return game.click("market.open_card")


def go_back_from_market_card():
    hwnd = get_picker_action_hwnd()
    if not hwnd:
        return False
    tap_key_scancode(VK_ESCAPE, delay=0.010)
    return True


def buy_current_market_item():
    return game.click("market.buy_button")


def increase_market_item_quantity():
    return game.click("market.quantity_plus")


def decrease_market_item_quantity():
    return game.click("market.quantity_minus")


def is_market_order_panel_open():
    return detect_market_action_stage() == STAGE_QUANTITY


def close_market_order_panel():
    if right_shift_order_down:
        set_order_button_hold(False)

    ok = game.click("market.order_panel_close")
    if ok:
        append_log_line("market navigation: closed order panel")
        reset_market_action_stage()
        time.sleep(GAME_SECTION_CLICK_DELAY_SECONDS)
    else:
        append_log_line("market navigation: close order panel failed")
    return ok


def ensure_market_order_panel_closed():
    if not is_market_order_panel_open():
        return True

    return close_market_order_panel()


def read_screen_point_rgb(point_name):
    point = game.screen_point(point_name)
    if point is None:
        return None

    x, y = point
    return get_screen_pixel_rgb(x, y)


def read_market_tab_probe():
    return read_screen_point_rgb("market.market_tab")


def is_market_tab_active_pixel(rgb):
    if rgb is None:
        return False

    red, green, blue = rgb
    target_red, target_green, target_blue = MARKET_TAB_ACTIVE_RGB
    return (
        abs(red - target_red) <= MARKET_TAB_ACTIVE_TOLERANCE
        and abs(green - target_green) <= MARKET_TAB_ACTIVE_TOLERANCE
        and abs(blue - target_blue) <= MARKET_TAB_ACTIVE_TOLERANCE
        and red > green + 45
        and green > blue + 60
    )


def is_market_view_active():
    return is_market_tab_active_pixel(read_market_tab_probe())


def ensure_market_view_before_picker_navigation():
    if not get_picker_action_hwnd():
        return False

    if not ensure_market_order_panel_closed():
        return False

    market_rgb = read_market_tab_probe()
    if (
        is_market_tab_active_pixel(market_rgb)
        and market_current_subtab == MARKET_SUBTAB_DETAILS
    ):
        return True

    append_log_line(
        "market navigation: open market details "
        f"market_rgb={market_rgb}"
    )
    return open_game_market_details()


def ensure_market_ready_for_picker_selection():
    if not wait_market_order_complete_probe_if_running():
        return False

    if get_picker_action_hwnd():
        return ensure_market_view_before_picker_navigation()

    return open_picker_market_details()


def is_market_order_complete_orange(rgb):
    if rgb is None:
        return False

    red, green, blue = rgb
    target_red, target_green, target_blue = MARKET_ORDER_COMPLETE_ORANGE_RGB
    return (
        abs(red - target_red) <= MARKET_ORDER_COMPLETE_ORANGE_TOLERANCE
        and abs(green - target_green) <= MARKET_ORDER_COMPLETE_ORANGE_TOLERANCE
        and abs(blue - target_blue) <= MARKET_ORDER_COMPLETE_ORANGE_TOLERANCE
        and red > green + 55
        and green > blue + 20
    )


def read_market_order_complete_probe():
    point = game.screen_point("market.order_complete_probe")
    if point is None:
        return None, None

    x, y = point
    for offset_x, offset_y in WHITE_PIXEL_SAMPLE_OFFSETS:
        sample_x = x + offset_x
        sample_y = y + offset_y
        rgb = get_screen_pixel_rgb(sample_x, sample_y)
        if is_market_order_complete_orange(rgb):
            return (sample_x, sample_y), rgb

    return None, get_screen_pixel_rgb(x, y)


def wait_market_order_complete_and_escape():
    global market_order_complete_probe_running, right_shift_order_down

    try:
        deadline = time.monotonic() + MARKET_ORDER_COMPLETE_PROBE_WAIT_SECONDS
        last_rgb = None
        while time.monotonic() < deadline:
            if not get_picker_action_hwnd():
                return

            hit_point, rgb = read_market_order_complete_probe()
            last_rgb = rgb
            if hit_point is not None:
                append_log_line(f"market order complete: esc at {hit_point} rgb={rgb}")
                if right_shift_order_down:
                    send_mouse_button(MOUSEEVENTF_LEFTUP)
                    right_shift_order_down = False
                reset_market_action_stage()
                tap_key_scancode(VK_ESCAPE, delay=0.010)
                time.sleep(MARKET_ORDER_COMPLETE_ESC_REPEAT_DELAY_SECONDS)
                tap_key_scancode(VK_ESCAPE, delay=0.010)
                return

            time.sleep(MARKET_ORDER_COMPLETE_PROBE_POLL_SECONDS)

        append_log_line(f"market order complete probe timeout: last_rgb={last_rgb}")
    finally:
        with market_order_complete_probe_lock:
            market_order_complete_probe_running = False
            market_order_complete_probe_done.set()


def start_market_order_complete_escape_probe():
    global market_order_complete_probe_running

    with market_order_complete_probe_lock:
        if market_order_complete_probe_running:
            return
        market_order_complete_probe_running = True
        market_order_complete_probe_done.clear()

    threading.Thread(target=wait_market_order_complete_and_escape, daemon=True).start()


def is_market_order_complete_probe_running():
    with market_order_complete_probe_lock:
        return market_order_complete_probe_running


def wait_market_order_complete_probe_if_running():
    if not is_market_order_complete_probe_running():
        return True

    append_log_line("market navigation: waiting for order complete probe")
    wait_seconds = MARKET_ORDER_COMPLETE_PROBE_WAIT_SECONDS + 0.25
    return market_order_complete_probe_done.wait(wait_seconds)


def cancel_pending_picker_selection(redraw=False):
    global picker_pending_row_index, picker_pending_selection_token

    picker_pending_selection_token += 1
    picker_pending_row_index = None
    if redraw:
        draw_picker_hover(picker_selected_row_index)


def begin_pending_picker_selection(row_index, item_name):
    global picker_pending_row_index, picker_pending_selection_token

    if not is_market_order_complete_probe_running():
        return False

    picker_pending_selection_token += 1
    token = picker_pending_selection_token
    picker_pending_row_index = row_index
    draw_picker_hover(row_index)

    def wait_and_finish():
        wait_ok = wait_market_order_complete_probe_if_running()
        root.after(
            0,
            lambda: finish_pending_picker_selection(
                token,
                row_index,
                item_name,
                wait_ok,
            ),
        )

    threading.Thread(target=wait_and_finish, daemon=True).start()
    return True


def finish_pending_picker_selection(token, row_index, item_name, wait_ok):
    global picker_pending_row_index

    if token != picker_pending_selection_token:
        return

    picker_pending_row_index = None
    draw_picker_hover(picker_selected_row_index)

    if not wait_ok:
        append_log_line("market navigation: order complete probe wait failed")
        return
    if picker_selected_row_index != row_index:
        return
    if not ensure_market_ready_for_picker_selection():
        return

    reset_market_action_stage()
    paste_item_name(item_name)


def open_game_market_details():
    return open_game_market_subtab(
        "market.details_tab",
        MARKET_SUBTAB_DETAILS,
    )


def open_game_market_lots():
    return open_game_market_subtab("market.lots_tab", MARKET_SUBTAB_LOTS)


def open_game_market_subtab(tab_point_name, subtab_name):
    global market_current_subtab

    if is_market_view_active():
        clicked_market = True
    else:
        clicked_market = game.click("market.market_tab")
        if not clicked_market:
            return False
        time.sleep(GAME_SECTION_CLICK_DELAY_SECONDS)

    clicked_tab = game.click(tab_point_name)
    if clicked_market or clicked_tab:
        if clicked_tab:
            market_current_subtab = subtab_name
        reset_market_action_stage()
    return clicked_market and clicked_tab


def reassert_picker_window():
    if picker_window is not None:
        show_picker(toggle=False)


def schedule_picker_reassert():
    if root is None:
        return

    root.after(0, reassert_picker_window)
    root.after(150, reassert_picker_window)


def open_picker_market_details():
    if not get_or_restore_game_hwnd():
        append_log_line("picker End open skipped: game window not found")
        return False

    open_game_market_details()
    show_picker(toggle=False)
    return True


def set_market_action_stage(stage, ready_at=0):
    market_action_state.set(stage, ready_at)


def reset_market_action_stage():
    market_action_state.reset()


def get_market_action_stage():
    return market_action_state.get()


def handle_market_action_right():
    global right_arrow_last_action_stage

    now = time.monotonic()
    detected_stage = detect_market_action_stage()

    if detected_stage == STAGE_QUANTITY:
        right_arrow_last_action_stage = STAGE_QUANTITY
        set_market_action_stage(STAGE_QUANTITY, 0)
        return increase_market_item_quantity()

    if detected_stage == STAGE_BUY:
        right_arrow_last_action_stage = STAGE_BUY
        ok = buy_current_market_item()
        if ok:
            set_market_action_stage(STAGE_OPENING_BUY_DIALOG, now + GAME_BUY_TO_QUANTITY_DELAY_SECONDS)
        return ok

    if get_market_action_stage() == STAGE_OPENING_BUY_DIALOG:
        return False

    right_arrow_last_action_stage = STAGE_OPEN_CARD
    ok = open_selected_market_card()
    if ok and market_action_state.stage != STAGE_OPENING_CARD:
        set_market_action_stage(STAGE_OPENING_CARD, now + GAME_OPEN_TO_BUY_DELAY_SECONDS)
    return ok


def handle_market_action_left():
    if is_market_order_panel_open():
        return close_market_order_panel()

    reset_market_action_stage()
    return go_back_from_market_card()


def resolve_picker_end_hold(expected_press_at):
    global picker_end_hold_pending, picker_end_hold_triggered
    global picker_end_background_hold_triggered

    if expected_press_at != picker_end_press_at:
        return

    picker_end_hold_pending = False
    if picker_end_hold_triggered:
        return

    if is_virtual_key_down(VK_END):
        picker_end_hold_triggered = True
        picker_end_background_hold_triggered = True
        send_game_to_background()


def schedule_picker_end_hold_check():
    global picker_end_hold_pending

    if picker_end_hold_pending or picker_end_hold_triggered:
        return

    picker_end_hold_pending = True
    press_at = picker_end_press_at
    root.after(
        max(1, int(PICKER_OPEN_HOLD_SECONDS * 1000)),
        lambda: resolve_picker_end_hold(press_at),
    )


def handle_picker_end_hotkey():
    global picker_end_press_active, picker_end_press_was_open, picker_end_hold_triggered
    global picker_end_background_hold_triggered, picker_end_latched, picker_end_press_at
    global picker_end_previous_hwnd, picker_end_started_in_game

    if time.monotonic() < picker_end_ignore_until:
        return

    if picker_end_latched or picker_end_press_active:
        return

    picker_end_latched = True
    picker_end_press_at = time.monotonic()
    picker_end_press_active = True
    picker_end_press_was_open = is_picker_open()
    picker_end_started_in_game = False
    picker_end_hold_triggered = False
    picker_end_background_hold_triggered = False
    foreground_hwnd = get_foreground_hwnd()
    picker_end_started_in_game = bool(foreground_hwnd and is_game_window(foreground_hwnd))
    if (
        foreground_hwnd
        and not is_own_overlay_hwnd(foreground_hwnd)
        and not is_game_window(foreground_hwnd)
    ):
        picker_end_previous_hwnd = foreground_hwnd
    else:
        picker_end_previous_hwnd = 0

    if picker_end_started_in_game and not picker_end_press_was_open:
        show_picker(toggle=False)

    schedule_picker_end_hold_check()


def finish_picker_end_press():
    global picker_end_press_active, picker_end_hold_pending, picker_end_latched
    global picker_end_ignore_until, picker_end_started_in_game

    if not picker_end_press_active:
        picker_end_latched = False
        picker_end_started_in_game = False
        return

    started_in_game = picker_end_started_in_game
    picker_end_press_active = False
    picker_end_hold_pending = False
    picker_end_latched = False
    picker_end_started_in_game = False

    if picker_end_hold_triggered:
        picker_end_ignore_until = time.monotonic() + 0.35
        return

    if not started_in_game:
        open_picker_market_details()
        return

    if picker_end_press_was_open:
        hide_picker()
    elif not is_picker_open():
        show_picker(toggle=False)


def handle_right_ctrl_escape():
    if not ensure_market_order_panel_closed():
        return False

    if market_current_subtab == MARKET_SUBTAB_DETAILS:
        ok = open_game_market_lots()
    else:
        ok = open_game_market_details()

    if ok:
        schedule_picker_reassert()
    return ok


def sleep_with_stop(seconds, stop_event, mouse_guard=False):
    return salvage_sleep_with_stop(
        seconds,
        stop_event,
        mouse_guard=mouse_guard,
        cursor_moved=salvage_cursor_moved_by_user,
        on_mouse_cancel=lambda: mark_salvage_mouse_cancel(stop_event),
    )


def salvage_click(point_name, stop_event, right=False):
    target_hwnd = salvage_action_hwnd or get_picker_action_hwnd()
    if stop_event.is_set() or not target_hwnd:
        return False
    ok = (
        game.right_click(point_name, hwnd=target_hwnd)
        if right
        else game.click(point_name, hwnd=target_hwnd)
    )
    if ok:
        note_salvage_cursor_pos()
        sleep_with_stop(SALVAGE_STEP_DELAY_SECONDS, stop_event, mouse_guard=True)
    return ok


def salvage_click_no_stop(point_name, hwnd=None):
    target_hwnd = hwnd if hwnd is not None else get_picker_action_hwnd()
    if not target_hwnd:
        return False
    ok = game.click(point_name, hwnd=target_hwnd)
    if ok:
        time.sleep(SALVAGE_STEP_DELAY_SECONDS)
    return ok


def get_screen_point_pixel_samples(point_name):
    point = game.screen_point(point_name)
    if point is None:
        return None

    x, y = point
    samples = []
    for offset_x, offset_y in WHITE_PIXEL_SAMPLE_OFFSETS:
        sample_x = x + offset_x
        sample_y = y + offset_y
        samples.append((sample_x, sample_y, get_screen_pixel_rgb(sample_x, sample_y)))

    return samples


def first_white_screen_sample(point_name):
    samples = get_screen_point_pixel_samples(point_name)
    if samples is None:
        return None, None

    for sample_x, sample_y, rgb in samples:
        if is_white_pixel(rgb):
            return (sample_x, sample_y), rgb

    center_rgb = samples[0][2] if samples else None
    return None, center_rgb


def select_salvage_context_disassemble_point(stop_event):
    started_at = time.monotonic()
    deadline = started_at + max(0.0, SALVAGE_CONTEXT_PROBE_WAIT_SECONDS)
    probe_log_parts = []

    while not stop_event.is_set() and is_live_game_window(salvage_action_hwnd):
        top_probe, top_click = SALVAGE_CONTEXT_DISASSEMBLE_CHOICES[0]
        bottom_probe, bottom_click = SALVAGE_CONTEXT_DISASSEMBLE_CHOICES[1]

        top_hit, top_rgb = first_white_screen_sample(top_probe)
        bottom_hit, bottom_rgb = first_white_screen_sample(bottom_probe)
        probe_log_parts = [
            f"{top_probe}={top_rgb}",
            f"{bottom_probe}={bottom_rgb}",
        ]

        if top_hit is not None:
            return top_click
        if bottom_hit is not None:
            return bottom_click

        remaining_seconds = deadline - time.monotonic()
        if remaining_seconds <= 0:
            break

        wait_seconds = min(
            max(0.001, SALVAGE_CONTEXT_PROBE_POLL_SECONDS),
            remaining_seconds,
        )
        if not sleep_with_stop(wait_seconds, stop_event, mouse_guard=True):
            return None

    elapsed_ms = round((time.monotonic() - started_at) * 1000)
    append_log_line(
        "salvage context probe "
        + " ".join(probe_log_parts)
        + f" auto_finish_after_current_step elapsed_ms={elapsed_ms}"
    )
    request_salvage_finish_current_cycle(cleanup=True)
    return "salvage.context_disassemble"


def salvage_click_screen(point_name, stop_event):
    target_hwnd = salvage_action_hwnd or get_picker_action_hwnd()
    if stop_event.is_set() or not target_hwnd:
        return False

    ok = game.click_screen(point_name)
    if ok:
        note_salvage_cursor_pos()
        sleep_with_stop(SALVAGE_STEP_DELAY_SECONDS, stop_event, mouse_guard=True)
    return ok


def salvage_click_context_disassemble(stop_event):
    target_hwnd = salvage_action_hwnd or get_picker_action_hwnd()
    if stop_event.is_set() or not target_hwnd:
        return False

    point_name = select_salvage_context_disassemble_point(stop_event)
    if point_name is None:
        return False

    return salvage_click_screen(point_name, stop_event)


def salvage_right_click_item(point_name, stop_event):
    global salvage_last_item_right_click_at

    target_hwnd = salvage_action_hwnd or get_picker_action_hwnd()
    if stop_event.is_set() or not target_hwnd:
        return False

    if not game.move_to(point_name, hwnd=target_hwnd):
        return False
    note_salvage_cursor_pos()
    if not sleep_with_stop(SALVAGE_ITEM_HOVER_DELAY_SECONDS, stop_event, mouse_guard=True):
        return False
    wait_time = remaining_cooldown_seconds(
        salvage_last_item_right_click_at,
        SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS,
    )
    if wait_time:
        if not sleep_with_stop(wait_time, stop_event, mouse_guard=True):
            return False
    if not send_mouse_right_click(MOUSE_CLICK_DELAY):
        return False
    salvage_last_item_right_click_at = time.monotonic()
    note_salvage_cursor_pos()
    return sleep_with_stop(SALVAGE_POST_RIGHT_CLICK_DELAY_SECONDS, stop_event, mouse_guard=True)


def salvage_confirm_available():
    return is_game_point_visible("salvage.confirm_button", hwnd=salvage_action_hwnd)


def wait_for_salvage_confirm_available(stop_event):
    deadline = time.monotonic() + max(0.0, SALVAGE_CONFIRM_WAIT_SECONDS)

    while not stop_event.is_set() and is_live_game_window(salvage_action_hwnd):
        if salvage_confirm_available():
            return True

        remaining_seconds = deadline - time.monotonic()
        if remaining_seconds <= 0:
            return False

        if not sleep_with_stop(
            min(SALVAGE_CONFIRM_POLL_SECONDS, remaining_seconds),
            stop_event,
            mouse_guard=True,
        ):
            return False

    return False


def restore_salvage_sort_type(hwnd=None):
    target_hwnd = hwnd if hwnd is not None else get_picker_action_hwnd()
    if not target_hwnd or not is_live_game_window(target_hwnd):
        append_log_line("salvage stop cleanup skipped: game window not found")
        return False

    force_foreground_window(target_hwnd)
    append_log_line("salvage stop cleanup: sort dropdown")
    opened = salvage_click_no_stop("salvage.sort_dropdown", hwnd=target_hwnd)
    if not opened:
        append_log_line("salvage stop cleanup failed: sort dropdown")
        return False

    append_log_line("salvage stop cleanup: sort type")
    if not salvage_click_no_stop("salvage.sort_type_option", hwnd=target_hwnd):
        append_log_line("salvage stop cleanup failed: sort type")
        return False

    append_log_line("salvage stop cleanup: finish click")
    if not salvage_click_no_stop("salvage.stop_finish_click", hwnd=target_hwnd):
        append_log_line("salvage stop cleanup failed: finish click")
        return False

    return True


def arm_salvage_del_pair(hwnd=None):
    global salvage_pair_armed, salvage_pair_hwnd

    salvage_pair_armed = True
    if hwnd:
        salvage_pair_hwnd = hwnd


def reset_salvage_del_pair(reason=None):
    global salvage_pair_armed, salvage_pair_hwnd

    if salvage_pair_armed and reason:
        append_log_line(f"salvage Del pair reset: {reason}")
    salvage_pair_armed = False
    salvage_pair_hwnd = 0


def is_any_non_delete_key_down():
    mouse_button_vks = {0x01, 0x02, 0x04, 0x05, 0x06}
    for vk in range(1, 256):
        if vk == VK_DELETE or vk in mouse_button_vks:
            continue
        if is_virtual_key_down(vk):
            return True
    return False


def run_salvage_loop(stop_event):
    global salvage_running, salvage_expected_cursor_pos, salvage_last_item_right_click_at
    global salvage_action_hwnd
    global salvage_cleanup_requested, salvage_restart_after_stop, salvage_arm_after_restart
    global salvage_finish_current_cycle_requested

    try:
        hwnd = salvage_action_hwnd or get_salvage_action_hwnd()
        if not hwnd:
            append_log_line("salvage start failed: game window not found")
            return

        salvage_action_hwnd = hwnd
        salvage_expected_cursor_pos = None
        salvage_last_item_right_click_at = 0
        root.after(0, hide_picker)
        sleep_with_stop(0.06, stop_event)

        if not salvage_click("salvage.storage_tab", stop_event):
            return
        if not salvage_click("salvage.details_tab", stop_event):
            return
        if not salvage_click("salvage.pre_decor_category", stop_event):
            return
        if not salvage_click("salvage.decor_category", stop_event):
            return
        if not salvage_click("salvage.sort_dropdown", stop_event):
            return
        if not salvage_click("salvage.sort_new_option", stop_event):
            return

        if salvage_finish_current_cycle_requested:
            return

        while (
            not stop_event.is_set()
            and not salvage_finish_current_cycle_requested
            and is_live_game_window(salvage_action_hwnd)
        ):
            if not salvage_right_click_item("salvage.first_item", stop_event):
                break
            if not salvage_click_context_disassemble(stop_event):
                break
            if (
                SALVAGE_POST_MENU_CLICK_DELAY_SECONDS > 0
                and not sleep_with_stop(
                    SALVAGE_POST_MENU_CLICK_DELAY_SECONDS,
                    stop_event,
                    mouse_guard=True,
                )
            ):
                break

            if not wait_for_salvage_confirm_available(stop_event):
                append_log_line("salvage stopped: confirm button not found")
                break

            if not salvage_click("salvage.all_button", stop_event):
                break
            if not sleep_with_stop(SALVAGE_POST_ALL_CLICK_DELAY_SECONDS, stop_event, mouse_guard=True):
                break
            if not game.hold(
                "salvage.confirm_button",
                SALVAGE_CONFIRM_HOLD_SECONDS,
                stop_event=stop_event,
                mouse_guard=True,
                before_hold=note_salvage_cursor_pos,
            ):
                break
            if not sleep_with_stop(SALVAGE_AFTER_CONFIRM_SECONDS, stop_event, mouse_guard=True):
                break
            if salvage_finish_current_cycle_requested:
                break
    except Exception as e:
        log_error("salvage", f"Salvage loop failed: {e}")
    finally:
        was_cancelled = stop_event.is_set()
        should_cleanup = salvage_cleanup_requested
        should_restart = was_cancelled and salvage_restart_after_stop
        should_arm_after_restart = salvage_arm_after_restart
        send_mouse_button(MOUSEEVENTF_LEFTUP)
        if should_cleanup:
            restore_salvage_sort_type(hwnd=salvage_action_hwnd)
        salvage_running = False
        salvage_action_hwnd = 0
        salvage_cleanup_requested = False
        salvage_restart_after_stop = False
        salvage_arm_after_restart = False
        salvage_finish_current_cycle_requested = False
        stop_event.clear()
        if should_restart:
            root.after(
                0,
                lambda: start_salvage_loop(arm_pair=should_arm_after_restart),
            )


def request_salvage_stop(cleanup=False, restart=False, arm_after_restart=False):
    global salvage_cleanup_requested, salvage_restart_after_stop, salvage_arm_after_restart
    global salvage_finish_current_cycle_requested

    if not salvage_running:
        return False

    salvage_cleanup_requested = bool(cleanup)
    salvage_restart_after_stop = bool(restart)
    salvage_arm_after_restart = bool(arm_after_restart)
    salvage_finish_current_cycle_requested = False
    salvage_stop_event.set()
    send_mouse_button(MOUSEEVENTF_LEFTUP)
    return True


def request_salvage_finish_current_cycle(cleanup=False):
    global salvage_cleanup_requested, salvage_finish_current_cycle_requested
    global salvage_restart_after_stop, salvage_arm_after_restart

    if not salvage_running:
        return False

    salvage_cleanup_requested = bool(cleanup)
    salvage_finish_current_cycle_requested = True
    salvage_restart_after_stop = False
    salvage_arm_after_restart = False
    append_log_line("salvage will stop after current cycle")
    return True


def start_salvage_loop(arm_pair=False):
    global salvage_running, salvage_delete_was_down
    global salvage_action_hwnd
    global salvage_cleanup_requested, salvage_restart_after_stop, salvage_arm_after_restart
    global salvage_finish_current_cycle_requested

    if salvage_running:
        return False
    target_hwnd = get_salvage_action_hwnd()
    if not target_hwnd:
        append_log_line("salvage start skipped: picker/game window not available")
        return False

    salvage_action_hwnd = target_hwnd
    salvage_delete_was_down = is_virtual_key_down(VK_DELETE)
    salvage_cleanup_requested = False
    salvage_restart_after_stop = False
    salvage_arm_after_restart = False
    salvage_finish_current_cycle_requested = False
    salvage_stop_event.clear()
    salvage_running = True
    if arm_pair:
        arm_salvage_del_pair()
    threading.Thread(target=run_salvage_loop, args=(salvage_stop_event,), daemon=True).start()
    return True


def run_salvage_second_script():
    target_hwnd = salvage_action_hwnd or salvage_pair_hwnd or get_picker_action_hwnd() or find_known_game_hwnd()
    reset_salvage_del_pair()
    if request_salvage_finish_current_cycle(cleanup=True):
        return True

    return restore_salvage_sort_type(hwnd=target_hwnd)


def handle_salvage_del_press(ignore_latch=False):
    global salvage_delete_was_down, salvage_last_delete_handled_at

    delete_down = is_virtual_key_down(VK_DELETE)
    now = time.monotonic()
    if delete_down and salvage_delete_was_down and not ignore_latch:
        return
    if now - salvage_last_delete_handled_at < 0.20:
        return

    salvage_delete_was_down = delete_down
    salvage_last_delete_handled_at = now

    if not ensure_market_order_panel_closed():
        return

    if not salvage_running and not get_picker_action_hwnd() and not is_picker_open():
        append_log_line("salvage Del ignored: picker is closed")
        hotkeys.pass_delete_once()
        return

    append_log_line("salvage Del: script")
    if salvage_running:
        request_salvage_stop(restart=True, arm_after_restart=False)
        return

    if not start_salvage_loop(arm_pair=False):
        append_log_line("salvage Del script start failed")
        hotkeys.pass_delete_once()


def set_order_button_hold(is_down):
    global right_shift_order_down

    if is_down == right_shift_order_down:
        return True

    if is_down:
        if detect_market_action_stage() != STAGE_QUANTITY:
            return False
        if not game.move_to("market.order_button"):
            return False
        ok = send_mouse_button(MOUSEEVENTF_LEFTDOWN)
        right_shift_order_down = ok
        if ok:
            start_market_order_complete_escape_probe()
        return ok

    was_down = right_shift_order_down
    ok = send_mouse_button(MOUSEEVENTF_LEFTUP)
    right_shift_order_down = False
    if was_down:
        reset_market_action_stage()
    return ok


def _log_direct(message):
    append_log_line(message)


def set_clipboard_text_win32(text):
    """Кладёт Unicode-текст в буфер обмена напрямую через WinAPI."""
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]

    text_bytes = text.encode("utf-16-le") + b"\x00\x00"

    if not user32.OpenClipboard(0):
        _log_direct(f"OpenClipboard failed, err={kernel32.GetLastError()}")
        return False

    h_mem = None
    try:
        user32.EmptyClipboard()
        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
        if not h_mem:
            _log_direct(f"GlobalAlloc failed, err={kernel32.GetLastError()}")
            return False

        ptr = kernel32.GlobalLock(h_mem)
        if not ptr:
            _log_direct(f"GlobalLock failed, err={kernel32.GetLastError()}")
            kernel32.GlobalFree(h_mem)
            return False

        ctypes.memmove(ptr, text_bytes, len(text_bytes))
        kernel32.GlobalUnlock(h_mem)

        if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
            _log_direct(f"SetClipboardData failed, err={kernel32.GetLastError()}")
            kernel32.GlobalFree(h_mem)
            return False

        # После успешного SetClipboardData память принадлежит Windows, освобождать её нельзя.
        h_mem = None
        return True
    finally:
        user32.CloseClipboard()


def set_clipboard_text_safe(text):
    # Сначала WinAPI, если не вышло — старый рабочий способ Tkinter.
    if set_clipboard_text_win32(text):
        return True
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        return True
    except Exception as e:
        _log_direct(f"Tk clipboard failed: {e}")
        return False


def restore_picker_after_paste():
    if picker_window is None or picker_window.state() == "withdrawn":
        return

    try:
        show_tk_window_no_activate(picker_window)
        position_picker_window()
    except Exception:
        pass


def paste_item_name(name):
    global last_picker_paste_at, last_picker_paste_name, picker_target_hwnd

    name = normalize_game_search_text(name)
    now = time.monotonic()
    if name == last_picker_paste_name and now - last_picker_paste_at < 0.5:
        return
    last_picker_paste_at = now
    last_picker_paste_name = name

    target_hwnd = picker_target_hwnd

    if not set_clipboard_text_safe(name):
        _log_direct(f"Clipboard failed for: {name!r}")
        return

    def do_paste():
        old_cursor = POINT()
        cursor_saved = bool(ctypes.windll.user32.GetCursorPos(ctypes.byref(old_cursor)))
        try:
            _log_direct(f"do_paste start: name={name!r} hwnd={target_hwnd}")

            fg_ok = force_foreground_window(target_hwnd)
            _log_direct(f"do_paste: foreground={fg_ok}")

            time.sleep(PASTE_BEFORE_CLICK_DELAY)
            click_ok = click_game_search_field(target_hwnd, clicks=PASTE_SEARCH_CLICKS)
            _log_direct(f"do_paste: click={click_ok}")

            time.sleep(PASTE_AFTER_CLICK_DELAY)
            send_ctrl_key(VK_A, PASTE_BETWEEN_KEYS_DELAY)
            time.sleep(PASTE_BETWEEN_KEYS_DELAY)
            tap_key(VK_BACK)
            time.sleep(PASTE_AFTER_CLEAR_DELAY)
            send_ctrl_key(VK_V, PASTE_BETWEEN_KEYS_DELAY)
            if cursor_saved:
                ctypes.windll.user32.SetCursorPos(old_cursor.x, old_cursor.y)
                cursor_saved = False
            time.sleep(PASTE_BEFORE_ENTER_DELAY)
            tap_key(VK_RETURN, delay=PASTE_ENTER_KEY_DELAY)
            _log_direct("do_paste: click + clear + ctrl+v + cursor restore + enter sent")
        except Exception as e:
            _log_direct(f"do_paste: EXCEPTION {e}")
        finally:
            if cursor_saved:
                ctypes.windll.user32.SetCursorPos(old_cursor.x, old_cursor.y)
            root.after(0, restore_picker_after_paste)
            root.after(120, restore_picker_after_paste)

    threading.Thread(target=do_paste, daemon=True).start()


def get_picker_content_height():
    if picker_total_content_height > 0:
        return picker_total_content_height
    if picker_canvas is None:
        return PICKER_ROW_HEIGHT * PICKER_MIN_ROWS

    try:
        picker_canvas.update_idletasks()
        bbox = picker_canvas.bbox("all")
    except Exception:
        bbox = None

    if not bbox:
        return PICKER_ROW_HEIGHT * PICKER_MIN_ROWS

    return max(0, bbox[3] - bbox[1])


def get_picker_total_height(max_available_height):
    min_height = PICKER_TIMER_HEIGHT + PICKER_ROW_HEIGHT * PICKER_MIN_ROWS
    desired_height = PICKER_TIMER_HEIGHT + get_picker_content_height() + 4
    return max(min_height, min(desired_height, PICKER_MAX_HEIGHT, max_available_height))


def position_picker_window():
    global picker_current_width

    if picker_window is None:
        return

    target_rect = get_hwnd_rect(picker_target_hwnd)
    if target_rect is None:
        target_rect = (0, 0, root.winfo_screenwidth(), root.winfo_screenheight())

    left, top, right, bottom = target_rect
    target_width = max(1, right - left)
    target_height = max(1, bottom - top)
    scale = max(1.0, root.winfo_fpixels("1i") / 96)
    x_ratio, y_ratio = game.point("picker.window_anchor")

    x = (
        left
        + round(target_width * x_ratio)
        + round(PICKER_GAME_SEARCH_GAP_PIXELS * scale)
    )
    y = (
        top
        + round(target_height * y_ratio)
        + round(PICKER_GAME_SEARCH_Y_OFFSET_PIXELS * scale)
    )
    x -= round(PICKER_LEFT_EXPAND_PIXELS * scale)
    y -= PICKER_TIMER_HEIGHT
    bottom_margin = round(PICKER_BOTTOM_MARGIN_PIXELS * scale)
    max_available_height = max(
        PICKER_TIMER_HEIGHT,
        bottom - y - bottom_margin,
    )
    available_width = max(1, right - left)
    available_height = max(1, bottom - top)
    total_height = min(get_picker_total_height(max_available_height), available_height)
    window_width = min(PICKER_WIDTH, available_width)

    if picker_current_width != window_width:
        picker_current_width = window_width
        picker_columns_cache.clear()

    x = min(max(left, x), right - window_width)
    y = min(max(top, y), bottom - total_height)

    picker_window.geometry(f"{window_width}x{total_height}{x:+d}{y:+d}")


def measure_picker_header(text, minimum):
    try:
        font = tkfont.Font(family="Segoe UI", size=8, weight="bold")
        return max(minimum, font.measure(text) + 24)
    except Exception:
        return minimum


def get_picker_table_inner_width():
    return picker_current_width - 18


def get_picker_columns(kind):
    cached_columns = picker_columns_cache.get(kind)
    if cached_columns is not None:
        return cached_columns

    if kind == "flash":
        value_columns = [
            {"key": "history_sell", "title": "60 мин", "min": PICKER_FLASH_HISTORY_COL_WIDTH, "bg": "#d69d34", "fg": "#111111", "anchor": "e"},
            {"key": "sell", "title": "Продажа", "min": PICKER_FLASH_PRICE_COL_WIDTH, "bg": "#08aeca", "fg": "#111111", "anchor": "e"},
            {"key": "buy", "title": "Покупка", "min": PICKER_FLASH_PRICE_COL_WIDTH, "bg": "#08aeca", "fg": "#111111", "anchor": "e"},
            {"key": "sell_orders", "title": "Предл.", "min": PICKER_FLASH_ORDER_COL_WIDTH, "bg": "#181818", "fg": "#aeb7c6", "anchor": "e"},
            {"key": "buy_orders", "title": "Запр.", "min": PICKER_FLASH_ORDER_COL_WIDTH, "bg": "#181818", "fg": "#aeb7c6", "anchor": "e"},
            {"key": "roi", "title": "ROI (%)", "min": PICKER_FLASH_ROI_COL_WIDTH, "bg": "#7ac36f", "fg": "#111111", "anchor": "center"},
            {"key": "profit", "title": "Прибыль", "min": PICKER_PROFIT_COL_WIDTH, "bg": "#f0cf23", "fg": "#111111", "anchor": "w"},
        ]
        name_title = "Название"
        name_min_width = PICKER_NAME_COL_WIDTH
    else:
        value_columns = [
            {"key": "profit", "title": "Прибыль", "min": PICKER_DECOR_VALUE_COL_WIDTH, "bg": "#181818", "fg": "#aeb7c6", "anchor": "center"},
            {"key": "price", "title": "Цена", "min": PICKER_DECOR_VALUE_COL_WIDTH, "bg": "#181818", "fg": "#aeb7c6", "anchor": "center"},
            {"key": "roi", "title": "ROI", "min": PICKER_DECOR_VALUE_COL_WIDTH, "bg": "#181818", "fg": "#aeb7c6", "anchor": "center"},
        ]
        name_title = "Предмет"
        name_min_width = PICKER_DECOR_NAME_COL_WIDTH

    for column in value_columns:
        column["width"] = measure_picker_header(column["title"], column["min"])

    table_width = get_picker_table_inner_width()
    value_width = sum(column["width"] for column in value_columns)
    remaining_name_width = max(120, table_width - value_width)
    preferred_name_width = measure_picker_header(name_title, name_min_width)
    name_width = max(preferred_name_width, remaining_name_width)
    if name_width + value_width > table_width:
        name_width = remaining_name_width

    columns = [
        {
            "key": "name",
            "title": name_title,
            "width": name_width,
            "bg": "#181818",
            "fg": "#aeb7c6",
            "anchor": "w",
        },
        *value_columns,
    ]
    picker_columns_cache[kind] = columns
    return columns


def get_picker_canvas_font(size=9, weight="bold"):
    key = (size, weight)
    font = picker_font_cache.get(key)
    if font is None:
        font = tkfont.Font(family="Segoe UI", size=size, weight=weight)
        picker_font_cache[key] = font
    return font


def fit_picker_canvas_text(text, font, max_width):
    text = "" if text is None else str(text)
    if font.measure(text) <= max_width:
        return text

    ellipsis = "..."
    max_width = max(0, max_width - font.measure(ellipsis))
    while text and font.measure(text) > max_width:
        text = text[:-1]
    return text + ellipsis if text else ellipsis


def draw_picker_rounded_rect(x1, y1, x2, y2, radius, fill, outline=""):
    if picker_canvas is None:
        return

    radius = max(1, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    picker_canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline=outline)
    picker_canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline=outline)
    picker_canvas.create_oval(x1, y1, x1 + radius * 2, y1 + radius * 2, fill=fill, outline=outline)
    picker_canvas.create_oval(x2 - radius * 2, y1, x2, y1 + radius * 2, fill=fill, outline=outline)
    picker_canvas.create_oval(x1, y2 - radius * 2, x1 + radius * 2, y2, fill=fill, outline=outline)
    picker_canvas.create_oval(x2 - radius * 2, y2 - radius * 2, x2, y2, fill=fill, outline=outline)


def draw_picker_rounded_outline(x1, y1, x2, y2, radius, color, width=1):
    if picker_canvas is None:
        return

    radius = max(1, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    picker_canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=color, width=width)
    picker_canvas.create_line(x2, y1 + radius, x2, y2 - radius, fill=color, width=width)
    picker_canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=color, width=width)
    picker_canvas.create_line(x1, y1 + radius, x1, y2 - radius, fill=color, width=width)
    picker_canvas.create_arc(
        x1,
        y1,
        x1 + radius * 2,
        y1 + radius * 2,
        start=90,
        extent=90,
        style="arc",
        outline=color,
        width=width,
    )
    picker_canvas.create_arc(
        x2 - radius * 2,
        y1,
        x2,
        y1 + radius * 2,
        start=0,
        extent=90,
        style="arc",
        outline=color,
        width=width,
    )
    picker_canvas.create_arc(
        x2 - radius * 2,
        y2 - radius * 2,
        x2,
        y2,
        start=270,
        extent=90,
        style="arc",
        outline=color,
        width=width,
    )
    picker_canvas.create_arc(
        x1,
        y2 - radius * 2,
        x1 + radius * 2,
        y2,
        start=180,
        extent=90,
        style="arc",
        outline=color,
        width=width,
    )


def clear_picker_rows():
    global picker_display_rows, picker_total_content_height, picker_hover_row_index
    global picker_render_signature

    picker_display_rows = []
    picker_total_content_height = 0
    picker_hover_row_index = None
    picker_render_signature = None
    if picker_canvas is not None:
        picker_canvas.delete("all")


def get_picker_render_signature():
    return (id(picker_items), len(picker_items), picker_last_refresh)


def build_picker_display_rows():
    return build_picker_display_rows_data(
        picker_items,
        PICKER_HEADER_HEIGHT,
        PICKER_ROW_HEIGHT,
    )


def draw_picker_cell(
    x,
    y,
    width,
    height,
    text,
    fg="#dfe7f3",
    bg="#101418",
    anchor="e",
    font=None,
    padx=7,
):
    if picker_canvas is None:
        return

    font = font or get_picker_canvas_font(9, "bold")
    picker_canvas.create_rectangle(
        x,
        y,
        x + width,
        y + height,
        fill=bg,
        outline="#0d1115",
        width=1,
    )

    if anchor == "center":
        text_x = x + width / 2
        text_anchor = "center"
        max_width = width - padx * 2
    elif anchor == "w":
        text_x = x + padx
        text_anchor = "w"
        max_width = width - padx * 2
    else:
        text_x = x + width - padx
        text_anchor = "e"
        max_width = width - padx * 2

    picker_canvas.create_text(
        text_x,
        y + height / 2,
        text=fit_picker_canvas_text(text, font, max_width),
        fill=fg,
        anchor=text_anchor,
        font=font,
    )


def draw_picker_separator_canvas(row, width):
    y = row["y"]
    height = row["height"]
    text = row.get("text", "")
    font = get_picker_canvas_font(11, "bold")
    center_x = width / 2
    center_y = y + height / 2
    text_width = font.measure(text)
    line_gap = text_width / 2 + 18

    picker_canvas.create_rectangle(8, y + 7, width - 8, y + height - 6, fill="#181818", outline="")
    picker_canvas.create_line(8, center_y, center_x - line_gap, center_y, fill="#373737")
    picker_canvas.create_line(center_x + line_gap, center_y, width - 8, center_y, fill="#373737")
    picker_canvas.create_text(
        center_x,
        center_y,
        text=text,
        fill="#d7d7d7",
        anchor="center",
        font=font,
    )


def draw_picker_decor_prices_canvas(row, width):
    y = row["y"]
    height = row["height"]
    prices = row.get("prices", {})
    font = get_picker_canvas_font(9, "bold")
    x = 14

    picker_canvas.create_rectangle(8, y, width - 8, y + height, fill="#101418", outline="")
    title = "По цене продажи:"
    picker_canvas.create_text(
        x,
        y + height / 2,
        text=title,
        fill="#c7ced8",
        anchor="w",
        font=font,
    )
    x += font.measure(title) + 14

    rarity_ids = []
    for rarity_key in prices.keys():
        try:
            rarity_id = int(rarity_key)
        except Exception:
            continue
        if rarity_id not in rarity_ids:
            rarity_ids.append(rarity_id)

    for rarity_id in sorted(rarity_ids):
        price = get_price_for_rarity(prices, rarity_id)
        if price is None:
            continue

        style = get_rarity_style(rarity_id)
        label = f'{style["short"]} {format_picker_number(price)}'
        chip_width = font.measure(label) + 16
        if x + chip_width > width - 8:
            break

        picker_canvas.create_rectangle(
            x,
            y + 7,
            x + chip_width,
            y + height - 7,
            fill="#151b21",
            outline="",
        )
        picker_canvas.create_text(
            x + 8,
            y + height / 2,
            text=label,
            fill=style["color"],
            anchor="w",
            font=font,
        )
        x += chip_width + 6


def draw_picker_header_canvas(row):
    x = 8
    kind = row.get("kind", "")
    y = row["y"]
    font = get_picker_canvas_font(8, "bold")

    for column in get_picker_columns(kind):
        draw_picker_cell(
            x,
            y,
            column["width"],
            row["height"],
            column["title"],
            fg="#aeb7c6",
            bg="#181818",
            anchor=column["anchor"],
            font=font,
            padx=6,
        )
        x += column["width"]


def get_picker_hover_bg(kind, key, default_bg):
    if key == "history_sell":
        return "#e1aa3f"
    if kind == "flash" and key in ("sell", "buy"):
        return "#18bfd8"
    if kind == "flash" and key == "roi":
        return "#88d47e"
    if kind == "flash" and key == "profit":
        return "#f6d847"
    return "#16202a" if default_bg == "#101418" else default_bg


def draw_picker_item_canvas(row, is_hover=False, is_pending=False):
    item = row["item"]
    kind = row.get("kind", get_picker_item_kind(item))
    values = get_picker_item_cell_values(item)
    x = 8
    y = row["y"]
    font = get_picker_canvas_font(9, "bold")

    for column in get_picker_columns(kind):
        key = column["key"]
        fg = "#dfe7f3"
        bg = "#16202a" if is_hover else "#101418"
        anchor = column["anchor"]
        padx = 7

        if key == "name":
            fg = get_picker_rarity_color(item)
            anchor = "w"
            padx = 18 if is_hover else 9
        elif kind == "flash" and key == "history_sell":
            fg = "#111111"
            bg = "#d69d34"
        elif kind == "flash" and key in ("sell", "buy"):
            fg = "#111111"
            bg = "#08aeca"
        elif kind == "flash" and key == "roi":
            fg = "#111111"
            bg = "#7ac36f"
        elif kind == "flash" and key == "profit":
            fg = "#111111"
            bg = "#f0cf23"
            anchor = "w"
            padx = 8
        elif kind == "decor" and key in ("profit", "roi"):
            fg = "#67e86f"

        if is_hover:
            bg = get_picker_hover_bg(kind, key, bg)

        draw_picker_cell(
            x,
            y,
            column["width"],
            row["height"],
            values.get(key, ""),
            fg=fg,
            bg=bg,
            anchor=anchor,
            font=font,
            padx=padx,
        )
        x += column["width"]

    if is_hover:
        table_width = sum(column["width"] for column in get_picker_columns(kind))
        draw_picker_rounded_outline(
            8.5,
            y + 3.5,
            8 + table_width - 0.5,
            y + row["height"] - 3.5,
            7,
            color="#34424d",
            width=1,
        )
        draw_picker_rounded_rect(
            13,
            y + 10,
            15,
            y + row["height"] - 10,
            1,
            fill="#2f8cff" if is_pending else "#f0cf23",
        )


def draw_picker_canvas_rows():
    global picker_total_content_height, picker_render_signature

    if picker_canvas is None:
        return

    picker_canvas.delete("all")
    width = max(picker_current_width, picker_canvas.winfo_width())
    rows, total_height = build_picker_display_rows()

    picker_display_rows[:] = rows
    picker_total_content_height = total_height
    picker_canvas.create_rectangle(0, 0, width, max(total_height, 1), fill="#0b0f14", outline="")

    for row_index, row in enumerate(rows):
        row_type = row["type"]
        if row_type == "separator":
            draw_picker_separator_canvas(row, width)
        elif row_type == "decor_prices":
            draw_picker_decor_prices_canvas(row, width)
        elif row_type == "header":
            draw_picker_header_canvas(row)
        elif row_type == "item":
            draw_picker_item_canvas(
                row,
                is_hover=(
                    row_index == picker_hover_row_index
                    or row_index == picker_selected_row_index
                ),
                is_pending=(row_index == picker_pending_row_index),
            )

    picker_canvas.configure(scrollregion=(0, 0, width, max(total_height, 1)))
    picker_render_signature = get_picker_render_signature()


def show_picker_message(text):
    global picker_display_rows, picker_total_content_height, picker_hover_row_index
    global picker_selected_row_index, picker_render_signature

    if picker_canvas is None:
        return

    picker_hover_row_index = None
    picker_selected_row_index = None
    picker_display_rows = [{"type": "separator", "text": text, "y": 0, "height": 34}]
    picker_total_content_height = 34
    picker_render_signature = ("message", text)
    picker_canvas.delete("all")
    width = max(picker_current_width, picker_canvas.winfo_width())
    picker_canvas.create_rectangle(0, 0, width, 34, fill="#0b0f14", outline="")
    draw_picker_separator_canvas(picker_display_rows[0], width)
    picker_canvas.configure(scrollregion=(0, 0, width, 34))


def populate_picker(force=False):
    if picker_canvas is None:
        return

    if not force and picker_display_rows and picker_render_signature == get_picker_render_signature():
        if picker_status is not None:
            picker_status.configure(text="")
        if picker_window is not None and picker_window.state() != "withdrawn":
            position_picker_window()
        return

    clear_picker_rows()
    if not picker_items:
        show_picker_message("Загрузка...")
    else:
        draw_picker_canvas_rows()

    if picker_status is not None:
        picker_status.configure(text="")

    if picker_window is not None and picker_window.state() != "withdrawn":
        position_picker_window()


def get_picker_canvas_row_at(canvas_y):
    return get_picker_canvas_row_at_data(picker_display_rows, canvas_y)


def get_picker_canvas_item_at(event):
    if picker_canvas is None:
        return None, None

    canvas_y = picker_canvas.canvasy(event.y)
    index, row = get_picker_canvas_row_at(canvas_y)
    if not row or row.get("type") != "item":
        return index, None
    return index, row.get("item")


def on_picker_canvas_click(event):
    row_index, item = get_picker_canvas_item_at(event)
    if item:
        select_picker_row(row_index, paste=True)


def get_picker_item_row_indices():
    return get_picker_item_row_indices_data(picker_display_rows)


def scroll_picker_row_into_view(row):
    if picker_canvas is None or picker_total_content_height <= 0:
        return

    canvas_height = max(1, picker_canvas.winfo_height())
    top = picker_canvas.canvasy(0)
    bottom = top + canvas_height
    row_top = row["y"]
    row_bottom = row["y"] + row["height"]

    if row_top < top:
        picker_canvas.yview_moveto(row_top / max(1, picker_total_content_height))
    elif row_bottom > bottom:
        target = (row_bottom - canvas_height) / max(1, picker_total_content_height)
        picker_canvas.yview_moveto(max(0, target))


def select_picker_row(row_index, paste=True):
    global picker_selected_row_index, picker_hover_row_index

    if row_index is None or row_index < 0 or row_index >= len(picker_display_rows):
        return

    row = picker_display_rows[row_index]
    item = row.get("item")
    if row.get("type") != "item" or not item:
        return

    picker_selected_row_index = row_index
    picker_hover_row_index = row_index
    scroll_picker_row_into_view(row)
    draw_picker_hover(row_index)
    if paste:
        item_name = item["name"]
        if begin_pending_picker_selection(row_index, item_name):
            return

        cancel_pending_picker_selection(redraw=True)
        if not ensure_market_ready_for_picker_selection():
            return
        reset_market_action_stage()
        paste_item_name(item_name)


def move_picker_selection(direction):
    if picker_window is None or picker_window.state() == "withdrawn":
        return

    item_rows = get_picker_item_row_indices()
    if not item_rows:
        return

    if picker_selected_row_index not in item_rows:
        target_index = item_rows[0] if direction > 0 else item_rows[-1]
    else:
        current_position = item_rows.index(picker_selected_row_index)
        next_position = (current_position + direction) % len(item_rows)
        target_index = item_rows[next_position]

    select_picker_row(target_index, paste=True)


def get_picker_section_first_item_indices():
    section_rows = []
    current_section = None

    for row_index, row in enumerate(picker_display_rows):
        if row.get("type") == "separator":
            current_section = row.get("text")
            continue

        if row.get("type") != "item" or not row.get("item"):
            continue

        item_section = row["item"].get("section", current_section)
        if not section_rows or section_rows[-1][0] != item_section:
            section_rows.append((item_section, row_index))

    return [row_index for _section, row_index in section_rows]


def move_picker_selection_to_section(direction):
    if picker_window is None or picker_window.state() == "withdrawn":
        return

    section_first_rows = get_picker_section_first_item_indices()
    if not section_first_rows:
        return

    if picker_selected_row_index not in get_picker_item_row_indices():
        target_index = section_first_rows[0] if direction > 0 else section_first_rows[-1]
        select_picker_row(target_index, paste=True)
        return

    current_section_position = 0
    for position, row_index in enumerate(section_first_rows):
        if row_index <= picker_selected_row_index:
            current_section_position = position
        else:
            break

    if direction < 0 and picker_selected_row_index != section_first_rows[current_section_position]:
        target_position = current_section_position
    else:
        target_position = (current_section_position + direction) % len(section_first_rows)

    target_index = section_first_rows[target_position]
    select_picker_row(target_index, paste=True)


def draw_picker_hover(row_index):
    if picker_canvas is None:
        return

    top = picker_canvas.yview()[0]
    draw_picker_canvas_rows()
    try:
        picker_canvas.yview_moveto(top)
    except Exception:
        pass


def on_picker_canvas_motion(event):
    global picker_hover_row_index

    row_index, item = get_picker_canvas_item_at(event)
    new_index = row_index if item else None
    if new_index == picker_hover_row_index:
        return

    picker_hover_row_index = new_index
    draw_picker_hover(picker_hover_row_index)
    picker_canvas.configure(cursor="hand2" if item else "")


def on_picker_canvas_leave(event):
    global picker_hover_row_index

    picker_hover_row_index = None
    draw_picker_hover(None)
    if picker_canvas is not None:
        picker_canvas.configure(cursor="")


def create_picker_window():
    global picker_canvas, picker_canvas_window, picker_inner, picker_status
    global picker_timer_label, picker_status_label, picker_window, picker_hwnd

    if picker_window is not None:
        return

    picker_window = tk.Toplevel(root)
    picker_window.withdraw()
    picker_window.title(ITEM_PICKER_TITLE)
    picker_window.overrideredirect(True)
    picker_window.configure(bg="#30363d")
    picker_window.attributes("-topmost", True)
    picker_window.protocol("WM_DELETE_WINDOW", hide_picker)
    picker_window.bind("<Escape>", lambda event: hide_picker())
    picker_window.bind("<Up>", lambda event: move_picker_selection(-1))
    picker_window.bind("<Down>", lambda event: move_picker_selection(1))

    body = tk.Frame(picker_window, bg="#0b0f14")
    body.pack(fill="both", expand=True, padx=1, pady=1)

    timer_frame = tk.Frame(body, bg="#111417", height=PICKER_TIMER_HEIGHT)
    timer_frame.pack(side="top", fill="x")
    timer_frame.pack_propagate(False)

    picker_timer_label = tk.Label(
        timer_frame,
        text="До обновления: --:--",
        fg="#c7ced8",
        bg="#111417",
        anchor="center",
        font=("Segoe UI", 10, "bold"),
    )
    picker_timer_label.place(relx=0.5, rely=0.5, anchor="center")

    if PICKER_SHOW_STATUS:
        picker_status_label = tk.Label(
            timer_frame,
            text="",
            fg=PICKER_STATUS_FG,
            bg="#111417",
            anchor="e",
            font=("Segoe UI", 7, "bold"),
        )
        picker_status_label.place(relx=1.0, x=-10, rely=0.5, anchor="e")
    else:
        picker_status_label = None

    list_frame = tk.Frame(body, bg="#0b0f14")
    list_frame.pack(side="top", fill="both", expand=True)

    picker_canvas = tk.Canvas(
        list_frame,
        bg="#0b0f14",
        highlightthickness=0,
        bd=0,
    )
    picker_canvas.pack(side="left", fill="both", expand=True)
    picker_inner = None
    picker_canvas_window = None

    def on_canvas_configure(event):
        if picker_canvas_window is not None:
            picker_canvas.itemconfigure(picker_canvas_window, width=event.width)

    def on_mousewheel(event):
        picker_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    picker_canvas.bind("<Configure>", on_canvas_configure)
    picker_canvas.bind("<Button-1>", on_picker_canvas_click)
    picker_canvas.bind("<Motion>", on_picker_canvas_motion)
    picker_canvas.bind("<Leave>", on_picker_canvas_leave)
    picker_window.bind("<MouseWheel>", on_mousewheel)

    picker_status = None
    update_picker_timer_label()
    apply_no_activate(picker_window)
    picker_hwnd = get_window_hwnd(picker_window)


def set_picker_navigation_hotkeys(enabled):
    global picker_actions_enabled

    enabled = bool(enabled)
    if picker_actions_enabled == enabled:
        return

    picker_actions_enabled = enabled
    hotkeys.set_picker_navigation(enabled)


def should_enable_picker_navigation_hotkeys():
    return is_picker_window_visible_fast() and bool(get_picker_action_hwnd())


def sync_picker_navigation_hotkeys():
    set_picker_navigation_hotkeys(should_enable_picker_navigation_hotkeys())


def reset_picker_selection():
    global picker_selected_row_index, picker_hover_row_index

    picker_selected_row_index = None
    picker_hover_row_index = None


def hide_picker():
    if picker_window is not None and picker_window.state() != "withdrawn":
        picker_window.withdraw()
    set_picker_navigation_hotkeys(False)
    set_order_button_hold(False)
    reset_market_action_stage()


def show_picker(toggle=True):
    global picker_target_hwnd, picker_hwnd

    create_picker_window()

    if picker_window.state() != "withdrawn":
        if not toggle:
            clear_dead_picker_targets()
            if picker_target_hwnd and is_live_game_window(picker_target_hwnd):
                position_picker_window()
            else:
                hide_picker()
            return
        hide_picker()
        return

    clear_dead_picker_targets()
    foreground_hwnd = get_foreground_hwnd()
    if foreground_hwnd and not is_own_overlay_hwnd(foreground_hwnd) and is_game_window(foreground_hwnd):
        picker_target_hwnd = foreground_hwnd
    elif picker_target_hwnd and is_live_game_window(picker_target_hwnd):
        return
    elif last_alert_context_hwnd and is_live_game_window(last_alert_context_hwnd):
        picker_target_hwnd = last_alert_context_hwnd
        return
    else:
        return

    reset_market_action_stage()
    if not ensure_market_order_panel_closed():
        return
    if not open_game_market_details():
        return
    if picker_items:
        populate_picker()
    else:
        show_picker_message("Загрузка...")

    position_picker_window()
    show_tk_window_no_activate(picker_window)
    picker_hwnd = get_window_hwnd(picker_window)
    sync_picker_navigation_hotkeys()
    update_picker_timer_label()

    if not has_real_picker_items(picker_items) and not picker_refreshing:
        threading.Thread(
            target=lambda: refresh_picker_and_repaint(force=True),
            daemon=True,
        ).start()


def right_shift_worker():
    global right_arrow_hold_active, right_arrow_hold_compensated, right_arrow_press_at
    global right_arrow_was_down, right_ctrl_was_down
    global up_arrow_was_down, up_arrow_press_at, up_arrow_hold_triggered
    global down_arrow_was_down, down_arrow_press_at, down_arrow_hold_triggered
    global salvage_delete_was_down

    while True:
        try:
            picker_visible = picker_actions_enabled and is_picker_window_visible_fast()

            up_down = is_virtual_key_down(VK_UP)
            if picker_visible and up_down and not up_arrow_was_down:
                up_arrow_was_down = True
                up_arrow_press_at = time.monotonic()
                up_arrow_hold_triggered = False
            if picker_visible and up_down and up_arrow_was_down and not up_arrow_hold_triggered:
                if time.monotonic() - up_arrow_press_at >= PICKER_ARROW_EDGE_HOLD_SECONDS:
                    up_arrow_hold_triggered = True
                    root.after(0, lambda: move_picker_selection_to_section(-1))
            if not picker_visible or not up_down:
                up_arrow_was_down = False
                up_arrow_hold_triggered = False

            down_down = is_virtual_key_down(VK_DOWN)
            if picker_visible and down_down and not down_arrow_was_down:
                down_arrow_was_down = True
                down_arrow_press_at = time.monotonic()
                down_arrow_hold_triggered = False
            if picker_visible and down_down and down_arrow_was_down and not down_arrow_hold_triggered:
                if time.monotonic() - down_arrow_press_at >= PICKER_ARROW_EDGE_HOLD_SECONDS:
                    down_arrow_hold_triggered = True
                    root.after(0, lambda: move_picker_selection_to_section(1))
            if not picker_visible or not down_down:
                down_arrow_was_down = False
                down_arrow_hold_triggered = False

            right_down = is_virtual_key_down(VK_RIGHT)

            if picker_visible and right_down and not right_arrow_was_down:
                right_arrow_was_down = True
                right_arrow_press_at = time.monotonic()
                right_arrow_hold_active = False
                right_arrow_hold_compensated = False

            if picker_visible and right_down and right_arrow_was_down and not right_arrow_hold_active:
                held_for = time.monotonic() - right_arrow_press_at
                if held_for >= RIGHT_ARROW_HOLD_SECONDS and get_picker_action_hwnd():
                    stage = detect_market_action_stage()
                    if stage == STAGE_QUANTITY:
                        if (
                            right_arrow_last_action_stage == STAGE_QUANTITY
                            and not right_arrow_hold_compensated
                        ):
                            decrease_market_item_quantity()
                            right_arrow_hold_compensated = True
                        if set_order_button_hold(True):
                            right_arrow_hold_active = True

            if (not picker_visible or not right_down) and (right_arrow_was_down or right_arrow_hold_active):
                if right_arrow_hold_active or right_shift_order_down:
                    set_order_button_hold(False)
                right_arrow_was_down = False
                right_arrow_hold_active = False
                right_arrow_hold_compensated = False

            right_ctrl_down = is_virtual_key_down(VK_RCONTROL)
            if right_ctrl_down and not right_ctrl_was_down:
                if picker_visible and get_picker_action_hwnd():
                    handle_right_ctrl_escape()
            right_ctrl_was_down = right_ctrl_down

            end_down = is_virtual_key_down(VK_END)
            end_ready_to_release = (
                not picker_end_latched
                or time.monotonic() - picker_end_press_at >= PICKER_END_RELEASE_GRACE_SECONDS
            )
            if not end_down and end_ready_to_release:
                finish_picker_end_press()

            if salvage_pair_armed and is_any_non_delete_key_down():
                reset_salvage_del_pair("other key")

            delete_down = is_virtual_key_down(VK_DELETE)
            if delete_down and not salvage_delete_was_down:
                salvage_delete_was_down = True
                root.after(0, lambda: handle_salvage_del_press(ignore_latch=True))
            elif not delete_down:
                salvage_delete_was_down = False
        except Exception as e:
            log_error("right_shift", f"Right Shift worker failed: {e}")

        time.sleep(max(0.005, RIGHT_SHIFT_POLL_SECONDS))


def check_hotkeys():
    close_picker_if_target_gone()

    for event in hotkeys.drain_events():
        if event == "picker":
            show_picker()
        elif event == "picker_end_open":
            handle_picker_end_hotkey()
        elif event == "salvage_toggle":
            handle_salvage_del_press()
        elif event == "picker_up":
            if should_enable_picker_navigation_hotkeys():
                if not up_arrow_hold_triggered:
                    move_picker_selection(-1)
            else:
                sync_picker_navigation_hotkeys()
        elif event == "picker_down":
            if should_enable_picker_navigation_hotkeys():
                if not down_arrow_hold_triggered:
                    move_picker_selection(1)
            else:
                sync_picker_navigation_hotkeys()
        elif event == "picker_right":
            if should_enable_picker_navigation_hotkeys():
                if not right_arrow_hold_active:
                    handle_market_action_right()
            else:
                sync_picker_navigation_hotkeys()
        elif event == "picker_left":
            if should_enable_picker_navigation_hotkeys():
                handle_market_action_left()
            else:
                sync_picker_navigation_hotkeys()

    sync_picker_navigation_hotkeys()
    root.after(50, check_hotkeys)


def keep_picker_on_top():
    if picker_window is None or picker_window.state() == "withdrawn":
        return
    if not picker_target_hwnd or not is_live_game_window(picker_target_hwnd):
        return

    foreground_hwnd = get_foreground_hwnd()
    if not foreground_hwnd or not is_game_window(foreground_hwnd):
        return

    try:
        position_picker_window()
        picker_window.attributes("-topmost", True)
        picker_window.update_idletasks()
        hwnd = get_window_hwnd(picker_window)
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            -1,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
    except Exception:
        pass


def keep_on_top():
    try:
        keep_picker_on_top()

        if primary_monitor_alert is not None and primary_monitor_alert.state() != "withdrawn":
            primary_hwnd = get_window_hwnd(primary_monitor_alert)
            ctypes.windll.user32.SetWindowPos(
                primary_hwnd,
                -1,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )

        if second_monitor_alert is not None and second_monitor_alert.state() != "withdrawn":
            second_hwnd = get_window_hwnd(second_monitor_alert)
            ctypes.windll.user32.SetWindowPos(
                second_hwnd,
                -1,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )

        hwnd = get_window_hwnd(root)
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            -1,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )
    except Exception:
        pass

    root.after(1000, keep_on_top)


def make_task_manager_app():
    configure_task_manager_app(root, APP_ID)


def show_overlay():
    show_overlay_window(root)


def apply_window_region():
    apply_overlay_window_region(root)


def create_primary_monitor_alert():
    global primary_monitor_alert, primary_monitor_canvas, primary_monitor_rect

    primary_monitor_rect = get_primary_monitor_rect()
    if primary_monitor_rect is None:
        log_error("monitor", "Primary monitor alert was not created: no monitor rect.")
        return

    primary_monitor_alert, primary_monitor_canvas, border_items = create_monitor_alert_window(
        root,
        primary_monitor_rect,
        "Crossout Timer Primary Monitor Alert",
        TRANSPARENT_BG,
        ALERT_BG,
        PRIMARY_MONITOR_ALPHA,
        PRIMARY_MONITOR_BORDER_THICKNESS,
        log_error,
        "primary_monitor_window",
        "Primary monitor window setup failed",
    )
    primary_monitor_border_items.clear()
    primary_monitor_border_items.extend(border_items)


def create_second_monitor_alert():
    global second_monitor_alert, second_monitor_canvas, second_monitor_rect

    second_monitor_rect = get_second_monitor_rect(ALERT_MONITOR_INDEX)
    if second_monitor_rect is None:
        log_error("monitor", "Second monitor alert was not created: no monitor rect.")
        return

    second_monitor_alert, second_monitor_canvas, border_items = create_monitor_alert_window(
        root,
        second_monitor_rect,
        "Crossout Timer Second Monitor Alert",
        TRANSPARENT_BG,
        ALERT_BG,
        SECOND_MONITOR_ALPHA,
        SECOND_MONITOR_BORDER_THICKNESS,
        log_error,
        "second_monitor_window",
        "Second monitor window setup failed",
    )
    second_monitor_border_items.clear()
    second_monitor_border_items.extend(border_items)


def center_notch():
    root.geometry(f"{overlay_width}x{notch_height}+0+0")
    root.update_idletasks()
    apply_window_region()


def configure_dpi_sizes():
    global font_pixels, notch_height, notch_radius, notch_width, notch_x, overlay_width

    (
        overlay_width,
        notch_x,
        notch_width,
        notch_height,
        notch_radius,
        font_pixels,
    ) = configure_notch_dpi_sizes(
        root,
        canvas,
        BASE_NOTCH_WIDTH,
        BASE_NOTCH_HEIGHT,
        BASE_NOTCH_RADIUS,
        BASE_FONT_PIXELS,
    )


def draw_notch():
    global alert_strip, notch_items, timer_text

    alert_strip, notch_items, timer_text = create_notch_items(
        canvas,
        overlay_width,
        notch_x,
        notch_width,
        notch_height,
        notch_radius,
        ALERT_BG,
        NORMAL_BG,
        NORMAL_FG,
        font_pixels,
    )


def main():
    global root, canvas

    enable_dpi_awareness()
    acquire_single_instance()
    hide_console()

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass

    root = tk.Tk()
    root.withdraw()
    root.title("Crossout Timer")

# Окно поверх всех окон
    root.attributes("-topmost", True)
    root.wm_attributes("-topmost", 1)

# Без рамки Windows
    root.overrideredirect(True)
    root.configure(bg=TRANSPARENT_BG)
    root.attributes("-transparentcolor", TRANSPARENT_BG)
    root.attributes("-alpha", NORMAL_ALPHA)

    if SHOW_NOTCH_OVERLAY:
        canvas = tk.Canvas(
            root,
            width=notch_width,
            height=notch_height,
            bg=TRANSPARENT_BG,
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill="both", expand=True)
        configure_dpi_sizes()
        draw_notch()
        center_notch()
    create_primary_monitor_alert()
    create_second_monitor_alert()
    make_task_manager_app()
    if SHOW_NOTCH_OVERLAY:
        show_overlay()
    root.after(500, make_task_manager_app)

    load_picker_cache()
    create_picker_window()
    if picker_items:
        populate_picker()
    threading.Thread(target=timer_worker, daemon=True).start()
    hotkeys.start()
    threading.Thread(target=right_shift_worker, daemon=True).start()
    threading.Thread(target=picker_refresh_worker, daemon=True).start()

    keep_on_top()
    update_label()
    check_hotkeys()
    root.mainloop()
