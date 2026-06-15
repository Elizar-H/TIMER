import ctypes
from ctypes import wintypes
import json


def enable_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


enable_dpi_awareness()

try:
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)
except Exception:
    pass

import threading
import queue
import math
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import re
import time
import urllib.request
import tkinter as tk
import tkinter.font as tkfont
from timer_settings import load_settings, setting

FLASH_URL = "https://crossoutcore.ru/flash-crashes/"
RECYCLING_URL = "https://crossoutcore.ru/recycling/"
URL = FLASH_URL
SERVER_TIME_RE = re.compile(r'\\?"serverTime\\?":(\d+)')
TARGET_TIME_RE = re.compile(r'\\?"targetUpdateTimestamp\\?":(\d+)')
NEXT_ACTION_DATE_RE = re.compile(r'"\$D([^"]+)"')
ITEM_PATTERN = re.compile(
    r'\{\\"id\\":(\d+),\\"name\\":\\"(.*?)\\",\\"rarityId\\":'
    r'(null|\d+),\\"factionId\\":(null|\d+),\\"categoryId\\":'
    r'(null|\d+),\\"typeId\\":(null|\d+).*?\\"removed\\":(\d+),'
    r'\\"amount\\":(\d+),\\"craftable\\":(\d+)',
    re.DOTALL,
)
MARKET_PATTERN = re.compile(
    r'\\"(\d+)\\":\{\\"s\\":([0-9.]+),\\"b\\":([0-9.]+),'
    r'\\"so\\":(\d+),\\"bo\\":(\d+),[^}]*?\\"t\\":(\d+)\}'
)
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Encoding": "identity",
}

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
LOG_PATH = Path(__file__).with_name("timer.log")
LOG_MAX_BYTES = 512 * 1024
SETTINGS_PATH = Path(__file__).with_name("settings.json")
PICKER_CACHE_PATH = Path(__file__).with_name("timer_items_cache.json")
PICKER_CACHE_VERSION = 14
PICKER_REFRESH_SECONDS = 30
PICKER_BACKGROUND_REFRESH_SECONDS = 10
PICKER_FAST_REFRESH_ATTEMPTS = 5
PICKER_FAST_REFRESH_DELAY_SECONDS = 0.35
PICKER_CACHE_MAX_AGE_SECONDS = 45
FILTERS_CACHE_SECONDS = 1.5
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
PICKER_DECOR_CATEGORIES = {6}
# Координаты под 4K/масштаб: окно списка справа впритык к поиску, верх на одной высоте.
PICKER_GAME_SEARCH_X_RATIO = 0.292
PICKER_GAME_SEARCH_Y_RATIO = 0.147
PICKER_GAME_SEARCH_GAP_PIXELS = 0
PICKER_GAME_SEARCH_Y_OFFSET_PIXELS = 16
# Клик внутрь поля поиска.
PICKER_GAME_SEARCH_CLICK_X_RATIO = 0.245
PICKER_GAME_SEARCH_CLICK_Y_RATIO = 0.170
GAME_OPEN_CARD_X_RATIO = 0.540
GAME_OPEN_CARD_Y_RATIO = 0.281
GAME_BUY_BUTTON_X_RATIO = 0.069
GAME_BUY_BUTTON_Y_RATIO = 0.904
GAME_ORDER_BUTTON_X_RATIO = 0.515
GAME_ORDER_BUTTON_Y_RATIO = 0.653
GAME_QUANTITY_PLUS_X_RATIO = 0.523
GAME_QUANTITY_PLUS_Y_RATIO = 0.512
GAME_QUANTITY_MINUS_X_RATIO = 0.469
GAME_QUANTITY_MINUS_Y_RATIO = 0.512
GAME_SELL_BUTTON_X_RATIO = 0.366927
GAME_SELL_BUTTON_Y_RATIO = 0.906944
GAME_SELL_PRICE_CLICK_X_RATIO = 0.494792
GAME_SELL_PRICE_CLICK_Y_RATIO = 0.376389
GAME_SELL_ALL_BUTTON_X_RATIO = 0.577604
GAME_SELL_ALL_BUTTON_Y_RATIO = 0.550926
GAME_SELL_CONFIRM_BUTTON_X_RATIO = 0.517448
GAME_SELL_CONFIRM_BUTTON_Y_RATIO = 0.694444
GAME_SELL_CONFIRM_HOLD_SECONDS = 1.0
GAME_SELL_STEP_DELAY_SECONDS = 0.050
GAME_ORDER_TO_SELL_DELAY_SECONDS = 0.12
GAME_OPEN_TO_BUY_DELAY_SECONDS = 0.20
GAME_BUY_TO_QUANTITY_DELAY_SECONDS = 0.12
GAME_MARKET_TAB_X_RATIO = 0.383
GAME_MARKET_TAB_Y_RATIO = 0.033
GAME_DETAILS_TAB_X_RATIO = 0.421
GAME_DETAILS_TAB_Y_RATIO = 0.088
GAME_SECTION_CLICK_DELAY_SECONDS = 0.045
SALVAGE_STORAGE_TAB_X_RATIO = 0.430729
SALVAGE_STORAGE_TAB_Y_RATIO = 0.036574
SALVAGE_DETAILS_TAB_X_RATIO = 0.327083
SALVAGE_DETAILS_TAB_Y_RATIO = 0.083796
SALVAGE_PRE_DECOR_CATEGORY_X_RATIO = 0.423958
SALVAGE_PRE_DECOR_CATEGORY_Y_RATIO = 0.168519
SALVAGE_DECOR_CATEGORY_X_RATIO = 0.341406
SALVAGE_DECOR_CATEGORY_Y_RATIO = 0.168519
SALVAGE_SORT_DROPDOWN_X_RATIO = 0.890365
SALVAGE_SORT_DROPDOWN_Y_RATIO = 0.169907
SALVAGE_SORT_NEW_OPTION_X_RATIO = 0.876563
SALVAGE_SORT_NEW_OPTION_Y_RATIO = 0.435185
SALVAGE_SORT_TYPE_OPTION_X_RATIO = 0.877865
SALVAGE_SORT_TYPE_OPTION_Y_RATIO = 0.215278
SALVAGE_FIRST_ITEM_X_RATIO = 0.066927
SALVAGE_FIRST_ITEM_Y_RATIO = 0.319907
SALVAGE_SELECT_ITEM_X_RATIO = 0.066927
SALVAGE_SELECT_ITEM_Y_RATIO = 0.319907
SALVAGE_ITEM_ROW_STEP_RATIO = 0.233
SALVAGE_CONTEXT_DISASSEMBLE_X_RATIO = 0.059896
SALVAGE_CONTEXT_DISASSEMBLE_Y_RATIO = 0.606481
SALVAGE_ALL_BUTTON_X_RATIO = 0.503646
SALVAGE_ALL_BUTTON_Y_RATIO = 0.471759
SALVAGE_CONFIRM_BUTTON_X_RATIO = 0.500260
SALVAGE_CONFIRM_BUTTON_Y_RATIO = 0.680093
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
MARKET_MINUTES_ACTION = "00a3c6f09401f51e0f2f5197309fad70a0f23590be"
FLASH_ANALYSIS_MINUTES = 60
FLASH_MIN_PROFIT = 1
FLASH_MIN_REQUESTS = 0
FLASH_MIN_BUYER_RATIO = 0
FILTER_STORAGE_KEYS = {
    "flash_min_profit": ("anomalyMinProfit", "Profit"),
    "flash_min_requests": ("anomalyMinBo", "MinBo"),
    "flash_time_window": ("anomalyTimeWindow", "TimeWindow"),
    "flash_min_buyer_ratio": ("anomalyMinBuyerRatio",),
    "recycling_rarities": ("Recycling-rarities", "rarities"),
    "recycling_buy_mode": ("Recycling-buy-mode", "buy-mode"),
    "recycling_sell_mode": ("Recycling-sell-mode", "sell-mode"),
    "recycling_show_only_sale_lots": (
        "Recycling-show-only-with-sale-lots",
        "show-only-with-sale-lots",
        "how-only-with-sale-lots",
    ),
}
FILTER_NUMERIC_SPECS = {
    "flash_min_profit": {"min": 0, "max": None, "prefer": "longest"},
    "flash_min_requests": {"min": 0, "max": None, "prefer": "first"},
    "flash_time_window": {"min": 15, "max": 240, "prefer": "longest"},
    "flash_min_buyer_ratio": {"min": 0, "max": 100, "prefer": "longest"},
}
# Декор: считаем прибыль строго/консервативно.
# Покупка декора по продаже (s), продажа ресурсов сразу в запросы на покупку (b).
RECYCLING_FORCE_INSTANT_PROFIT_PRICES = False
RECYCLING_MIN_PROFIT = 0.01
RESOURCE_RECIPES = {
    2: (("scrap", 1),),
    3: (("scrap", 150), ("copper", 50)),
    4: (("scrap", 40), ("copper", 100), ("wires", 60), ("plastic", 30)),
    5: (("scrap", 80), ("copper", 150), ("wires", 170), ("plastic", 80)),
    6: (("scrap", 50), ("copper", 250), ("electronics", 250), ("batteries", 250)),
    7: (("copper", 500), ("electronics", 500), ("batteries", 350)),
}
RESOURCES = {
    "scrap": {"id": 1434, "lot_size": 100},
    "copper": {"id": 1432, "lot_size": 100},
    "wires": {"id": 1438, "lot_size": 100},
    "plastic": {"id": 1430, "lot_size": 100},
    "electronics": {"id": 1436, "lot_size": 10},
    "batteries": {"id": 1424, "lot_size": 10},
}
RARITY_STYLES = {
    2: {"name": "Обычный", "short": "Обычн.", "color": "#d7d7d7"},
    3: {"name": "Редкий", "short": "Редк.", "color": "#2f8cff"},
    4: {"name": "Особый", "short": "Особ.", "color": "#00d6ef"},
    5: {"name": "Эпический", "short": "Эпич.", "color": "#bd3cff"},
    6: {"name": "Легендарный", "short": "Легенд.", "color": "#ffb000"},
    7: {"name": "Реликтовый", "short": "Реликт.", "color": "#ff5a00"},
}

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

DEFAULT_SETTINGS = {
    "test_mode": TEST_MODE,
    "test_alert_seconds": TEST_ALERT_SECONDS,
    "alert": {
        "start_seconds": ALERT_START_SECONDS,
        "end_seconds": ALERT_END_SECONDS,
        "update_ms": ALERT_UPDATE_MS,
        "monitor_index": ALERT_MONITOR_INDEX,
        "pulse_pattern": ALERT_PULSE_PATTERN,
        "color": ALERT_BG,
        "min_alpha": ALERT_MIN_ALPHA,
        "max_alpha": ALERT_ALPHA,
        "primary_min_alpha": PRIMARY_MONITOR_MIN_ALPHA,
        "primary_max_alpha": PRIMARY_MONITOR_ALPHA,
        "primary_border_thickness": PRIMARY_MONITOR_BORDER_THICKNESS,
        "second_min_alpha": SECOND_MONITOR_MIN_ALPHA,
        "second_max_alpha": SECOND_MONITOR_ALPHA,
        "second_border_thickness": SECOND_MONITOR_BORDER_THICKNESS,
    },
    "notch": {
        "width": BASE_NOTCH_WIDTH,
        "height": BASE_NOTCH_HEIGHT,
        "radius": BASE_NOTCH_RADIUS,
        "font_pixels": BASE_FONT_PIXELS,
        "normal_alpha": NORMAL_ALPHA,
        "normal_bg": NORMAL_BG,
        "normal_fg": NORMAL_FG,
    },
    "picker": {
        "width": PICKER_WIDTH,
        "max_height": PICKER_MAX_HEIGHT,
        "row_height": PICKER_ROW_HEIGHT,
        "refresh_seconds": PICKER_REFRESH_SECONDS,
        "background_refresh_seconds": PICKER_BACKGROUND_REFRESH_SECONDS,
        "fast_refresh_attempts": PICKER_FAST_REFRESH_ATTEMPTS,
        "fast_refresh_delay_seconds": PICKER_FAST_REFRESH_DELAY_SECONDS,
        "empty_retry_attempts": PICKER_EMPTY_RETRY_ATTEMPTS,
        "empty_retry_delay_seconds": PICKER_EMPTY_RETRY_DELAY_SECONDS,
        "show_status": PICKER_SHOW_STATUS,
        "status_alpha_color": PICKER_STATUS_FG,
        "profile_refresh": PICKER_PROFILE_REFRESH,
    },
    "game_search": {
        "window_x_ratio": PICKER_GAME_SEARCH_X_RATIO,
        "window_y_ratio": PICKER_GAME_SEARCH_Y_RATIO,
        "window_y_offset_pixels": PICKER_GAME_SEARCH_Y_OFFSET_PIXELS,
        "click_x_ratio": PICKER_GAME_SEARCH_CLICK_X_RATIO,
        "click_y_ratio": PICKER_GAME_SEARCH_CLICK_Y_RATIO,
    },
    "game_actions": {
        "open_card_x_ratio": GAME_OPEN_CARD_X_RATIO,
        "open_card_y_ratio": GAME_OPEN_CARD_Y_RATIO,
        "buy_button_x_ratio": GAME_BUY_BUTTON_X_RATIO,
        "buy_button_y_ratio": GAME_BUY_BUTTON_Y_RATIO,
        "order_button_x_ratio": GAME_ORDER_BUTTON_X_RATIO,
        "order_button_y_ratio": GAME_ORDER_BUTTON_Y_RATIO,
        "quantity_plus_x_ratio": GAME_QUANTITY_PLUS_X_RATIO,
        "quantity_plus_y_ratio": GAME_QUANTITY_PLUS_Y_RATIO,
        "quantity_minus_x_ratio": GAME_QUANTITY_MINUS_X_RATIO,
        "quantity_minus_y_ratio": GAME_QUANTITY_MINUS_Y_RATIO,
        "sell_button_x_ratio": GAME_SELL_BUTTON_X_RATIO,
        "sell_button_y_ratio": GAME_SELL_BUTTON_Y_RATIO,
        "sell_price_click_x_ratio": GAME_SELL_PRICE_CLICK_X_RATIO,
        "sell_price_click_y_ratio": GAME_SELL_PRICE_CLICK_Y_RATIO,
        "sell_all_button_x_ratio": GAME_SELL_ALL_BUTTON_X_RATIO,
        "sell_all_button_y_ratio": GAME_SELL_ALL_BUTTON_Y_RATIO,
        "sell_confirm_button_x_ratio": GAME_SELL_CONFIRM_BUTTON_X_RATIO,
        "sell_confirm_button_y_ratio": GAME_SELL_CONFIRM_BUTTON_Y_RATIO,
        "sell_confirm_hold_seconds": GAME_SELL_CONFIRM_HOLD_SECONDS,
        "sell_step_delay_seconds": GAME_SELL_STEP_DELAY_SECONDS,
        "order_to_sell_delay_seconds": GAME_ORDER_TO_SELL_DELAY_SECONDS,
        "open_to_buy_delay_seconds": GAME_OPEN_TO_BUY_DELAY_SECONDS,
        "buy_to_quantity_delay_seconds": GAME_BUY_TO_QUANTITY_DELAY_SECONDS,
        "market_tab_x_ratio": GAME_MARKET_TAB_X_RATIO,
        "market_tab_y_ratio": GAME_MARKET_TAB_Y_RATIO,
        "details_tab_x_ratio": GAME_DETAILS_TAB_X_RATIO,
        "details_tab_y_ratio": GAME_DETAILS_TAB_Y_RATIO,
        "section_click_delay_seconds": GAME_SECTION_CLICK_DELAY_SECONDS,
        "salvage_storage_tab_x_ratio": SALVAGE_STORAGE_TAB_X_RATIO,
        "salvage_storage_tab_y_ratio": SALVAGE_STORAGE_TAB_Y_RATIO,
        "salvage_details_tab_x_ratio": SALVAGE_DETAILS_TAB_X_RATIO,
        "salvage_details_tab_y_ratio": SALVAGE_DETAILS_TAB_Y_RATIO,
        "salvage_pre_decor_category_x_ratio": SALVAGE_PRE_DECOR_CATEGORY_X_RATIO,
        "salvage_pre_decor_category_y_ratio": SALVAGE_PRE_DECOR_CATEGORY_Y_RATIO,
        "salvage_decor_category_x_ratio": SALVAGE_DECOR_CATEGORY_X_RATIO,
        "salvage_decor_category_y_ratio": SALVAGE_DECOR_CATEGORY_Y_RATIO,
        "salvage_sort_dropdown_x_ratio": SALVAGE_SORT_DROPDOWN_X_RATIO,
        "salvage_sort_dropdown_y_ratio": SALVAGE_SORT_DROPDOWN_Y_RATIO,
        "salvage_sort_new_option_x_ratio": SALVAGE_SORT_NEW_OPTION_X_RATIO,
        "salvage_sort_new_option_y_ratio": SALVAGE_SORT_NEW_OPTION_Y_RATIO,
        "salvage_sort_type_option_x_ratio": SALVAGE_SORT_TYPE_OPTION_X_RATIO,
        "salvage_sort_type_option_y_ratio": SALVAGE_SORT_TYPE_OPTION_Y_RATIO,
        "salvage_first_item_x_ratio": SALVAGE_FIRST_ITEM_X_RATIO,
        "salvage_first_item_y_ratio": SALVAGE_FIRST_ITEM_Y_RATIO,
        "salvage_select_item_x_ratio": SALVAGE_SELECT_ITEM_X_RATIO,
        "salvage_select_item_y_ratio": SALVAGE_SELECT_ITEM_Y_RATIO,
        "salvage_item_row_step_ratio": SALVAGE_ITEM_ROW_STEP_RATIO,
        "salvage_context_disassemble_x_ratio": SALVAGE_CONTEXT_DISASSEMBLE_X_RATIO,
        "salvage_context_disassemble_y_ratio": SALVAGE_CONTEXT_DISASSEMBLE_Y_RATIO,
        "salvage_all_button_x_ratio": SALVAGE_ALL_BUTTON_X_RATIO,
        "salvage_all_button_y_ratio": SALVAGE_ALL_BUTTON_Y_RATIO,
        "salvage_confirm_button_x_ratio": SALVAGE_CONFIRM_BUTTON_X_RATIO,
        "salvage_confirm_button_y_ratio": SALVAGE_CONFIRM_BUTTON_Y_RATIO,
        "salvage_confirm_hold_seconds": SALVAGE_CONFIRM_HOLD_SECONDS,
        "salvage_confirm_wait_seconds": SALVAGE_CONFIRM_WAIT_SECONDS,
        "salvage_after_confirm_seconds": SALVAGE_AFTER_CONFIRM_SECONDS,
        "salvage_step_delay_seconds": SALVAGE_STEP_DELAY_SECONDS,
        "salvage_item_hover_delay_seconds": SALVAGE_ITEM_HOVER_DELAY_SECONDS,
        "salvage_item_right_click_min_interval_seconds": SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS,
        "salvage_post_right_click_delay_seconds": SALVAGE_POST_RIGHT_CLICK_DELAY_SECONDS,
        "salvage_post_menu_click_delay_seconds": SALVAGE_POST_MENU_CLICK_DELAY_SECONDS,
        "salvage_post_all_click_delay_seconds": SALVAGE_POST_ALL_CLICK_DELAY_SECONDS,
        "salvage_mouse_cancel_threshold_pixels": SALVAGE_MOUSE_CANCEL_THRESHOLD_PIXELS,
        "picker_open_hold_seconds": PICKER_OPEN_HOLD_SECONDS,
        "picker_end_release_grace_seconds": PICKER_END_RELEASE_GRACE_SECONDS,
        "right_arrow_hold_seconds": RIGHT_ARROW_HOLD_SECONDS,
        "market_action_stage_max_age_seconds": MARKET_ACTION_STAGE_MAX_AGE_SECONDS,
        "right_shift_poll_seconds": RIGHT_SHIFT_POLL_SECONDS,
    },
    "paste": {
        "before_click_delay": PASTE_BEFORE_CLICK_DELAY,
        "hover_before_click_delay": PASTE_HOVER_BEFORE_CLICK_DELAY,
        "after_click_delay": PASTE_AFTER_CLICK_DELAY,
        "after_clear_delay": PASTE_AFTER_CLEAR_DELAY,
        "between_keys_delay": PASTE_BETWEEN_KEYS_DELAY,
        "before_enter_delay": PASTE_BEFORE_ENTER_DELAY,
        "enter_key_delay": PASTE_ENTER_KEY_DELAY,
        "search_clicks": PASTE_SEARCH_CLICKS,
        "mouse_click_delay": MOUSE_CLICK_DELAY,
    },
}


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
    global PICKER_GAME_SEARCH_X_RATIO, PICKER_GAME_SEARCH_Y_RATIO
    global PICKER_GAME_SEARCH_Y_OFFSET_PIXELS
    global PICKER_GAME_SEARCH_CLICK_X_RATIO, PICKER_GAME_SEARCH_CLICK_Y_RATIO
    global GAME_OPEN_CARD_X_RATIO, GAME_OPEN_CARD_Y_RATIO
    global GAME_BUY_BUTTON_X_RATIO, GAME_BUY_BUTTON_Y_RATIO
    global GAME_ORDER_BUTTON_X_RATIO, GAME_ORDER_BUTTON_Y_RATIO
    global GAME_QUANTITY_PLUS_X_RATIO, GAME_QUANTITY_PLUS_Y_RATIO
    global GAME_QUANTITY_MINUS_X_RATIO, GAME_QUANTITY_MINUS_Y_RATIO
    global GAME_SELL_BUTTON_X_RATIO, GAME_SELL_BUTTON_Y_RATIO
    global GAME_SELL_PRICE_CLICK_X_RATIO, GAME_SELL_PRICE_CLICK_Y_RATIO
    global GAME_SELL_ALL_BUTTON_X_RATIO, GAME_SELL_ALL_BUTTON_Y_RATIO
    global GAME_SELL_CONFIRM_BUTTON_X_RATIO, GAME_SELL_CONFIRM_BUTTON_Y_RATIO
    global GAME_SELL_CONFIRM_HOLD_SECONDS, GAME_SELL_STEP_DELAY_SECONDS
    global GAME_ORDER_TO_SELL_DELAY_SECONDS
    global GAME_OPEN_TO_BUY_DELAY_SECONDS, GAME_BUY_TO_QUANTITY_DELAY_SECONDS
    global GAME_MARKET_TAB_X_RATIO, GAME_MARKET_TAB_Y_RATIO
    global GAME_DETAILS_TAB_X_RATIO, GAME_DETAILS_TAB_Y_RATIO
    global GAME_SECTION_CLICK_DELAY_SECONDS, PICKER_OPEN_HOLD_SECONDS
    global SALVAGE_STORAGE_TAB_X_RATIO, SALVAGE_STORAGE_TAB_Y_RATIO
    global SALVAGE_DETAILS_TAB_X_RATIO, SALVAGE_DETAILS_TAB_Y_RATIO
    global SALVAGE_PRE_DECOR_CATEGORY_X_RATIO, SALVAGE_PRE_DECOR_CATEGORY_Y_RATIO
    global SALVAGE_DECOR_CATEGORY_X_RATIO, SALVAGE_DECOR_CATEGORY_Y_RATIO
    global SALVAGE_SORT_DROPDOWN_X_RATIO, SALVAGE_SORT_DROPDOWN_Y_RATIO
    global SALVAGE_SORT_NEW_OPTION_X_RATIO, SALVAGE_SORT_NEW_OPTION_Y_RATIO
    global SALVAGE_SORT_TYPE_OPTION_X_RATIO, SALVAGE_SORT_TYPE_OPTION_Y_RATIO
    global SALVAGE_FIRST_ITEM_X_RATIO, SALVAGE_FIRST_ITEM_Y_RATIO
    global SALVAGE_SELECT_ITEM_X_RATIO, SALVAGE_SELECT_ITEM_Y_RATIO
    global SALVAGE_ITEM_ROW_STEP_RATIO
    global SALVAGE_CONTEXT_DISASSEMBLE_X_RATIO, SALVAGE_CONTEXT_DISASSEMBLE_Y_RATIO
    global SALVAGE_ALL_BUTTON_X_RATIO, SALVAGE_ALL_BUTTON_Y_RATIO
    global SALVAGE_CONFIRM_BUTTON_X_RATIO, SALVAGE_CONFIRM_BUTTON_Y_RATIO
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

    PICKER_GAME_SEARCH_X_RATIO = float(
        setting(settings, "game_search.window_x_ratio", PICKER_GAME_SEARCH_X_RATIO)
    )
    PICKER_GAME_SEARCH_Y_RATIO = float(
        setting(settings, "game_search.window_y_ratio", PICKER_GAME_SEARCH_Y_RATIO)
    )
    PICKER_GAME_SEARCH_Y_OFFSET_PIXELS = int(
        setting(settings, "game_search.window_y_offset_pixels", PICKER_GAME_SEARCH_Y_OFFSET_PIXELS)
    )
    PICKER_GAME_SEARCH_CLICK_X_RATIO = float(
        setting(settings, "game_search.click_x_ratio", PICKER_GAME_SEARCH_CLICK_X_RATIO)
    )
    PICKER_GAME_SEARCH_CLICK_Y_RATIO = float(
        setting(settings, "game_search.click_y_ratio", PICKER_GAME_SEARCH_CLICK_Y_RATIO)
    )

    GAME_OPEN_CARD_X_RATIO = float(
        setting(settings, "game_actions.open_card_x_ratio", GAME_OPEN_CARD_X_RATIO)
    )
    GAME_OPEN_CARD_Y_RATIO = float(
        setting(settings, "game_actions.open_card_y_ratio", GAME_OPEN_CARD_Y_RATIO)
    )
    GAME_BUY_BUTTON_X_RATIO = float(
        setting(settings, "game_actions.buy_button_x_ratio", GAME_BUY_BUTTON_X_RATIO)
    )
    GAME_BUY_BUTTON_Y_RATIO = float(
        setting(settings, "game_actions.buy_button_y_ratio", GAME_BUY_BUTTON_Y_RATIO)
    )
    GAME_ORDER_BUTTON_X_RATIO = float(
        setting(settings, "game_actions.order_button_x_ratio", GAME_ORDER_BUTTON_X_RATIO)
    )
    GAME_ORDER_BUTTON_Y_RATIO = float(
        setting(settings, "game_actions.order_button_y_ratio", GAME_ORDER_BUTTON_Y_RATIO)
    )
    GAME_QUANTITY_PLUS_X_RATIO = float(
        setting(settings, "game_actions.quantity_plus_x_ratio", GAME_QUANTITY_PLUS_X_RATIO)
    )
    GAME_QUANTITY_PLUS_Y_RATIO = float(
        setting(settings, "game_actions.quantity_plus_y_ratio", GAME_QUANTITY_PLUS_Y_RATIO)
    )
    GAME_QUANTITY_MINUS_X_RATIO = float(
        setting(settings, "game_actions.quantity_minus_x_ratio", GAME_QUANTITY_MINUS_X_RATIO)
    )
    GAME_QUANTITY_MINUS_Y_RATIO = float(
        setting(settings, "game_actions.quantity_minus_y_ratio", GAME_QUANTITY_MINUS_Y_RATIO)
    )
    GAME_SELL_BUTTON_X_RATIO = float(
        setting(settings, "game_actions.sell_button_x_ratio", GAME_SELL_BUTTON_X_RATIO)
    )
    GAME_SELL_BUTTON_Y_RATIO = float(
        setting(settings, "game_actions.sell_button_y_ratio", GAME_SELL_BUTTON_Y_RATIO)
    )
    GAME_SELL_PRICE_CLICK_X_RATIO = float(
        setting(settings, "game_actions.sell_price_click_x_ratio", GAME_SELL_PRICE_CLICK_X_RATIO)
    )
    GAME_SELL_PRICE_CLICK_Y_RATIO = float(
        setting(settings, "game_actions.sell_price_click_y_ratio", GAME_SELL_PRICE_CLICK_Y_RATIO)
    )
    GAME_SELL_ALL_BUTTON_X_RATIO = float(
        setting(settings, "game_actions.sell_all_button_x_ratio", GAME_SELL_ALL_BUTTON_X_RATIO)
    )
    GAME_SELL_ALL_BUTTON_Y_RATIO = float(
        setting(settings, "game_actions.sell_all_button_y_ratio", GAME_SELL_ALL_BUTTON_Y_RATIO)
    )
    GAME_SELL_CONFIRM_BUTTON_X_RATIO = float(
        setting(settings, "game_actions.sell_confirm_button_x_ratio", GAME_SELL_CONFIRM_BUTTON_X_RATIO)
    )
    GAME_SELL_CONFIRM_BUTTON_Y_RATIO = float(
        setting(settings, "game_actions.sell_confirm_button_y_ratio", GAME_SELL_CONFIRM_BUTTON_Y_RATIO)
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
    GAME_MARKET_TAB_X_RATIO = float(
        setting(settings, "game_actions.market_tab_x_ratio", GAME_MARKET_TAB_X_RATIO)
    )
    GAME_MARKET_TAB_Y_RATIO = float(
        setting(settings, "game_actions.market_tab_y_ratio", GAME_MARKET_TAB_Y_RATIO)
    )
    GAME_DETAILS_TAB_X_RATIO = float(
        setting(settings, "game_actions.details_tab_x_ratio", GAME_DETAILS_TAB_X_RATIO)
    )
    GAME_DETAILS_TAB_Y_RATIO = float(
        setting(settings, "game_actions.details_tab_y_ratio", GAME_DETAILS_TAB_Y_RATIO)
    )
    GAME_SECTION_CLICK_DELAY_SECONDS = float(
        setting(settings, "game_actions.section_click_delay_seconds", GAME_SECTION_CLICK_DELAY_SECONDS)
    )
    SALVAGE_STORAGE_TAB_X_RATIO = float(
        setting(settings, "game_actions.salvage_storage_tab_x_ratio", SALVAGE_STORAGE_TAB_X_RATIO)
    )
    SALVAGE_STORAGE_TAB_Y_RATIO = float(
        setting(settings, "game_actions.salvage_storage_tab_y_ratio", SALVAGE_STORAGE_TAB_Y_RATIO)
    )
    SALVAGE_DETAILS_TAB_X_RATIO = float(
        setting(settings, "game_actions.salvage_details_tab_x_ratio", SALVAGE_DETAILS_TAB_X_RATIO)
    )
    SALVAGE_DETAILS_TAB_Y_RATIO = float(
        setting(settings, "game_actions.salvage_details_tab_y_ratio", SALVAGE_DETAILS_TAB_Y_RATIO)
    )
    SALVAGE_PRE_DECOR_CATEGORY_X_RATIO = float(
        setting(
            settings,
            "game_actions.salvage_pre_decor_category_x_ratio",
            SALVAGE_PRE_DECOR_CATEGORY_X_RATIO,
        )
    )
    SALVAGE_PRE_DECOR_CATEGORY_Y_RATIO = float(
        setting(
            settings,
            "game_actions.salvage_pre_decor_category_y_ratio",
            SALVAGE_PRE_DECOR_CATEGORY_Y_RATIO,
        )
    )
    SALVAGE_DECOR_CATEGORY_X_RATIO = float(
        setting(settings, "game_actions.salvage_decor_category_x_ratio", SALVAGE_DECOR_CATEGORY_X_RATIO)
    )
    SALVAGE_DECOR_CATEGORY_Y_RATIO = float(
        setting(settings, "game_actions.salvage_decor_category_y_ratio", SALVAGE_DECOR_CATEGORY_Y_RATIO)
    )
    SALVAGE_SORT_DROPDOWN_X_RATIO = float(
        setting(settings, "game_actions.salvage_sort_dropdown_x_ratio", SALVAGE_SORT_DROPDOWN_X_RATIO)
    )
    SALVAGE_SORT_DROPDOWN_Y_RATIO = float(
        setting(settings, "game_actions.salvage_sort_dropdown_y_ratio", SALVAGE_SORT_DROPDOWN_Y_RATIO)
    )
    SALVAGE_SORT_NEW_OPTION_X_RATIO = float(
        setting(settings, "game_actions.salvage_sort_new_option_x_ratio", SALVAGE_SORT_NEW_OPTION_X_RATIO)
    )
    SALVAGE_SORT_NEW_OPTION_Y_RATIO = float(
        setting(settings, "game_actions.salvage_sort_new_option_y_ratio", SALVAGE_SORT_NEW_OPTION_Y_RATIO)
    )
    SALVAGE_SORT_TYPE_OPTION_X_RATIO = float(
        setting(
            settings,
            "game_actions.salvage_sort_type_option_x_ratio",
            SALVAGE_SORT_TYPE_OPTION_X_RATIO,
        )
    )
    SALVAGE_SORT_TYPE_OPTION_Y_RATIO = float(
        setting(
            settings,
            "game_actions.salvage_sort_type_option_y_ratio",
            SALVAGE_SORT_TYPE_OPTION_Y_RATIO,
        )
    )
    SALVAGE_FIRST_ITEM_X_RATIO = float(
        setting(settings, "game_actions.salvage_first_item_x_ratio", SALVAGE_FIRST_ITEM_X_RATIO)
    )
    SALVAGE_FIRST_ITEM_Y_RATIO = float(
        setting(settings, "game_actions.salvage_first_item_y_ratio", SALVAGE_FIRST_ITEM_Y_RATIO)
    )
    SALVAGE_SELECT_ITEM_X_RATIO = float(
        setting(settings, "game_actions.salvage_select_item_x_ratio", SALVAGE_SELECT_ITEM_X_RATIO)
    )
    SALVAGE_SELECT_ITEM_Y_RATIO = float(
        setting(settings, "game_actions.salvage_select_item_y_ratio", SALVAGE_SELECT_ITEM_Y_RATIO)
    )
    SALVAGE_ITEM_ROW_STEP_RATIO = float(
        setting(settings, "game_actions.salvage_item_row_step_ratio", SALVAGE_ITEM_ROW_STEP_RATIO)
    )
    SALVAGE_CONTEXT_DISASSEMBLE_X_RATIO = float(
        setting(settings, "game_actions.salvage_context_disassemble_x_ratio", SALVAGE_CONTEXT_DISASSEMBLE_X_RATIO)
    )
    SALVAGE_CONTEXT_DISASSEMBLE_Y_RATIO = float(
        setting(settings, "game_actions.salvage_context_disassemble_y_ratio", SALVAGE_CONTEXT_DISASSEMBLE_Y_RATIO)
    )
    SALVAGE_ALL_BUTTON_X_RATIO = float(
        setting(settings, "game_actions.salvage_all_button_x_ratio", SALVAGE_ALL_BUTTON_X_RATIO)
    )
    SALVAGE_ALL_BUTTON_Y_RATIO = float(
        setting(settings, "game_actions.salvage_all_button_y_ratio", SALVAGE_ALL_BUTTON_Y_RATIO)
    )
    SALVAGE_CONFIRM_BUTTON_X_RATIO = float(
        setting(settings, "game_actions.salvage_confirm_button_x_ratio", SALVAGE_CONFIRM_BUTTON_X_RATIO)
    )
    SALVAGE_CONFIRM_BUTTON_Y_RATIO = float(
        setting(settings, "game_actions.salvage_confirm_button_y_ratio", SALVAGE_CONFIRM_BUTTON_Y_RATIO)
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

# Windows constants
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000
WS_EX_APPWINDOW = 0x00040000
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_FRAMECHANGED = 0x0020
SW_SHOWNOACTIVATE = 4
SW_SHOW = 5
SW_RESTORE = 9
MONITORINFOF_PRIMARY = 1
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MAPVK_VK_TO_VSC = 0
VK_CONTROL = 0x11
VK_A = 0x41
VK_V = 0x56
VK_BACK = 0x08
VK_RETURN = 0x0D
VK_ESCAPE = 0x1B
VK_NEXT = 0x22
VK_END = 0x23
VK_DELETE = 0x2E
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_RCONTROL = 0xA3
VK_RSHIFT = 0xA1
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


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUTUNION)]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]

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
last_log_times = {}
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
filters_cache_lock = threading.Lock()
filters_cache = None
filters_cache_at = 0
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


def rotate_log_if_needed():
    try:
        if not LOG_PATH.exists() or LOG_PATH.stat().st_size <= LOG_MAX_BYTES:
            return

        LOG_PATH.unlink()
    except Exception:
        pass


def append_log_line(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        rotate_log_if_needed()
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def log_error(key, message):
    now = time.monotonic()
    if now - last_log_times.get(key, 0) < 30:
        return

    last_log_times[key] = now
    append_log_line(message)


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


def parse_local_storage_value(data, keys):
    best_value = None

    for key in keys:
        start = 0
        key_bytes = key.encode("utf-8")
        while True:
            index = data.find(key_bytes, start)
            if index == -1:
                break

            tail = data[index + len(key_bytes) : index + len(key_bytes) + 140]
            text = "".join(chr(byte) if 32 <= byte <= 126 else " " for byte in tail)
            match = re.search(
                r"(\[[0-9,\s]*\]|true|false|-?\d+(?:\.\d+)?|(?<![A-Za-z])[sb](?![A-Za-z]))",
                text,
            )
            if match:
                best_value = match.group(1)

            start = index + 1

    return best_value


def get_storage_text_tail(data, index, key_length, size=48):
    tail = data[index + key_length : index + key_length + size]
    return "".join(chr(byte) if 32 <= byte <= 126 else " " for byte in tail)


def number_in_range(value, min_value=None, max_value=None):
    if min_value is not None and value < min_value:
        return False
    if max_value is not None and value > max_value:
        return False
    return True


def parse_number_from_storage_text(text, min_value=None, max_value=None, prefer="first"):
    candidates = []
    for match in re.finditer(r"-?\d+(?:\.\d+)?", text):
        token = match.group(0)
        prefixes = [token]
        if max_value is not None and "." not in token:
            trimmed = token
            while len(trimmed) > 1:
                trimmed = trimmed[:-1]
                prefixes.append(trimmed)

        for prefix in prefixes:
            try:
                value = float(prefix)
            except Exception:
                continue
            if value.is_integer():
                value = int(value)
            if number_in_range(value, min_value, max_value):
                candidates.append((match.start(), len(prefix), value))
                break

    if not candidates:
        return None

    if prefer == "longest":
        _, _, value = max(candidates, key=lambda item: (item[1], -item[0]))
    else:
        _, _, value = min(candidates, key=lambda item: item[0])
    return value


def get_storage_text_range(data, start, end):
    start = max(0, min(len(data), start))
    end = max(start, min(len(data), end))
    chunk = data[start:end]
    return "".join(chr(byte) if 32 <= byte <= 126 else " " for byte in chunk)


def parse_flash_filter_cluster(data):
    result = {}
    start = 0
    anchor = b"anomalyMinBo"

    while True:
        anchor_index = data.find(anchor, start)
        if anchor_index == -1:
            break

        cluster_end = min(len(data), anchor_index + 180)
        profit_index = data.find(b"Profit", anchor_index, cluster_end)
        window_index = data.find(b"TimeWindow", anchor_index, cluster_end)

        if profit_index != -1 and window_index != -1:
            min_requests_text = get_storage_text_range(
                data,
                anchor_index + len(anchor),
                profit_index,
            )
            min_profit_text = get_storage_text_range(
                data,
                profit_index + len(b"Profit"),
                window_index,
            )
            time_window_text = get_storage_text_range(
                data,
                window_index + len(b"TimeWindow"),
                min(len(data), window_index + len(b"TimeWindow") + 48),
            )

            parsed = {
                "flash_min_requests": parse_number_from_storage_text(
                    min_requests_text,
                    min_value=0,
                    prefer="first",
                ),
                "flash_min_profit": parse_number_from_storage_text(
                    min_profit_text,
                    min_value=0,
                    prefer="longest",
                ),
                "flash_time_window": parse_number_from_storage_text(
                    time_window_text,
                    min_value=15,
                    max_value=240,
                    prefer="longest",
                ),
            }
            result.update({key: value for key, value in parsed.items() if value is not None})

        start = anchor_index + len(anchor)

    return result


def parse_local_storage_number(data, keys, min_value=None, max_value=None, prefer="first"):
    best_value = None

    for key in keys:
        start = 0
        key_bytes = key.encode("utf-8")
        while True:
            index = data.find(key_bytes, start)
            if index == -1:
                break

            text = get_storage_text_tail(data, index, len(key_bytes))
            parsed = parse_number_from_storage_text(
                text,
                min_value=min_value,
                max_value=max_value,
                prefer=prefer,
            )
            if parsed is not None:
                best_value = parsed

            start = index + 1

    return best_value


def coerce_storage_value(value):
    if value is None:
        return None

    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith("["):
        try:
            return json.loads(value)
        except Exception:
            return None
    if value in ("s", "b"):
        return value

    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except Exception:
        return None


def normalize_filter_number(value, default_value, min_value=None, max_value=None):
    if not isinstance(value, (int, float)):
        return default_value

    if min_value is not None and value < min_value:
        return default_value
    if max_value is not None and value > max_value:
        return default_value

    return value


def read_crossoutcore_filters():
    filters = {
        "flash_min_profit": FLASH_MIN_PROFIT,
        "flash_min_requests": FLASH_MIN_REQUESTS,
        "flash_time_window": FLASH_ANALYSIS_MINUTES,
        "flash_min_buyer_ratio": FLASH_MIN_BUYER_RATIO,
        "recycling_rarities": [],
        "recycling_buy_mode": "s",
        "recycling_sell_mode": "s",
        "recycling_show_only_sale_lots": True,
    }
    flash_cluster_filters = {}
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return filters

    chrome_user_data_path = Path(local_app_data) / "Google" / "Chrome" / "User Data"
    if not chrome_user_data_path.exists():
        return filters

    try:
        leveldb_paths = [
            path / "Local Storage" / "leveldb"
            for path in chrome_user_data_path.iterdir()
            if (path / "Local Storage" / "leveldb").exists()
        ]
        files = sorted(
            (
                path
                for leveldb_path in leveldb_paths
                for path in leveldb_path.iterdir()
                if path.suffix.lower() in (".ldb", ".log")
            ),
            key=lambda path: path.stat().st_mtime,
        )
    except Exception:
        return filters

    for path in files:
        try:
            data = path.read_bytes()
        except Exception:
            continue

        if b"crossoutcore.ru" not in data and not any(
            key.encode("utf-8") in data
            for variants in FILTER_STORAGE_KEYS.values()
            for key in variants
        ):
            continue

        for name, variants in FILTER_STORAGE_KEYS.items():
            if name in FILTER_NUMERIC_SPECS:
                spec = FILTER_NUMERIC_SPECS[name]
                parsed = parse_local_storage_number(
                    data,
                    variants,
                    min_value=spec["min"],
                    max_value=spec["max"],
                    prefer=spec["prefer"],
                )
            else:
                parsed = coerce_storage_value(parse_local_storage_value(data, variants))
            if parsed is not None:
                filters[name] = parsed

        flash_cluster_filters.update(parse_flash_filter_cluster(data))

    filters.update(flash_cluster_filters)

    filters["flash_time_window"] = normalize_filter_number(
        filters["flash_time_window"],
        FLASH_ANALYSIS_MINUTES,
        15,
        240,
    )
    # Сайт показывает таблицу "Продажа (60 мин)"; в Chrome LevelDB рядом с этим
    # ключом иногда читается служебное число 50, из-за чего список становится
    # короче сайта. Держим период ровно как у видимой таблицы.
    filters["flash_time_window"] = FLASH_ANALYSIS_MINUTES
    filters["flash_min_profit"] = normalize_filter_number(
        filters["flash_min_profit"],
        FLASH_MIN_PROFIT,
        0,
    )
    filters["flash_min_requests"] = normalize_filter_number(
        filters["flash_min_requests"],
        FLASH_MIN_REQUESTS,
        0,
    )
    filters["flash_min_buyer_ratio"] = normalize_filter_number(
        filters["flash_min_buyer_ratio"],
        FLASH_MIN_BUYER_RATIO,
        0,
        100,
    )
    filters["flash_min_buyer_ratio"] = 0
    if filters["recycling_buy_mode"] not in ("s", "b"):
        filters["recycling_buy_mode"] = "s"
    if filters["recycling_sell_mode"] not in ("s", "b"):
        filters["recycling_sell_mode"] = "s"
    if not isinstance(filters["recycling_rarities"], list):
        filters["recycling_rarities"] = []
    else:
        normalized_rarities = []
        for rarity in filters["recycling_rarities"]:
            try:
                normalized_rarity = int(rarity)
            except Exception:
                continue
            if normalized_rarity not in normalized_rarities:
                normalized_rarities.append(normalized_rarity)
        filters["recycling_rarities"] = normalized_rarities

    return filters


def clone_filters(filters):
    cloned = dict(filters)
    cloned["recycling_rarities"] = list(filters.get("recycling_rarities") or [])
    return cloned


def read_crossoutcore_filters_cached(force=False):
    global filters_cache, filters_cache_at

    now = time.monotonic()
    with filters_cache_lock:
        if (
            not force
            and filters_cache is not None
            and now - filters_cache_at <= FILTERS_CACHE_SECONDS
        ):
            return clone_filters(filters_cache)

    filters = read_crossoutcore_filters()
    with filters_cache_lock:
        filters_cache = clone_filters(filters)
        filters_cache_at = now

    return filters


def parse_timer(value):
    match = re.search(r"(\d{1,2}):(\d{2})", value)
    if not match:
        return "--:--", None

    minutes = int(match.group(1))
    seconds = int(match.group(2))
    return match.group(0), minutes * 60 + seconds


def hide_console():
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


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


def fetch_target_update():
    request = urllib.request.Request(
        URL,
        headers=HTTP_HEADERS,
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        html = response.read().decode("utf-8", "ignore")

    server_match = SERVER_TIME_RE.search(html)
    target_match = TARGET_TIME_RE.search(html)

    if not server_match or not target_match:
        return None

    server_time = int(server_match.group(1))
    target_time = int(target_match.group(1))
    return max(0, target_time - server_time)


def fetch_page_html(url):
    request = urllib.request.Request(
        url,
        headers=HTTP_HEADERS,
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", "ignore")


def parse_next_action_response(text):
    for line in text.splitlines():
        if line.startswith("1:"):
            payload = line[2:]
            payload = NEXT_ACTION_DATE_RE.sub(r'"\1"', payload)
            return json.loads(payload)

    raise ValueError("Next action payload was not found")


def post_server_action(action_id, args=None, referer=FLASH_URL):
    body = json.dumps(args or [], separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        referer,
        data=body,
        method="POST",
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/x-component",
            "Content-Type": "text/plain;charset=UTF-8",
            "Next-Action": action_id,
            "Next-Router-State-Tree": "[]",
            "Origin": "https://crossoutcore.ru",
            "Referer": referer,
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        text = response.read().decode("utf-8", "ignore")

    return parse_next_action_response(text)


def fetch_market_minutes():
    return post_server_action(MARKET_MINUTES_ACTION)


def decode_json_string(value):
    try:
        return json.loads(f'"{value}"')
    except Exception:
        return value.replace('\\"', '"')


def parse_crossout_data(page_html):
    items = {}
    market_data = {}

    for match in ITEM_PATTERN.finditer(page_html):
        item_id = int(match.group(1))
        rarity_id = None if match.group(3) == "null" else int(match.group(3))
        faction_id = None if match.group(4) == "null" else int(match.group(4))
        category_id = None if match.group(5) == "null" else int(match.group(5))
        type_id = None if match.group(6) == "null" else int(match.group(6))
        removed = int(match.group(7))
        amount = int(match.group(8))
        craftable = int(match.group(9))
        if removed:
            continue
        items[item_id] = {
            "id": item_id,
            "name": decode_json_string(match.group(2)),
            "rarity_id": rarity_id,
            "faction_id": faction_id,
            "category_id": category_id,
            "type_id": type_id,
            "removed": removed,
            "amount": amount,
            "craftable": craftable,
        }

    for match in MARKET_PATTERN.finditer(page_html):
        item_id = int(match.group(1))
        market_data[item_id] = {
            "sell": float(match.group(2)),
            "buy": float(match.group(3)),
            "sell_orders": int(match.group(4)),
            "buy_orders": int(match.group(5)),
        }

    return items, market_data


def calculate_profit_and_roi(sell_price, buy_price):
    if sell_price <= 0 or buy_price <= 0:
        return 0, 0, 0

    commission = max(0.1 * sell_price, 0.01)
    profit = sell_price - commission - buy_price
    roi = profit / buy_price * 100
    relative_spread = (sell_price - buy_price) / buy_price * 100
    return profit, roi, relative_spread


def subtract_market_commission(sell_price):
    if sell_price <= 0:
        return 0
    return sell_price - max(0.1 * sell_price, 0.01)


def build_flash_items(items_by_id, market_data, market_minutes, filters):
    flash_candidates = []
    history_window = max(1, int(filters["flash_time_window"]) // 5)

    for item_id, item in items_by_id.items():
        history = market_minutes.get(str(item_id)) or market_minutes.get(item_id)
        current = market_data.get(item_id)
        if not history or not current:
            continue

        window = history[-history_window:]
        if not window:
            continue

        max_sell_in_window = max(point.get("s", 0) for point in window)
        current_sell = current["sell"]
        current_buy = current["buy"]
        if max_sell_in_window <= 0 or current_sell <= 0 or current_buy <= 0:
            continue

        profit, roi, relative_spread = calculate_profit_and_roi(
            max_sell_in_window,
            current_sell,
        )
        total_orders = current["sell_orders"] + current["buy_orders"]
        buyer_ratio = current["buy_orders"] / total_orders * 100 if total_orders else 0

        if (
            profit < filters["flash_min_profit"]
            or current["buy_orders"] < filters["flash_min_requests"]
            or buyer_ratio < filters["flash_min_buyer_ratio"]
        ):
            continue

        flash_candidates.append(
            {
                **item,
                "kind": "flash",
                "section": "Обвалы цен",
                "score": profit,
                "profit": profit,
                "history_sell": max_sell_in_window,
                "sell": current_sell,
                "buy": current_buy,
                "sell_orders": current["sell_orders"],
                "buy_orders": current["buy_orders"],
                "roi": roi,
                "relative_spread": relative_spread,
            }
        )

    return sorted(flash_candidates, key=lambda item: item["score"], reverse=True)


def build_recycling_items(items_by_id, market_data, filters):
    # Берем те же режимы цен, что сохранены сайтом для /recycling/.
    # Сортируем именно по монетам прибыли, а не по ROI.
    if RECYCLING_FORCE_INSTANT_PROFIT_PRICES:
        filters = dict(filters)
        filters["recycling_buy_mode"] = "s"
        filters["recycling_sell_mode"] = "b"
        filters["recycling_show_only_sale_lots"] = True

    resource_prices = {}
    for key, resource in RESOURCES.items():
        data = market_data.get(resource["id"])
        if not data:
            resource_prices[key] = 0
        elif filters["recycling_sell_mode"] == "b":
            resource_prices[key] = data["buy"]
        else:
            resource_prices[key] = data["sell"]

    decor_candidates = []
    selected_rarities = set(filters["recycling_rarities"] or [])
    for item in items_by_id.values():
        item_id = item["id"]
        if (
            item["category_id"] not in PICKER_DECOR_CATEGORIES
            or item.get("removed")
            or item.get("amount", 0) <= 0
            or (selected_rarities and item.get("rarity_id") not in selected_rarities)
        ):
            continue

        current = market_data.get(item_id)
        if not current:
            continue
        if filters["recycling_show_only_sale_lots"] and current["sell_orders"] <= 0:
            continue

        # s = купить из лота продажи, b = купить по запросу на покупку.
        item_cost = (
            current["buy"] if filters["recycling_buy_mode"] == "b" else current["sell"]
        )
        if item_cost <= 0:
            continue

        recipe = RESOURCE_RECIPES.get(item.get("rarity_id"))
        if not recipe:
            continue

        gross_revenue = 0
        for resource_key, amount in recipe:
            resource = RESOURCES[resource_key]
            price = resource_prices.get(resource_key, 0)
            if price <= 0:
                gross_revenue = 0
                break
            gross_revenue += amount / resource["lot_size"] * price

        if gross_revenue <= 0:
            continue

        profit, roi, _ = calculate_profit_and_roi(gross_revenue, item_cost)
        if profit < RECYCLING_MIN_PROFIT:
            continue

        decor_candidates.append(
            {
                **item,
                "kind": "decor",
                "section": "Декор",
                "score": profit,
                "roi": roi,
                "profit": profit,
                "price": item_cost,
            }
        )

    return sorted(decor_candidates, key=lambda item: item["score"], reverse=True)


def normalize_selected_rarities(rarities):
    selected = []
    for rarity in rarities or []:
        try:
            rarity_id = int(rarity)
        except Exception:
            continue
        if rarity_id in RESOURCE_RECIPES and rarity_id not in selected:
            selected.append(rarity_id)
    return selected


def build_recycling_sale_prices(market_data, selected_rarities=None):
    resource_prices = {}
    for key, resource in RESOURCES.items():
        data = market_data.get(resource["id"])
        resource_prices[key] = data["sell"] if data else 0

    prices = {}
    rarity_ids = normalize_selected_rarities(selected_rarities)
    if not rarity_ids:
        rarity_ids = [rarity_id for rarity_id in sorted(RESOURCE_RECIPES) if rarity_id >= 3]

    for rarity_id in rarity_ids:
        recipe = RESOURCE_RECIPES.get(rarity_id)
        if not recipe:
            continue

        gross_revenue = 0
        for resource_key, amount in recipe:
            resource = RESOURCES[resource_key]
            price = resource_prices.get(resource_key, 0)
            if price <= 0:
                gross_revenue = 0
                break
            gross_revenue += amount / resource["lot_size"] * price

        if gross_revenue > 0:
            prices[rarity_id] = subtract_market_commission(gross_revenue)

    return prices


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

    try:
        with PICKER_CACHE_PATH.open("r", encoding="utf-8") as cache_file:
            data = json.load(cache_file)
    except Exception:
        return

    items = data.get("items")
    if not isinstance(items, list):
        return
    if data.get("version") != PICKER_CACHE_VERSION:
        return
    if not has_real_picker_items(items):
        return

    age_seconds = 0
    saved_at = data.get("saved_at")
    if isinstance(saved_at, str):
        try:
            saved_dt = datetime.fromisoformat(saved_at)
            age_seconds = max(0, (datetime.now() - saved_dt).total_seconds())
        except Exception:
            pass

    picker_items = items
    picker_last_refresh = time.monotonic() - age_seconds
    picker_last_success_at = time.monotonic() - age_seconds
    picker_last_item_count = count_real_picker_items(items)
    picker_last_refresh_note = "кэш"


def save_picker_cache():
    if not has_real_picker_items(picker_items):
        return

    try:
        with PICKER_CACHE_PATH.open("w", encoding="utf-8") as cache_file:
            json.dump(
                {
                    "version": PICKER_CACHE_VERSION,
                    "saved_at": datetime.now().isoformat(timespec="seconds"),
                    "items": picker_items,
                },
                cache_file,
                ensure_ascii=False,
            )
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

    primary_active = is_window_on_primary_monitor(foreground_hwnd)

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


def get_foreground_hwnd():
    try:
        return ctypes.windll.user32.GetForegroundWindow()
    except Exception:
        return 0


def is_live_window(hwnd):
    if not hwnd:
        return False

    try:
        return bool(ctypes.windll.user32.IsWindow(hwnd))
    except Exception:
        return False


def is_live_game_window(hwnd):
    return is_live_window(hwnd) and is_game_window(hwnd)


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


def get_window_info(hwnd):
    try:
        if not hwnd:
            return ""

        title_length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        title_buffer = ctypes.create_unicode_buffer(title_length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, title_buffer, title_length + 1)

        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_path = ""

        if pid.value:
            process = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                pid.value,
            )
            if process:
                try:
                    path_size = wintypes.DWORD(32768)
                    path_buffer = ctypes.create_unicode_buffer(path_size.value)
                    if ctypes.windll.kernel32.QueryFullProcessImageNameW(
                        process,
                        0,
                        path_buffer,
                        ctypes.byref(path_size),
                    ):
                        process_path = path_buffer.value
                finally:
                    ctypes.windll.kernel32.CloseHandle(process)

        return f"{title_buffer.value} {process_path}".lower()
    except Exception:
        return ""


def get_window_process_path(hwnd):
    try:
        if not hwnd:
            return ""

        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        if not pid.value:
            return ""

        process = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid.value,
        )
        if not process:
            return ""

        try:
            path_size = wintypes.DWORD(32768)
            path_buffer = ctypes.create_unicode_buffer(path_size.value)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(
                process,
                0,
                path_buffer,
                ctypes.byref(path_size),
            ):
                return path_buffer.value.lower()
        finally:
            ctypes.windll.kernel32.CloseHandle(process)

    except Exception:
        return ""

    return ""


def get_foreground_window_info():
    return get_window_info(get_foreground_hwnd())


def is_game_window(hwnd):
    process_path = get_window_process_path(hwnd)
    if not process_path:
        return False

    process_name = Path(process_path).name.lower()
    process_info = f"{process_name} {process_path}"
    return any(keyword in process_info for keyword in GAME_WINDOW_KEYWORDS)


def is_game_foreground():
    return is_game_window(get_foreground_hwnd())


def find_game_window():
    found_hwnds = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def enum_proc(hwnd, _lparam):
        if hwnd and is_game_window(hwnd):
            found_hwnds.append(hwnd)
            return False
        return True

    try:
        ctypes.windll.user32.EnumWindows(enum_proc, 0)
    except Exception as e:
        log_error("game_window", f"EnumWindows failed: {e}")

    return found_hwnds[0] if found_hwnds else 0


def restore_game_window(hwnd):
    if not hwnd:
        return False

    user32 = ctypes.windll.user32
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
            time.sleep(0.10)
        else:
            user32.ShowWindow(hwnd, SW_SHOW)

        if force_foreground_window(hwnd):
            return True

        time.sleep(0.06)
        return bool(force_foreground_window(hwnd) or is_game_window(get_foreground_hwnd()))
    except Exception as e:
        log_error("game_window", f"Restore failed: {e}")
        return False


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


def is_window_on_primary_monitor(hwnd):
    try:
        window_rect = get_hwnd_rect(hwnd)
        monitor_rect = primary_monitor_rect or get_primary_monitor_rect()

        if window_rect is None or monitor_rect is None:
            return False

        left, top, right, bottom = window_rect
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        monitor_left, monitor_top, monitor_right, monitor_bottom = monitor_rect

        return (
            monitor_left <= center_x < monitor_right
            and monitor_top <= center_y < monitor_bottom
        )
    except Exception:
        return False


def is_foreground_on_primary_monitor():
    return is_window_on_primary_monitor(get_foreground_hwnd())


def send_key(vk, key_up=False):
    flags = KEYEVENTF_KEYUP if key_up else 0
    input_event = INPUT(
        type=INPUT_KEYBOARD,
        union=INPUTUNION(
            ki=KEYBDINPUT(
                wVk=vk,
                wScan=0,
                dwFlags=flags,
                time=0,
                dwExtraInfo=None,
            )
        ),
    )
    ctypes.windll.user32.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(INPUT))


def send_key_scancode(vk, key_up=False):
    scan_code = ctypes.windll.user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
    flags = KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if key_up else 0)
    input_event = INPUT(
        type=INPUT_KEYBOARD,
        union=INPUTUNION(
            ki=KEYBDINPUT(
                wVk=0,
                wScan=scan_code,
                dwFlags=flags,
                time=0,
                dwExtraInfo=None,
            )
        ),
    )
    ctypes.windll.user32.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(INPUT))


def tap_key_scancode(vk, delay=0.025):
    send_key_scancode(vk)
    time.sleep(delay)
    send_key_scancode(vk, key_up=True)


def send_unicode_unit(unit, key_up=False):
    flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if key_up else 0)
    input_event = INPUT(
        type=INPUT_KEYBOARD,
        union=INPUTUNION(
            ki=KEYBDINPUT(
                wVk=0,
                wScan=unit,
                dwFlags=flags,
                time=0,
                dwExtraInfo=None,
            )
        ),
    )
    ctypes.windll.user32.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(INPUT))


def send_unicode_text(text):
    encoded_text = text.encode("utf-16-le", "surrogatepass")
    for index in range(0, len(encoded_text), 2):
        unit = int.from_bytes(encoded_text[index : index + 2], "little")
        send_unicode_unit(unit)
        send_unicode_unit(unit, key_up=True)
        time.sleep(0.003)


def send_mouse_button(flags):
    input_event = INPUT(
        type=INPUT_MOUSE,
        union=INPUTUNION(
            mi=MOUSEINPUT(
                dx=0,
                dy=0,
                mouseData=0,
                dwFlags=flags,
                time=0,
                dwExtraInfo=None,
            )
        ),
    )
    return ctypes.windll.user32.SendInput(
        1,
        ctypes.byref(input_event),
        ctypes.sizeof(INPUT),
    ) == 1


def send_mouse_click():
    down_ok = send_mouse_button(MOUSEEVENTF_LEFTDOWN)
    time.sleep(MOUSE_CLICK_DELAY)
    up_ok = send_mouse_button(MOUSEEVENTF_LEFTUP)
    return down_ok and up_ok


def send_mouse_right_click():
    down_ok = send_mouse_button(MOUSEEVENTF_RIGHTDOWN)
    time.sleep(MOUSE_CLICK_DELAY)
    up_ok = send_mouse_button(MOUSEEVENTF_RIGHTUP)
    return down_ok and up_ok


def get_cursor_pos():
    point = POINT()
    try:
        if ctypes.windll.user32.GetCursorPos(ctypes.byref(point)):
            return point.x, point.y
    except Exception:
        pass
    return None


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


def tap_key(vk, delay=0.004):
    # Очень быстрое нажатие клавиши через keybd_event.
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    time.sleep(delay)
    ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def send_ctrl_key(vk):
    # Очень быстрый Ctrl+клавиша.
    ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(PASTE_BETWEEN_KEYS_DELAY)
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    time.sleep(PASTE_BETWEEN_KEYS_DELAY)
    ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(PASTE_BETWEEN_KEYS_DELAY)
    ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def force_foreground_window(hwnd):
    if not hwnd:
        return False

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    foreground_hwnd = user32.GetForegroundWindow()
    if foreground_hwnd == hwnd:
        return True

    current_thread_id = kernel32.GetCurrentThreadId()
    foreground_thread_id = user32.GetWindowThreadProcessId(foreground_hwnd, None)
    target_thread_id = user32.GetWindowThreadProcessId(hwnd, None)
    attached_foreground = False
    attached_target = False

    try:
        if foreground_thread_id and foreground_thread_id != current_thread_id:
            attached_foreground = bool(
                user32.AttachThreadInput(current_thread_id, foreground_thread_id, True)
            )
        if target_thread_id and target_thread_id != current_thread_id:
            attached_target = bool(
                user32.AttachThreadInput(current_thread_id, target_thread_id, True)
            )

        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
        user32.SetFocus(hwnd)
        return user32.GetForegroundWindow() == hwnd
    finally:
        if attached_target:
            user32.AttachThreadInput(current_thread_id, target_thread_id, False)
        if attached_foreground:
            user32.AttachThreadInput(current_thread_id, foreground_thread_id, False)


def click_game_search_field(hwnd, clicks=1):
    rect = get_hwnd_rect(hwnd)
    if rect is None:
        return False

    left, top, right, bottom = rect
    width = max(1, right - left)
    height = max(1, bottom - top)
    x = left + round(width * PICKER_GAME_SEARCH_CLICK_X_RATIO)
    y = top + round(height * PICKER_GAME_SEARCH_CLICK_Y_RATIO)

    user32 = ctypes.windll.user32
    user32.SetCursorPos(x, y)
    time.sleep(PASTE_HOVER_BEFORE_CLICK_DELAY)

    clicked = False
    for _ in range(max(1, clicks)):
        user32.SetCursorPos(x, y)
        if not send_mouse_click():
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


def get_hwnd_ratio_point(hwnd, x_ratio, y_ratio):
    rect = get_hwnd_rect(hwnd)
    if rect is None:
        return None

    left, top, right, bottom = rect
    width = max(1, right - left)
    height = max(1, bottom - top)
    return left + round(width * x_ratio), top + round(height * y_ratio)


def get_screen_pixel_rgb(x, y):
    hdc = ctypes.windll.user32.GetDC(0)
    if not hdc:
        return None

    try:
        color = ctypes.windll.gdi32.GetPixel(hdc, int(x), int(y))
        if color == -1:
            return None
        return color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF
    finally:
        ctypes.windll.user32.ReleaseDC(0, hdc)


def get_hwnd_pixel_rgb(hwnd, x, y):
    rect = get_hwnd_rect(hwnd)
    if rect is None:
        return None

    left, top, _right, _bottom = rect
    hdc = ctypes.windll.user32.GetDC(hwnd)
    if not hdc:
        return None

    try:
        color = ctypes.windll.gdi32.GetPixel(hdc, int(x - left), int(y - top))
        if color == -1:
            return None
        return color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF
    finally:
        ctypes.windll.user32.ReleaseDC(hwnd, hdc)


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


def detect_market_action_stage():
    if is_game_button_visible(GAME_ORDER_BUTTON_X_RATIO, GAME_ORDER_BUTTON_Y_RATIO):
        return "quantity"
    if is_game_button_visible(GAME_BUY_BUTTON_X_RATIO, GAME_BUY_BUTTON_Y_RATIO):
        return "buy"
    return None


def move_cursor_to_game_ratio(x_ratio, y_ratio):
    hwnd = get_picker_action_hwnd()
    if not hwnd:
        return False

    point = get_hwnd_ratio_point(hwnd, x_ratio, y_ratio)
    if point is None:
        return False

    ctypes.windll.user32.SetCursorPos(point[0], point[1])
    time.sleep(PASTE_HOVER_BEFORE_CLICK_DELAY)
    return True


def click_game_ratio(x_ratio, y_ratio):
    if not move_cursor_to_game_ratio(x_ratio, y_ratio):
        return False
    return send_mouse_click()


def right_click_game_ratio(x_ratio, y_ratio):
    if not move_cursor_to_game_ratio(x_ratio, y_ratio):
        return False
    return send_mouse_right_click()


def hold_game_ratio(x_ratio, y_ratio, seconds, stop_event=None, mouse_guard=False):
    if not move_cursor_to_game_ratio(x_ratio, y_ratio):
        return False
    if mouse_guard:
        note_salvage_cursor_pos()
    return hold_left_mouse(seconds, stop_event=stop_event, mouse_guard=mouse_guard)


def open_selected_market_card():
    return click_game_ratio(GAME_OPEN_CARD_X_RATIO, GAME_OPEN_CARD_Y_RATIO)


def go_back_from_market_card():
    hwnd = get_picker_action_hwnd()
    if not hwnd:
        return False
    tap_key_scancode(VK_ESCAPE, delay=0.010)
    return True


def buy_current_market_item():
    return click_game_ratio(GAME_BUY_BUTTON_X_RATIO, GAME_BUY_BUTTON_Y_RATIO)


def increase_market_item_quantity():
    return click_game_ratio(GAME_QUANTITY_PLUS_X_RATIO, GAME_QUANTITY_PLUS_Y_RATIO)


def decrease_market_item_quantity():
    return click_game_ratio(GAME_QUANTITY_MINUS_X_RATIO, GAME_QUANTITY_MINUS_Y_RATIO)


def open_game_market_details():
    clicked_market = click_game_ratio(GAME_MARKET_TAB_X_RATIO, GAME_MARKET_TAB_Y_RATIO)
    time.sleep(GAME_SECTION_CLICK_DELAY_SECONDS)
    clicked_details = click_game_ratio(GAME_DETAILS_TAB_X_RATIO, GAME_DETAILS_TAB_Y_RATIO)
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


def salvage_click(x_ratio, y_ratio, stop_event, right=False):
    if stop_event.is_set() or not get_picker_action_hwnd():
        return False
    ok = right_click_game_ratio(x_ratio, y_ratio) if right else click_game_ratio(x_ratio, y_ratio)
    if ok:
        note_salvage_cursor_pos()
        sleep_with_stop(SALVAGE_STEP_DELAY_SECONDS, stop_event, mouse_guard=True)
    return ok


def salvage_click_no_stop(x_ratio, y_ratio):
    if not get_picker_action_hwnd():
        return False
    ok = click_game_ratio(x_ratio, y_ratio)
    if ok:
        time.sleep(SALVAGE_STEP_DELAY_SECONDS)
    return ok


def salvage_right_click_item(x_ratio, y_ratio, stop_event):
    global salvage_last_item_right_click_at

    if stop_event.is_set() or not get_picker_action_hwnd():
        return False

    if not move_cursor_to_game_ratio(x_ratio, y_ratio):
        return False
    note_salvage_cursor_pos()
    if not sleep_with_stop(SALVAGE_ITEM_HOVER_DELAY_SECONDS, stop_event, mouse_guard=True):
        return False
    since_last_right_click = time.monotonic() - salvage_last_item_right_click_at
    if since_last_right_click < SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS:
        wait_time = SALVAGE_ITEM_RIGHT_CLICK_MIN_INTERVAL_SECONDS - since_last_right_click
        if not sleep_with_stop(wait_time, stop_event, mouse_guard=True):
            return False
    if not send_mouse_right_click():
        return False
    salvage_last_item_right_click_at = time.monotonic()
    note_salvage_cursor_pos()
    return sleep_with_stop(SALVAGE_POST_RIGHT_CLICK_DELAY_SECONDS, stop_event, mouse_guard=True)


def salvage_confirm_available():
    return is_game_button_visible(SALVAGE_CONFIRM_BUTTON_X_RATIO, SALVAGE_CONFIRM_BUTTON_Y_RATIO)


def restore_salvage_sort_type():
    if not get_picker_action_hwnd():
        return False

    opened = salvage_click_no_stop(SALVAGE_SORT_DROPDOWN_X_RATIO, SALVAGE_SORT_DROPDOWN_Y_RATIO)
    if not opened:
        return False

    return salvage_click_no_stop(SALVAGE_SORT_TYPE_OPTION_X_RATIO, SALVAGE_SORT_TYPE_OPTION_Y_RATIO)


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

        if not salvage_click(SALVAGE_STORAGE_TAB_X_RATIO, SALVAGE_STORAGE_TAB_Y_RATIO, stop_event):
            return
        if not salvage_click(SALVAGE_DETAILS_TAB_X_RATIO, SALVAGE_DETAILS_TAB_Y_RATIO, stop_event):
            return
        if not salvage_click(
            SALVAGE_PRE_DECOR_CATEGORY_X_RATIO,
            SALVAGE_PRE_DECOR_CATEGORY_Y_RATIO,
            stop_event,
        ):
            return
        if not salvage_click(SALVAGE_DECOR_CATEGORY_X_RATIO, SALVAGE_DECOR_CATEGORY_Y_RATIO, stop_event):
            return
        if not salvage_click(SALVAGE_SORT_DROPDOWN_X_RATIO, SALVAGE_SORT_DROPDOWN_Y_RATIO, stop_event):
            return
        if not salvage_click(SALVAGE_SORT_NEW_OPTION_X_RATIO, SALVAGE_SORT_NEW_OPTION_Y_RATIO, stop_event):
            return

        item_y = SALVAGE_FIRST_ITEM_Y_RATIO
        while not stop_event.is_set() and get_picker_action_hwnd():
            if not salvage_right_click_item(SALVAGE_FIRST_ITEM_X_RATIO, item_y, stop_event):
                break
            if not salvage_click(
                SALVAGE_CONTEXT_DISASSEMBLE_X_RATIO,
                SALVAGE_CONTEXT_DISASSEMBLE_Y_RATIO,
                stop_event,
            ):
                break
            if not sleep_with_stop(SALVAGE_POST_MENU_CLICK_DELAY_SECONDS, stop_event, mouse_guard=True):
                break

            if not sleep_with_stop(SALVAGE_CONFIRM_WAIT_SECONDS, stop_event, mouse_guard=True):
                break
            if not salvage_confirm_available():
                append_log_line("salvage stopped: confirm button not found")
                break

            if not salvage_click(SALVAGE_ALL_BUTTON_X_RATIO, SALVAGE_ALL_BUTTON_Y_RATIO, stop_event):
                break
            if not sleep_with_stop(SALVAGE_POST_ALL_CLICK_DELAY_SECONDS, stop_event, mouse_guard=True):
                break
            if not hold_game_ratio(
                SALVAGE_CONFIRM_BUTTON_X_RATIO,
                SALVAGE_CONFIRM_BUTTON_Y_RATIO,
                SALVAGE_CONFIRM_HOLD_SECONDS,
                stop_event=stop_event,
                mouse_guard=True,
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
        if not move_cursor_to_game_ratio(GAME_ORDER_BUTTON_X_RATIO, GAME_ORDER_BUTTON_Y_RATIO):
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
            send_ctrl_key(VK_A)
            time.sleep(PASTE_BETWEEN_KEYS_DELAY)
            tap_key(VK_BACK)
            time.sleep(PASTE_AFTER_CLEAR_DELAY)
            send_ctrl_key(VK_V)
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


def get_hwnd_rect(hwnd):
    if not hwnd:
        return None

    rect = wintypes.RECT()
    if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None

    return rect.left, rect.top, rect.right, rect.bottom


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

    x = (
        left
        + round(target_width * PICKER_GAME_SEARCH_X_RATIO)
        + round(PICKER_GAME_SEARCH_GAP_PIXELS * scale)
    )
    y = (
        top
        + round(target_height * PICKER_GAME_SEARCH_Y_RATIO)
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
    foreground_hwnd = ctypes.windll.user32.GetForegroundWindow()
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


def is_virtual_key_down(vk):
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


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

        hwnd = get_window_hwnd()
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


def get_window_hwnd(window=None):
    if window is None:
        window = root

    hwnd = window.winfo_id()
    parent = ctypes.windll.user32.GetParent(hwnd)
    return parent or hwnd


def apply_no_focus_clickthrough(window, show_in_task_manager=False):
    window.update_idletasks()
    hwnd = get_window_hwnd(window)
    ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

    if show_in_task_manager:
        ex_style = (ex_style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
    else:
        ex_style = (ex_style & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW

    ex_style |= WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
    ctypes.windll.user32.SetWindowPos(
        hwnd,
        -1,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
    )


def apply_no_activate(window, show_in_task_manager=False):
    window.update_idletasks()
    hwnd = get_window_hwnd(window)
    ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

    if show_in_task_manager:
        ex_style = (ex_style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
    else:
        ex_style = (ex_style & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW

    ex_style |= WS_EX_NOACTIVATE
    ex_style &= ~WS_EX_TRANSPARENT
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
    ctypes.windll.user32.SetWindowPos(
        hwnd,
        -1,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
    )


def make_task_manager_app():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass

    try:
        apply_no_focus_clickthrough(root, show_in_task_manager=False)
    except Exception:
        pass


def show_tk_window_no_activate(window):
    try:
        window.deiconify()
        window.update_idletasks()
        hwnd = get_window_hwnd(window)
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
        window.deiconify()


def show_tk_window_on_rect_no_activate(window, rect):
    try:
        window.deiconify()
        window.update_idletasks()
        hwnd = get_window_hwnd(window)
        left, top, right, bottom = rect
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            -1,
            left,
            top,
            right - left,
            bottom - top,
            SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
    except Exception:
        window.deiconify()


def show_overlay():
    show_tk_window_no_activate(root)


def apply_window_region():
    pass


def get_monitor_rects():
    monitors = []

    def callback(hmonitor, hdc, rect, data):
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            monitor_rect = info.rcMonitor
            monitors.append(
                {
                    "primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
                    "rect": (
                        monitor_rect.left,
                        monitor_rect.top,
                        monitor_rect.right,
                        monitor_rect.bottom,
                    ),
                }
            )
        return 1

    monitor_enum_proc = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(wintypes.RECT),
        wintypes.LPARAM,
    )(callback)

    ctypes.windll.user32.EnumDisplayMonitors(0, 0, monitor_enum_proc, 0)
    for index, monitor in enumerate(monitors, start=1):
        monitor["index"] = index
    return monitors


def get_second_monitor_rect():
    monitors = get_monitor_rects()

    if ALERT_MONITOR_INDEX is not None:
        for monitor in monitors:
            if monitor["index"] == ALERT_MONITOR_INDEX:
                return monitor["rect"]

        log_error(
            "monitor",
            f"Configured monitor {ALERT_MONITOR_INDEX} was not found. "
            f"Detected monitors: {monitors}",
        )

    for monitor in monitors:
        if not monitor["primary"]:
            return monitor["rect"]

    log_error("monitor", f"Second monitor was not found. Detected monitors: {monitors}")
    return None


def get_primary_monitor_rect():
    monitors = get_monitor_rects()
    for monitor in monitors:
        if monitor["primary"]:
            return monitor["rect"]

    if monitors:
        return monitors[0]["rect"]

    log_error("monitor", "Primary monitor was not found.")
    return None


def geometry_from_rect(rect):
    left, top, right, bottom = rect
    return f"{right - left}x{bottom - top}{left:+d}{top:+d}"


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

    second_monitor_rect = get_second_monitor_rect()
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
