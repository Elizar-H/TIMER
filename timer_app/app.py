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
from timer_app.config import DEFAULT_SETTINGS, load_settings, setting
from timer_app.coordinates import (
    DEFAULT_COORDINATES,
    apply_legacy_coordinate_settings,
    load_coordinates,
)
from timer_app.crossout import (
    FLASH_URL,
    RARITY_STYLES,
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
from timer_app.log import append_log_line, log_error
from timer_app.paths import COORDINATES_PATH, SETTINGS_PATH
from timer_app.picker.cache import (
    load_picker_cache as load_picker_cache_file,
    save_picker_cache as save_picker_cache_file,
)
from timer_app.winapi import (
    MOUSEEVENTF_LEFTDOWN,
    MOUSEEVENTF_LEFTUP,
    MSG,
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
    VK_LEFT,
    VK_RCONTROL,
    VK_RETURN,
    VK_RIGHT,
    VK_UP,
    VK_V,
    WM_APP_HOTKEY_COMMAND,
    WM_HOTKEY,
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
    geometry_from_rect,
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
GAME_SECTION_CLICK_DELAY_SECONDS = 0.045
SALVAGE_ITEM_ROW_STEP_RATIO = 0.233
SALVAGE_CONFIRM_HOLD_SECONDS = 0.564
SALVAGE_CONFIRM_WAIT_SECONDS = 0.25
SALVAGE_AFTER_CONFIRM_SECONDS = 0.12
SALVAGE_STEP_DELAY_SECONDS = 0.035
SALVAGE_ITEM_HOVER_DELAY_SECONDS = 0.03
SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS = 0.18
SALVAGE_POST_RIGHT_CLICK_DELAY_SECONDS = 0.08
SALVAGE_POST_MENU_CLICK_DELAY_SECONDS = 0.08
SALVAGE_POST_ALL_CLICK_DELAY_SECONDS = 0.04
SALVAGE_MOUSE_CANCEL_THRESHOLD_PIXELS = 12
PICKER_OPEN_HOLD_SECONDS = 0.14
PICKER_END_RELEASE_GRACE_SECONDS = 0.05
RIGHT_ARROW_HOLD_SECONDS = 0.09
PICKER_ARROW_EDGE_HOLD_SECONDS = 0.20
MARKET_ACTION_STAGE_MAX_AGE_SECONDS = 1.10
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
PICKER_HOTKEY_ID = 7311
PICKER_OPEN_END_HOTKEY_ID = 7316
PICKER_HOTKEY_VK = 0xC0
WM_HOTKEY = 0x0312
WM_APP_HOTKEY_COMMAND = 0x8001
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
    global SALVAGE_POST_MENU_CLICK_DELAY_SECONDS, SALVAGE_POST_ALL_CLICK_DELAY_SECONDS
    global SALVAGE_MOUSE_CANCEL_THRESHOLD_PIXELS
    global PICKER_END_RELEASE_GRACE_SECONDS, RIGHT_ARROW_HOLD_SECONDS
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

SALVAGE_HOTKEY_ID = 7317
PICKER_UP_HOTKEY_ID = 7312
PICKER_DOWN_HOTKEY_ID = 7313
PICKER_RIGHT_HOTKEY_ID = 7314
PICKER_LEFT_HOTKEY_ID = 7315
PICKER_ACTION_HOTKEYS = (
    (PICKER_UP_HOTKEY_ID, VK_UP, "picker_up"),
    (PICKER_DOWN_HOTKEY_ID, VK_DOWN, "picker_down"),
    (PICKER_RIGHT_HOTKEY_ID, VK_RIGHT, "picker_right"),
    (PICKER_LEFT_HOTKEY_ID, VK_LEFT, "picker_left"),
)

q = queue.Queue()
hotkey_q = queue.Queue()
hotkey_command_q = queue.Queue()
hotkey_thread_id = None
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
picker_font_cache = {}
picker_columns_cache = {}
picker_last_refresh = 0
picker_last_success_at = None
picker_last_refresh_ms = None
picker_last_item_count = 0
picker_last_refresh_note = "кэш"
picker_refresh_lock = threading.Lock()
picker_fast_refresh_lock = threading.Lock()
picker_refreshing = False
picker_navigation_hotkeys_registered = False
picker_actions_enabled = False
right_shift_order_down = False
right_ctrl_was_down = False
right_arrow_was_down = False
right_arrow_press_at = 0
right_arrow_hold_active = False
right_arrow_hold_compensated = False
right_arrow_last_action_stage = None
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
picker_end_hold_triggered = False
picker_end_latched = False
picker_end_press_at = 0
picker_end_ignore_until = 0
salvage_running = False
salvage_stop_event = threading.Event()
salvage_expected_cursor_pos = None
salvage_last_item_right_click_at = 0
market_action_stage = "open_card"
market_action_stage_ready_at = 0
market_action_stage_updated_at = 0
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
    "make_task_manager_app",
    "show_overlay",
    "apply_window_region",
    "configure_dpi_sizes",
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


def has_real_picker_items(items):
    return any(
        isinstance(item, dict)
        and not item.get("separator")
        and not item.get("decor_prices")
        for item in items or []
    )


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


def count_real_picker_items(items):
    return sum(
        1
        for item in items or []
        if isinstance(item, dict)
        and not item.get("separator")
        and not item.get("decor_prices")
    )


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
    cycle = sum(duration for _, duration, _ in ALERT_PULSE_PATTERN)
    position = time.monotonic() % cycle

    for mode, duration, peak in ALERT_PULSE_PATTERN:
        if position < duration:
            if duration <= 0:
                return peak

            progress = position / duration
            eased = progress * progress * (3 - 2 * progress)
            if mode == "rise":
                return peak * eased
            if mode == "fall":
                return peak * (1 - eased)
            return peak

        position -= duration

    return 0


def get_pulse_alpha(min_alpha, max_alpha, pulse):
    pulse = max(0, min(1, pulse))
    return min_alpha + (max_alpha - min_alpha) * pulse


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

    for item in second_monitor_border_items:
        second_monitor_canvas.itemconfig(item, fill=color)


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


def note_salvage_cursor_pos():
    global salvage_expected_cursor_pos

    salvage_expected_cursor_pos = get_cursor_pos()


def mark_salvage_mouse_cancel(stop_event):
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

    dx = abs(current_pos[0] - salvage_expected_cursor_pos[0])
    dy = abs(current_pos[1] - salvage_expected_cursor_pos[1])
    return dx > SALVAGE_MOUSE_CANCEL_THRESHOLD_PIXELS or dy > SALVAGE_MOUSE_CANCEL_THRESHOLD_PIXELS


def hold_left_mouse(seconds, stop_event=None, mouse_guard=False):
    if not send_mouse_button(MOUSEEVENTF_LEFTDOWN):
        return False

    try:
        end_at = time.monotonic() + max(0, seconds)
        while time.monotonic() < end_at:
            if stop_event is not None and stop_event.is_set():
                return False
            if mouse_guard and salvage_cursor_moved_by_user():
                mark_salvage_mouse_cancel(stop_event)
                return False
            time.sleep(0.01)
        return True
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


def count_orange_button_samples(x_ratio, y_ratio):
    hwnd = get_picker_action_hwnd()
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


def is_game_button_visible(x_ratio, y_ratio):
    return count_orange_button_samples(x_ratio, y_ratio) >= GAME_BUTTON_SAMPLE_REQUIRED_HITS


def is_game_point_visible(point_name):
    return is_game_button_visible(*game.point(point_name))


def detect_market_action_stage():
    if is_game_point_visible("market.order_button"):
        return "quantity"
    if is_game_point_visible("market.buy_button"):
        return "buy"
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


def open_game_market_details():
    clicked_market = game.click("market.market_tab")
    time.sleep(GAME_SECTION_CLICK_DELAY_SECONDS)
    clicked_details = game.click("market.details_tab")
    if clicked_market or clicked_details:
        reset_market_action_stage()
    return clicked_market and clicked_details


def set_market_action_stage(stage, ready_at=0):
    global market_action_stage, market_action_stage_ready_at, market_action_stage_updated_at

    market_action_stage = stage
    market_action_stage_ready_at = ready_at
    market_action_stage_updated_at = time.monotonic()


def reset_market_action_stage():
    set_market_action_stage("open_card", 0)


def get_market_action_stage():
    global market_action_stage, market_action_stage_ready_at

    now = time.monotonic()
    if (
        market_action_stage != "open_card"
        and market_action_stage_updated_at
        and now - market_action_stage_updated_at > MARKET_ACTION_STAGE_MAX_AGE_SECONDS
    ):
        reset_market_action_stage()
        return market_action_stage

    if market_action_stage == "opening_card" and now >= market_action_stage_ready_at:
        set_market_action_stage("buy", 0)
    elif market_action_stage == "opening_buy_dialog" and now >= market_action_stage_ready_at:
        set_market_action_stage("quantity", 0)

    return market_action_stage


def handle_market_action_right():
    global right_arrow_last_action_stage

    now = time.monotonic()
    detected_stage = detect_market_action_stage()

    if detected_stage == "quantity":
        right_arrow_last_action_stage = "quantity"
        set_market_action_stage("quantity", 0)
        return increase_market_item_quantity()

    if detected_stage == "buy":
        right_arrow_last_action_stage = "buy"
        ok = buy_current_market_item()
        if ok:
            set_market_action_stage("opening_buy_dialog", now + GAME_BUY_TO_QUANTITY_DELAY_SECONDS)
        return ok

    if get_market_action_stage() == "opening_buy_dialog":
        return False

    right_arrow_last_action_stage = "open_card"
    ok = open_selected_market_card()
    if ok and market_action_stage != "opening_card":
        set_market_action_stage("opening_card", now + GAME_OPEN_TO_BUY_DELAY_SECONDS)
    return ok


def handle_market_action_left():
    reset_market_action_stage()
    return go_back_from_market_card()


def resolve_picker_end_hold():
    global picker_end_hold_pending, picker_end_hold_triggered

    picker_end_hold_pending = False
    if picker_end_hold_triggered:
        return

    if is_virtual_key_down(VK_END):
        picker_end_hold_triggered = True
        if get_or_restore_game_hwnd():
            open_game_market_details()
            show_picker(toggle=False)


def schedule_picker_end_hold_check():
    global picker_end_hold_pending

    if picker_end_hold_pending or picker_end_hold_triggered:
        return

    picker_end_hold_pending = True
    root.after(max(1, int(PICKER_OPEN_HOLD_SECONDS * 1000)), resolve_picker_end_hold)


def handle_picker_end_hotkey():
    global picker_end_press_active, picker_end_press_was_open, picker_end_hold_triggered
    global picker_end_latched, picker_end_press_at

    if time.monotonic() < picker_end_ignore_until:
        return

    if picker_end_latched or picker_end_press_active:
        return

    picker_end_latched = True
    picker_end_press_at = time.monotonic()
    picker_end_press_active = True
    picker_end_press_was_open = is_picker_open()
    picker_end_hold_triggered = False

    if not picker_end_press_was_open:
        show_picker(toggle=False)

    schedule_picker_end_hold_check()


def finish_picker_end_press():
    global picker_end_press_active, picker_end_hold_pending, picker_end_latched
    global picker_end_ignore_until

    if not picker_end_press_active:
        picker_end_latched = False
        return

    picker_end_press_active = False
    picker_end_hold_pending = False
    picker_end_latched = False

    if picker_end_hold_triggered:
        picker_end_ignore_until = time.monotonic() + 0.35
        return

    if picker_end_press_was_open:
        hide_picker()
    elif not is_picker_open():
        show_picker(toggle=False)


def handle_right_ctrl_escape():
    if detect_market_action_stage() != "quantity":
        return False
    return decrease_market_item_quantity()


def sleep_with_stop(seconds, stop_event, mouse_guard=False):
    end_at = time.monotonic() + max(0, seconds)
    while time.monotonic() < end_at:
        if stop_event.is_set():
            return False
        if mouse_guard and salvage_cursor_moved_by_user():
            mark_salvage_mouse_cancel(stop_event)
            return False
        time.sleep(min(0.02, max(0, end_at - time.monotonic())))
    return not stop_event.is_set()


def salvage_click(point_name, stop_event, right=False):
    if stop_event.is_set() or not get_picker_action_hwnd():
        return False
    ok = game.right_click(point_name) if right else game.click(point_name)
    if ok:
        note_salvage_cursor_pos()
        sleep_with_stop(SALVAGE_STEP_DELAY_SECONDS, stop_event, mouse_guard=True)
    return ok


def salvage_click_no_stop(point_name):
    if not get_picker_action_hwnd():
        return False
    ok = game.click(point_name)
    if ok:
        time.sleep(SALVAGE_STEP_DELAY_SECONDS)
    return ok


def salvage_right_click_item(point_name, stop_event):
    global salvage_last_item_right_click_at

    if stop_event.is_set() or not get_picker_action_hwnd():
        return False

    if not game.move_to(point_name):
        return False
    note_salvage_cursor_pos()
    if not sleep_with_stop(SALVAGE_ITEM_HOVER_DELAY_SECONDS, stop_event, mouse_guard=True):
        return False
    since_last_right_click = time.monotonic() - salvage_last_item_right_click_at
    if since_last_right_click < SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS:
        wait_time = SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS - since_last_right_click
        if not sleep_with_stop(wait_time, stop_event, mouse_guard=True):
            return False
    if not send_mouse_right_click(MOUSE_CLICK_DELAY):
        return False
    salvage_last_item_right_click_at = time.monotonic()
    note_salvage_cursor_pos()
    return sleep_with_stop(SALVAGE_POST_RIGHT_CLICK_DELAY_SECONDS, stop_event, mouse_guard=True)


def salvage_confirm_available():
    return is_game_point_visible("salvage.confirm_button")


def restore_salvage_sort_type():
    if not get_picker_action_hwnd():
        return False

    opened = salvage_click_no_stop("salvage.sort_dropdown")
    if not opened:
        return False

    return salvage_click_no_stop("salvage.sort_type_option")


def run_salvage_loop(stop_event):
    global salvage_running, salvage_expected_cursor_pos, salvage_last_item_right_click_at

    try:
        hwnd = get_picker_action_hwnd()
        if not hwnd:
            return

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

        while not stop_event.is_set() and get_picker_action_hwnd():
            if not salvage_right_click_item("salvage.first_item", stop_event):
                break
            if not salvage_click("salvage.context_disassemble", stop_event):
                break
            if not sleep_with_stop(SALVAGE_POST_MENU_CLICK_DELAY_SECONDS, stop_event, mouse_guard=True):
                break

            if not sleep_with_stop(SALVAGE_CONFIRM_WAIT_SECONDS, stop_event, mouse_guard=True):
                break
            if not salvage_confirm_available():
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
    except Exception as e:
        log_error("salvage", f"Salvage loop failed: {e}")
    finally:
        was_cancelled = stop_event.is_set()
        send_mouse_button(MOUSEEVENTF_LEFTUP)
        if was_cancelled:
            restore_salvage_sort_type()
        salvage_running = False
        stop_event.clear()


def toggle_salvage_loop():
    global salvage_running

    if salvage_running:
        salvage_stop_event.set()
        send_mouse_button(MOUSEEVENTF_LEFTUP)
        return

    if not get_picker_action_hwnd():
        return

    salvage_stop_event.clear()
    salvage_running = True
    threading.Thread(target=run_salvage_loop, args=(salvage_stop_event,), daemon=True).start()


def set_order_button_hold(is_down):
    global right_shift_order_down

    if is_down == right_shift_order_down:
        return True

    if is_down:
        if detect_market_action_stage() != "quantity":
            return False
        if not game.move_to("market.order_button"):
            return False
        ok = send_mouse_button(MOUSEEVENTF_LEFTDOWN)
        right_shift_order_down = ok
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


def normalize_game_search_text(text):
    return re.sub(r"[\u00a0\u202f\u2007]+", " ", str(text)).strip()


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
    total_height = get_picker_total_height(max_available_height)

    x = min(max(left, x), right - PICKER_WIDTH)
    y = min(max(top, y), bottom - total_height)

    picker_window.geometry(f"{PICKER_WIDTH}x{total_height}{x:+d}{y:+d}")


def get_picker_item_kind(item):
    kind = item.get("kind")
    if kind:
        return kind
    if "relative_spread" in item:
        return "flash"
    if item.get("profit") is not None:
        return "decor"
    return ""


def format_picker_profit(item):
    profit = item.get("profit", item.get("score"))
    if profit is None:
        return ""

    sign = "+" if profit > 0 else ""
    return f"{sign}{profit:.2f}"


def format_picker_number(value):
    if value is None:
        return ""
    try:
        return f"{float(value):.2f}"
    except Exception:
        return ""


def format_picker_int(value):
    if value is None:
        return ""
    try:
        return str(int(value))
    except Exception:
        return ""


def format_picker_roi(item):
    roi = item.get("roi")
    if roi is None:
        return ""
    try:
        sign = "+" if get_picker_item_kind(item) == "decor" and roi > 0 else ""
        return f"{sign}{float(roi):.2f}%"
    except Exception:
        return ""


def get_rarity_style(rarity_id):
    try:
        rarity_id = int(rarity_id)
    except Exception:
        return {"name": "", "short": "", "color": "#f0cf23"}
    return RARITY_STYLES.get(
        rarity_id,
        {"name": "", "short": "", "color": "#f0cf23"},
    )


def get_picker_rarity_color(item):
    return get_rarity_style(item.get("rarity_id"))["color"]


def measure_picker_header(text, minimum):
    try:
        font = tkfont.Font(family="Segoe UI", size=8, weight="bold")
        return max(minimum, font.measure(text) + 24)
    except Exception:
        return minimum


def get_picker_table_inner_width():
    return PICKER_WIDTH - 18


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


def get_price_for_rarity(prices, rarity_id):
    return prices.get(rarity_id, prices.get(str(rarity_id)))


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
    rows = []
    y = 0
    current_section = None
    header_section = None

    def add_row(row_type, height, **data):
        nonlocal y
        row = {"type": row_type, "y": y, "height": height, **data}
        rows.append(row)
        y += height

    for item in picker_items:
        if item.get("separator"):
            add_row("separator", 34, text=item.get("section", ""))
            current_section = item.get("section")
            header_section = None
            continue

        if item.get("decor_prices"):
            add_row("decor_prices", 42, prices=item.get("prices", {}))
            continue

        if item.get("section") != current_section:
            add_row("separator", 34, text=item.get("section", ""))
            current_section = item.get("section")
            header_section = None

        if current_section != header_section:
            add_row("header", PICKER_HEADER_HEIGHT, kind=get_picker_item_kind(item))
            header_section = current_section

        add_row("item", PICKER_ROW_HEIGHT, item=item, kind=get_picker_item_kind(item))

    return rows, y


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


def get_picker_item_cell_values(item):
    kind = get_picker_item_kind(item)
    if kind == "flash":
        return {
            "name": item.get("name", ""),
            "history_sell": format_picker_number(item.get("history_sell")),
            "sell": format_picker_number(item.get("sell")),
            "buy": format_picker_number(item.get("buy")),
            "sell_orders": format_picker_int(item.get("sell_orders")),
            "buy_orders": format_picker_int(item.get("buy_orders")),
            "roi": format_picker_roi(item),
            "profit": format_picker_profit(item),
        }

    return {
        "name": item.get("name", ""),
        "profit": format_picker_profit(item),
        "price": format_picker_number(item.get("price")),
        "roi": format_picker_roi(item),
    }


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


def draw_picker_item_canvas(row, is_hover=False):
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
            fill="#f0cf23",
        )


def draw_picker_canvas_rows():
    global picker_total_content_height, picker_render_signature

    if picker_canvas is None:
        return

    picker_canvas.delete("all")
    width = max(PICKER_WIDTH, picker_canvas.winfo_width())
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
    width = max(PICKER_WIDTH, picker_canvas.winfo_width())
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
    for index, row in enumerate(picker_display_rows):
        if row["y"] <= canvas_y < row["y"] + row["height"]:
            return index, row
    return None, None


def get_picker_canvas_item_at(event):
    if picker_canvas is None:
        return None, None

    canvas_y = picker_canvas.canvasy(event.y)
    index, row = get_picker_canvas_row_at(canvas_y)
    if not row or row.get("type") != "item":
        return index, None
    return index, row.get("item")


def on_picker_canvas_click(event):
    global picker_selected_row_index

    row_index, item = get_picker_canvas_item_at(event)
    if item:
        picker_selected_row_index = row_index
        draw_picker_hover(row_index)
        reset_market_action_stage()
        paste_item_name(item["name"])


def get_picker_item_row_indices():
    return [
        index
        for index, row in enumerate(picker_display_rows)
        if row.get("type") == "item" and row.get("item")
    ]


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
        reset_market_action_stage()
        paste_item_name(item["name"])


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


def move_picker_selection_to_edge(direction):
    if picker_window is None or picker_window.state() == "withdrawn":
        return

    item_rows = get_picker_item_row_indices()
    if not item_rows:
        return

    target_index = item_rows[0] if direction < 0 else item_rows[-1]
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


def wake_hotkey_worker():
    if hotkey_thread_id:
        try:
            ctypes.windll.user32.PostThreadMessageW(
                hotkey_thread_id,
                WM_APP_HOTKEY_COMMAND,
                0,
                0,
            )
        except Exception:
            pass


def send_hotkey_worker_command(command):
    hotkey_command_q.put(command)
    wake_hotkey_worker()


def set_picker_navigation_hotkeys(enabled):
    global picker_actions_enabled

    enabled = bool(enabled)
    if picker_actions_enabled == enabled:
        return

    picker_actions_enabled = enabled
    send_hotkey_worker_command("register_picker_nav" if enabled else "unregister_picker_nav")


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
    else:
        picker_target_hwnd = None
        return

    reset_market_action_stage()
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


def process_hotkey_worker_commands():
    global picker_navigation_hotkeys_registered

    while not hotkey_command_q.empty():
        command = hotkey_command_q.get()

        if command == "register_picker_nav" and not picker_navigation_hotkeys_registered:
            registered_ids = []
            for hotkey_id, vk, _event_name in PICKER_ACTION_HOTKEYS:
                if ctypes.windll.user32.RegisterHotKey(None, hotkey_id, 0, vk):
                    registered_ids.append(hotkey_id)
                else:
                    break

            picker_navigation_hotkeys_registered = len(registered_ids) == len(PICKER_ACTION_HOTKEYS)
            if not picker_navigation_hotkeys_registered:
                for hotkey_id in registered_ids:
                    ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
                log_error("picker_nav_hotkey", "RegisterHotKey failed for picker action keys")

        elif command == "unregister_picker_nav" and picker_navigation_hotkeys_registered:
            for hotkey_id, _vk, _event_name in PICKER_ACTION_HOTKEYS:
                ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
            picker_navigation_hotkeys_registered = False


def hotkey_worker():
    global hotkey_thread_id

    try:
        hotkey_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        if not ctypes.windll.user32.RegisterHotKey(
            None,
            PICKER_HOTKEY_ID,
            0,
            PICKER_HOTKEY_VK,
        ):
            log_error("hotkey", "RegisterHotKey failed for ё / `")
            return
        if not ctypes.windll.user32.RegisterHotKey(
            None,
            PICKER_OPEN_END_HOTKEY_ID,
            0,
            VK_END,
        ):
            log_error("hotkey", "RegisterHotKey failed for End")
        if not ctypes.windll.user32.RegisterHotKey(
            None,
            SALVAGE_HOTKEY_ID,
            0,
            VK_DELETE,
        ):
            log_error("hotkey", "RegisterHotKey failed for Delete")

        msg = MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_APP_HOTKEY_COMMAND:
                process_hotkey_worker_commands()
            elif msg.message == WM_HOTKEY:
                if msg.wParam == PICKER_HOTKEY_ID:
                    hotkey_q.put("picker")
                elif msg.wParam == PICKER_OPEN_END_HOTKEY_ID:
                    hotkey_q.put("picker_end_open")
                elif msg.wParam == SALVAGE_HOTKEY_ID:
                    hotkey_q.put("salvage_toggle")
                else:
                    for hotkey_id, _vk, event_name in PICKER_ACTION_HOTKEYS:
                        if msg.wParam == hotkey_id:
                            hotkey_q.put(event_name)
                            break
    except Exception as e:
        log_error("hotkey", f"Hotkey worker failed: {e}")


def right_shift_worker():
    global right_arrow_hold_active, right_arrow_hold_compensated, right_arrow_press_at
    global right_arrow_was_down, right_ctrl_was_down
    global up_arrow_was_down, up_arrow_press_at, up_arrow_hold_triggered
    global down_arrow_was_down, down_arrow_press_at, down_arrow_hold_triggered

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
                    root.after(0, lambda: move_picker_selection_to_edge(-1))
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
                    root.after(0, lambda: move_picker_selection_to_edge(1))
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
                    if stage == "quantity":
                        if right_arrow_last_action_stage == "quantity" and not right_arrow_hold_compensated:
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
        except Exception as e:
            log_error("right_shift", f"Right Shift worker failed: {e}")

        time.sleep(max(0.005, RIGHT_SHIFT_POLL_SECONDS))


def check_hotkeys():
    close_picker_if_target_gone()

    while not hotkey_q.empty():
        event = hotkey_q.get()
        if event == "picker":
            show_picker()
        elif event == "picker_end_open":
            handle_picker_end_hotkey()
        elif event == "salvage_toggle":
            toggle_salvage_loop()
        elif event == "picker_up":
            if should_enable_picker_navigation_hotkeys():
                move_picker_selection(-1)
            else:
                sync_picker_navigation_hotkeys()
        elif event == "picker_down":
            if should_enable_picker_navigation_hotkeys():
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
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass

    try:
        apply_no_focus_clickthrough(root, show_in_task_manager=False)
    except Exception:
        pass


def show_overlay():
    show_tk_window_no_activate(root)


def apply_window_region():
    pass


def create_primary_monitor_alert():
    global primary_monitor_alert, primary_monitor_canvas, primary_monitor_rect

    primary_monitor_rect = get_primary_monitor_rect()
    if primary_monitor_rect is None:
        log_error("monitor", "Primary monitor alert was not created: no monitor rect.")
        return

    left, top, right, bottom = primary_monitor_rect
    width = right - left
    height = bottom - top
    scale = max(1.0, root.winfo_fpixels("1i") / 96)
    thickness = round(PRIMARY_MONITOR_BORDER_THICKNESS * scale)

    primary_monitor_alert = tk.Toplevel(root)
    primary_monitor_alert.withdraw()
    primary_monitor_alert.title("Crossout Timer Primary Monitor Alert")
    primary_monitor_alert.overrideredirect(True)
    primary_monitor_alert.configure(bg=TRANSPARENT_BG)
    primary_monitor_alert.attributes("-transparentcolor", TRANSPARENT_BG)
    primary_monitor_alert.attributes("-topmost", True)
    primary_monitor_alert.attributes("-alpha", PRIMARY_MONITOR_ALPHA)
    primary_monitor_alert.geometry(geometry_from_rect(primary_monitor_rect))

    primary_monitor_canvas = tk.Canvas(
        primary_monitor_alert,
        width=width,
        height=height,
        bg=TRANSPARENT_BG,
        highlightthickness=0,
        bd=0,
    )
    primary_monitor_canvas.pack(fill="both", expand=True)
    primary_monitor_border_items.extend(
        [
            primary_monitor_canvas.create_rectangle(
                0,
                0,
                width,
                thickness,
                fill=ALERT_BG,
                outline="",
            ),
            primary_monitor_canvas.create_rectangle(
                0,
                height - thickness,
                width,
                height,
                fill=ALERT_BG,
                outline="",
            ),
            primary_monitor_canvas.create_rectangle(
                0,
                thickness,
                thickness,
                height - thickness,
                fill=ALERT_BG,
                outline="",
            ),
            primary_monitor_canvas.create_rectangle(
                width - thickness,
                thickness,
                width,
                height - thickness,
                fill=ALERT_BG,
                outline="",
            ),
        ]
    )
    primary_monitor_alert.update_idletasks()

    try:
        apply_no_focus_clickthrough(primary_monitor_alert)
        hwnd = get_window_hwnd(primary_monitor_alert)
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            -1,
            left,
            top,
            width,
            height,
            SWP_NOACTIVATE,
        )
    except Exception as e:
        log_error("primary_monitor_window", f"Primary monitor window setup failed: {e}")


def create_second_monitor_alert():
    global second_monitor_alert, second_monitor_canvas, second_monitor_rect

    second_monitor_rect = get_second_monitor_rect(ALERT_MONITOR_INDEX)
    if second_monitor_rect is None:
        log_error("monitor", "Second monitor alert was not created: no monitor rect.")
        return

    left, top, right, bottom = second_monitor_rect
    width = right - left
    height = bottom - top
    scale = max(1.0, root.winfo_fpixels("1i") / 96)
    thickness = round(SECOND_MONITOR_BORDER_THICKNESS * scale)

    second_monitor_alert = tk.Toplevel(root)
    second_monitor_alert.withdraw()
    second_monitor_alert.title("Crossout Timer Second Monitor Alert")
    second_monitor_alert.overrideredirect(True)
    second_monitor_alert.configure(bg=TRANSPARENT_BG)
    second_monitor_alert.attributes("-transparentcolor", TRANSPARENT_BG)
    second_monitor_alert.attributes("-topmost", True)
    second_monitor_alert.attributes("-alpha", SECOND_MONITOR_ALPHA)
    second_monitor_alert.geometry(geometry_from_rect(second_monitor_rect))

    second_monitor_canvas = tk.Canvas(
        second_monitor_alert,
        width=width,
        height=height,
        bg=TRANSPARENT_BG,
        highlightthickness=0,
        bd=0,
    )
    second_monitor_canvas.pack(fill="both", expand=True)
    second_monitor_border_items.extend(
        [
            second_monitor_canvas.create_rectangle(
                0,
                0,
                width,
                thickness,
                fill=ALERT_BG,
                outline="",
            ),
            second_monitor_canvas.create_rectangle(
                0,
                height - thickness,
                width,
                height,
                fill=ALERT_BG,
                outline="",
            ),
            second_monitor_canvas.create_rectangle(
                0,
                thickness,
                thickness,
                height - thickness,
                fill=ALERT_BG,
                outline="",
            ),
            second_monitor_canvas.create_rectangle(
                width - thickness,
                thickness,
                width,
                height - thickness,
                fill=ALERT_BG,
                outline="",
            ),
        ]
    )
    second_monitor_alert.update_idletasks()

    try:
        apply_no_focus_clickthrough(second_monitor_alert)
        hwnd = get_window_hwnd(second_monitor_alert)
        left, top, right, bottom = second_monitor_rect
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            -1,
            left,
            top,
            right - left,
            bottom - top,
            SWP_NOACTIVATE,
        )
    except Exception as e:
        log_error("second_monitor_window", f"Second monitor window setup failed: {e}")


def center_notch():
    root.geometry(f"{overlay_width}x{notch_height}+0+0")
    root.update_idletasks()
    apply_window_region()


def configure_dpi_sizes():
    global font_pixels, notch_height, notch_radius, notch_width, notch_x, overlay_width

    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(root.winfo_id())
    except Exception:
        try:
            dpi = ctypes.windll.user32.GetDpiForSystem()
        except Exception:
            dpi = root.winfo_fpixels("1i")

    scale = max(1.0, dpi / 96)
    notch_width = round(BASE_NOTCH_WIDTH * scale)
    notch_height = round(BASE_NOTCH_HEIGHT * scale)
    notch_radius = round(BASE_NOTCH_RADIUS * scale)
    font_pixels = round(BASE_FONT_PIXELS * scale)
    overlay_width = root.winfo_screenwidth()
    notch_x = (overlay_width - notch_width) // 2
    canvas.config(width=overlay_width, height=notch_height)


def rounded_bottom_rect_points(x, y, width, height, radius, steps=16):
    radius = min(radius, width // 2, height)
    x1 = x
    y1 = y
    x2 = x + width
    y2 = y + height
    points = [x1, y1, x2, y1, x2, y2 - radius]

    right_cx = x2 - radius
    corner_cy = y2 - radius
    for step in range(steps + 1):
        angle = math.radians(step * 90 / steps)
        points.extend(
            [
                round(right_cx + radius * math.cos(angle)),
                round(corner_cy + radius * math.sin(angle)),
            ]
        )

    left_cx = x1 + radius
    points.extend([left_cx, y2])
    for step in range(steps + 1):
        angle = math.radians(90 + step * 90 / steps)
        points.extend(
            [
                round(left_cx + radius * math.cos(angle)),
                round(corner_cy + radius * math.sin(angle)),
            ]
        )

    points.extend([x1, y1])
    return points


def draw_notch():
    global alert_strip, timer_text

    alert_strip = canvas.create_rectangle(
        0,
        0,
        overlay_width,
        notch_height,
        fill=ALERT_BG,
        outline="",
        state="hidden",
    )
    notch_items.append(
        canvas.create_polygon(
            rounded_bottom_rect_points(
                notch_x,
                0,
                notch_width,
                notch_height,
                notch_radius,
            ),
            fill=NORMAL_BG,
            outline="",
        )
    )
    timer_text = canvas.create_text(
        notch_x + notch_width // 2,
        notch_height // 2,
        text="--:--",
        fill=NORMAL_FG,
        font=("Segoe UI", -font_pixels),
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
    threading.Thread(target=hotkey_worker, daemon=True).start()
    threading.Thread(target=right_shift_worker, daemon=True).start()
    threading.Thread(target=picker_refresh_worker, daemon=True).start()

    keep_on_top()
    update_label()
    check_hotkeys()
    root.mainloop()
