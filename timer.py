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
from datetime import datetime
from pathlib import Path
import re
import time
import urllib.request
import tkinter as tk
import tkinter.font as tkfont

FLASH_URL = "https://crossoutcore.ru/flash-crashes/"
RECYCLING_URL = "https://crossoutcore.ru/recycling/"
URL = FLASH_URL
SERVER_TIME_RE = re.compile(r'\\?"serverTime\\?":(\d+)')
TARGET_TIME_RE = re.compile(r'\\?"targetUpdateTimestamp\\?":(\d+)')

# Настройки
APP_ID = "CrossoutCore.Timer"
TEST_MODE = False
TEST_ALERT_SECONDS = 0.5
ALERT_START_SECONDS = 0
ALERT_END_SECONDS = -2
ALERT_FADE_IN_SECONDS = 0.08
ALERT_FADE_OUT_SECONDS = 0.14
ALERT_OFF_GAP_SECONDS = 0.16
ALERT_UPDATE_MS = 16
SHOW_MILLISECONDS_ALWAYS = True
ALERT_MONITOR_INDEX = 2
LOG_PATH = Path(__file__).with_name("timer.log")
PICKER_CACHE_PATH = Path(__file__).with_name("timer_items_cache.json")
PICKER_CACHE_VERSION = 8
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
PICKER_DECOR_CATEGORIES = {6}
# Координаты под 4K/масштаб: окно списка справа впритык к поиску, верх на одной высоте.
PICKER_GAME_SEARCH_X_RATIO = 0.292
PICKER_GAME_SEARCH_Y_RATIO = 0.147
PICKER_GAME_SEARCH_GAP_PIXELS = 0
PICKER_GAME_SEARCH_Y_OFFSET_PIXELS = 0
# Клик внутрь поля поиска.
PICKER_GAME_SEARCH_CLICK_X_RATIO = 0.245
PICKER_GAME_SEARCH_CLICK_Y_RATIO = 0.170
# Скорость вставки. Если игра иногда не успевает сфокусировать поле, увеличь PASTE_AFTER_CLICK_DELAY до 0.03-0.05.
PASTE_BEFORE_CLICK_DELAY = 0.002
PASTE_HOVER_BEFORE_CLICK_DELAY = 0.018
PASTE_AFTER_CLICK_DELAY = 0.030
PASTE_AFTER_CLEAR_DELAY = 0.008
PASTE_BETWEEN_KEYS_DELAY = 0.003
PASTE_BEFORE_ENTER_DELAY = 0.055
PASTE_ENTER_KEY_DELAY = 0.008
PASTE_SEARCH_CLICKS = 2
MOUSE_CLICK_DELAY = 0.006
PICKER_HOTKEY_ID = 7311
PICKER_HOTKEY_VK = 0xC0
WM_HOTKEY = 0x0312
ITEM_PICKER_TITLE = "Crossout Item Picker"
MARKET_MINUTES_ACTION = "00a3c6f09401f51e0f2f5197309fad70a0f23590be"
FLASH_ANALYSIS_MINUTES = 60
FLASH_MIN_PROFIT = 1
FLASH_MIN_REQUESTS = 0
FLASH_MIN_BUYER_RATIO = 0
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
ALERT_MIN_ALPHA = 0.00
ALERT_ALPHA = 1.00
PRIMARY_MONITOR_MIN_ALPHA = 1.00
PRIMARY_MONITOR_ALPHA = 1.00
PRIMARY_MONITOR_BORDER_THICKNESS = 24
SECOND_MONITOR_MIN_ALPHA = 1.00
SECOND_MONITOR_ALPHA = 1.00
SECOND_MONITOR_BORDER_THICKNESS = 13

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
MONITORINFOF_PRIMARY = 1
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MAPVK_VK_TO_VSC = 0
VK_CONTROL = 0x11
VK_A = 0x41
VK_V = 0x56
VK_BACK = 0x08
VK_RETURN = 0x0D


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
remaining_seconds = None
timer_base_seconds = None
timer_base_at = None
blink_on = False
last_blink_at = 0
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
picker_canvas = None
picker_canvas_window = None
picker_inner = None
picker_status = None
picker_timer_label = None
picker_target_hwnd = None
picker_last_refresh = 0
picker_refresh_lock = threading.Lock()
picker_refreshing = False
last_picker_paste_at = 0
last_picker_paste_name = None
last_alert_context_hwnd = None
overlay_width = BASE_NOTCH_WIDTH
notch_x = 0
notch_width = BASE_NOTCH_WIDTH
notch_height = BASE_NOTCH_HEIGHT
notch_radius = BASE_NOTCH_RADIUS
font_pixels = BASE_FONT_PIXELS


def log_error(key, message):
    now = time.monotonic()
    if now - last_log_times.get(key, 0) < 30:
        return

    last_log_times[key] = now
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


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
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return filters

    chrome_user_data_path = Path(local_app_data) / "Google" / "Chrome" / "User Data"
    if not chrome_user_data_path.exists():
        return filters

    keys = {
        "flash_min_profit": ("anomalyMinProfit", "Profit"),
        "flash_min_requests": ("anomalyMinBo", "MinBo"),
        "flash_time_window": ("anomalyTimeWindow", "TimeWindow"),
        "flash_min_buyer_ratio": ("anomalyMinBuyerRatio", "BuyerRatio", "uyerRatio"),
        "recycling_rarities": ("Recycling-rarities", "rarities"),
        "recycling_buy_mode": ("Recycling-buy-mode", "buy-mode"),
        "recycling_sell_mode": ("Recycling-sell-mode", "sell-mode"),
        "recycling_show_only_sale_lots": (
            "Recycling-show-only-with-sale-lots",
            "show-only-with-sale-lots",
            "how-only-with-sale-lots",
        ),
    }

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
            key.encode("utf-8") in data for variants in keys.values() for key in variants
        ):
            continue

        for name, variants in keys.items():
            parsed = coerce_storage_value(parse_local_storage_value(data, variants))
            if parsed is not None:
                filters[name] = parsed

    filters["flash_time_window"] = normalize_filter_number(
        filters["flash_time_window"],
        FLASH_ANALYSIS_MINUTES,
        15,
        240,
    )
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


def update_picker_timer_label():
    if picker_timer_label is None:
        return

    if remaining_seconds is None:
        text = "До обновления: --:--"
    else:
        text = f"До обновления: {format_seconds(remaining_seconds)}"

    picker_timer_label.configure(text=text)


def fetch_target_update():
    request = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Encoding": "identity",
        },
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
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Encoding": "identity",
        },
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", "ignore")


def parse_next_action_response(text):
    for line in text.splitlines():
        if line.startswith("1:"):
            payload = line[2:]
            payload = re.sub(r'"\$D([^"]+)"', r'"\1"', payload)
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
    item_pattern = re.compile(
        r'\{\\"id\\":(\d+),\\"name\\":\\"(.*?)\\",\\"rarityId\\":'
        r'(null|\d+),\\"factionId\\":(null|\d+),\\"categoryId\\":'
        r'(null|\d+),\\"typeId\\":(null|\d+).*?\\"removed\\":(\d+),'
        r'\\"amount\\":(\d+),\\"craftable\\":(\d+)',
        re.DOTALL,
    )
    market_pattern = re.compile(
        r'\\"(\d+)\\":\{\\"s\\":([0-9.]+),\\"b\\":([0-9.]+),'
        r'\\"so\\":(\d+),\\"bo\\":(\d+),[^}]*?\\"t\\":(\d+)\}'
    )

    for match in item_pattern.finditer(page_html):
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

    for match in market_pattern.finditer(page_html):
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


def build_recycling_items(items_by_id, market_data, excluded_ids, filters):
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
            item_id in excluded_ids
            or item["category_id"] not in PICKER_DECOR_CATEGORIES
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


def build_picker_items():
    flash_html = fetch_page_html(FLASH_URL)
    items_by_id, market_data = parse_crossout_data(flash_html)

    if not items_by_id:
        raise ValueError("No Crossout items parsed")

    try:
        recycling_html = fetch_page_html(RECYCLING_URL)
        recycling_items_by_id, recycling_market_data = parse_crossout_data(recycling_html)
        if not recycling_items_by_id or not recycling_market_data:
            raise ValueError("No recycling data parsed")
    except Exception as e:
        log_error("picker_recycling_fetch", f"Recycling page fetch failed: {e}")
        recycling_items_by_id = items_by_id
        recycling_market_data = market_data

    filters = read_crossoutcore_filters()
    market_minutes = fetch_market_minutes()
    flash_items = build_flash_items(items_by_id, market_data, market_minutes, filters)
    flash_item_ids = {item["id"] for item in flash_items}
    decor_items = build_recycling_items(
        recycling_items_by_id,
        recycling_market_data,
        flash_item_ids,
        filters,
    )

    decor_sale_prices = build_recycling_sale_prices(
        recycling_market_data,
        filters["recycling_rarities"],
    )

    result = (
        flash_items
        + ([{"separator": True, "section": "Декор"}] if decor_items else [])
        + ([{"decor_prices": True, "prices": decor_sale_prices}] if decor_items else [])
        + decor_items
    )
    if not any(not item.get("separator") for item in result):
        return [{"separator": True, "section": "Предметы не найдены"}]

    return result


def refresh_picker_items(force=False):
    global picker_items, picker_last_refresh, picker_refreshing

    now = time.monotonic()
    if not force and picker_items and now - picker_last_refresh < PICKER_REFRESH_SECONDS:
        return

    if not picker_refresh_lock.acquire(blocking=False):
        return

    picker_refreshing = True
    try:
        fresh_items = build_picker_items()
        picker_items = fresh_items
        picker_last_refresh = now
        save_picker_cache()
    except Exception as e:
        log_error("picker_fetch", f"Picker item fetch failed: {e}")
        if not picker_items:
            picker_items = [{"separator": True, "section": "Не удалось загрузить предметы"}]
    finally:
        picker_refreshing = False
        picker_refresh_lock.release()


def load_picker_cache():
    global picker_items, picker_last_refresh

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

    # Старый кэш может показывать декор, который уже перестал быть прибыльным.
    # Поэтому не используем кэш старше PICKER_CACHE_MAX_AGE_SECONDS.
    age_seconds = PICKER_CACHE_MAX_AGE_SECONDS + 1
    saved_at = data.get("saved_at")
    if isinstance(saved_at, str):
        try:
            saved_dt = datetime.fromisoformat(saved_at)
            age_seconds = max(0, (datetime.now() - saved_dt).total_seconds())
        except Exception:
            pass

    if age_seconds > PICKER_CACHE_MAX_AGE_SECONDS:
        picker_items = []
        picker_last_refresh = 0
        return

    picker_items = items
    picker_last_refresh = time.monotonic() - age_seconds


def save_picker_cache():
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
    if picker_window is not None and picker_window.state() != "withdrawn":
        populate_picker()


def refresh_picker_and_repaint(force=False):
    refresh_picker_items(force=force)
    root.after(0, repaint_picker_if_visible)


def picker_refresh_worker():
    while True:
        refresh_picker_and_repaint(force=True)
        time.sleep(PICKER_BACKGROUND_REFRESH_SECONDS)


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
            canvas.itemconfig(timer_text, text=display_value)

    if timer_base_seconds is not None:
        if timer_base_at is None:
            smooth_seconds = timer_base_seconds
        elif TEST_MODE:
            smooth_seconds = timer_base_seconds
        else:
            smooth_seconds = timer_base_seconds - (time.monotonic() - timer_base_at)

        remaining_seconds = smooth_seconds
        canvas.itemconfig(timer_text, text=format_seconds(smooth_seconds))

    update_colors()
    update_picker_timer_label()

    root.after(ALERT_UPDATE_MS, update_label)


def update_colors():
    if not is_alert_window(remaining_seconds):
        set_alert_visible(False)
        set_primary_monitor_alert(False)
        set_second_monitor_alert(False)
        return

    pulse = get_alert_pulse()
    if pulse <= 0:
        set_alert_visible(False)
        set_primary_monitor_alert(False)
        set_second_monitor_alert(False)
        return

    context_hwnd = get_alert_context_hwnd()
    game_active = is_game_window(context_hwnd)
    primary_active = is_window_on_primary_monitor(context_hwnd)

    if game_active:
        set_alert_visible(False)
        set_primary_monitor_alert(False)
        set_second_monitor_alert(True, pulse)
    elif TEST_MODE or primary_active:
        set_alert_visible(True, pulse)
        set_primary_monitor_alert(True, pulse)
        set_second_monitor_alert(False)
    else:
        set_alert_visible(False)
        set_primary_monitor_alert(False)
        set_second_monitor_alert(False)


def get_alert_pulse():
    cycle = ALERT_FADE_IN_SECONDS + ALERT_FADE_OUT_SECONDS + ALERT_OFF_GAP_SECONDS
    position = time.monotonic() % cycle

    if position < ALERT_FADE_IN_SECONDS:
        progress = position / ALERT_FADE_IN_SECONDS
        return progress * progress * (3 - 2 * progress)

    position -= ALERT_FADE_IN_SECONDS
    if position < ALERT_FADE_OUT_SECONDS:
        progress = position / ALERT_FADE_OUT_SECONDS
        eased = progress * progress * (3 - 2 * progress)
        return 1 - eased

    return 0


def set_notch_colors(bg, fg, alpha):
    root.attributes("-alpha", alpha)
    for item in notch_items:
        canvas.itemconfig(item, fill=bg)
    canvas.itemconfig(timer_text, fill=fg)


def set_alert_visible(is_visible, pulse=0):
    if is_visible:
        root.attributes("-alpha", ALERT_ALPHA)
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
        primary_monitor_alert.attributes("-alpha", PRIMARY_MONITOR_ALPHA)
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
        second_monitor_alert.attributes("-alpha", SECOND_MONITOR_ALPHA)
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
    return picker_window is not None and picker_window.state() != "withdrawn"


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


def get_foreground_window_info():
    return get_window_info(get_foreground_hwnd())


def is_game_window(hwnd):
    window_info = get_window_info(hwnd)
    return any(keyword in window_info for keyword in GAME_WINDOW_KEYWORDS)


def is_game_foreground():
    return is_game_window(get_foreground_hwnd())


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

def _log_direct(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


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


def paste_item_name(name):
    global last_picker_paste_at, last_picker_paste_name, picker_target_hwnd

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

    threading.Thread(target=do_paste, daemon=True).start()


def get_hwnd_rect(hwnd):
    if not hwnd:
        return None

    rect = wintypes.RECT()
    if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None

    return rect.left, rect.top, rect.right, rect.bottom


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
    total_height = PICKER_HEIGHT + PICKER_TIMER_HEIGHT
    y -= PICKER_TIMER_HEIGHT

    x = min(max(left, x), right - PICKER_WIDTH)
    y = min(max(top, y), bottom - total_height)

    picker_window.geometry(f"{PICKER_WIDTH}x{total_height}{x:+d}{y:+d}")


def clear_picker_rows():
    if picker_inner is None:
        return

    for child in picker_inner.winfo_children():
        child.destroy()


def add_picker_separator(text):
    frame = tk.Frame(picker_inner, bg="#181818", height=34)
    frame.pack(fill="x", padx=8, pady=(8, 4))
    frame.pack_propagate(False)

    left = tk.Frame(frame, bg="#3a3a3a", height=1)
    left.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=16)

    label = tk.Label(
        frame,
        text=text,
        fg="#d7d7d7",
        bg="#181818",
        font=("Segoe UI", 10, "bold"),
    )
    label.pack(side="left")

    right = tk.Frame(frame, bg="#3a3a3a", height=1)
    right.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=16)


def show_picker_message(text):
    clear_picker_rows()
    add_picker_separator(text)
    picker_inner.update_idletasks()
    picker_canvas.configure(scrollregion=picker_canvas.bbox("all"))


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


def add_picker_item_row(item):
    row = tk.Frame(picker_inner, bg="#101418", height=PICKER_ROW_HEIGHT, cursor="hand2")
    row.pack(fill="x", padx=8, pady=2)
    row.pack_propagate(False)

    kind = get_picker_item_kind(item)
    profit_text = format_picker_profit(item)
    profit_base_bg = "#101418"
    profit_hover_bg = "#1b242c"

    name_label = tk.Label(
        row,
        text=item["name"],
        fg="#f0cf23",
        bg="#101418",
        anchor="w",
        font=("Segoe UI", 11, "bold"),
    )
    name_label.pack(side="left", fill="both", expand=True, padx=(12, 8))

    profit_label = None
    if item.get("section") == "Декор":
        profit_label = tk.Label(
            row,
            text=format_picker_profit(item),
            fg="#67e86f",
            bg="#101418",
            anchor="e",
            font=("Segoe UI", 10, "bold"),
            width=7,
        )
        profit_label.pack(side="right", fill="y", padx=(0, 12))

    if profit_label is None and kind == "flash" and profit_text:
        profit_base_bg = "#f0cf23"
        profit_hover_bg = "#ffe04c"
        profit_label = tk.Label(
            row,
            text=profit_text,
            fg="#111111",
            bg=profit_base_bg,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
            width=7,
            padx=6,
        )
        profit_label.pack(side="right", fill="y")

    def on_enter(event):
        row.configure(bg="#1b242c")
        name_label.configure(bg="#1b242c")
        if profit_label is not None:
            profit_label.configure(bg=profit_hover_bg)

    def on_leave(event):
        row.configure(bg="#101418")
        name_label.configure(bg="#101418")
        if profit_label is not None:
            profit_label.configure(bg=profit_base_bg)

    def on_click(event):
        paste_item_name(item["name"])

    clickable_widgets = [row, name_label]
    if profit_label is not None:
        clickable_widgets.append(profit_label)

    for widget in clickable_widgets:
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<Button-1>", on_click)
        widget.bind("<ButtonRelease-1>", on_click)


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


def add_picker_cell(
    parent,
    text,
    width,
    height,
    fg,
    bg,
    anchor="e",
    font=("Segoe UI", 9, "bold"),
    padx=(6, 6),
):
    frame = tk.Frame(parent, bg=bg, width=width, height=height)
    frame.pack(side="left", fill="y")
    frame.pack_propagate(False)

    label = tk.Label(
        frame,
        text=text,
        fg=fg,
        bg=bg,
        anchor=anchor,
        font=font,
    )
    label.pack(fill="both", expand=True, padx=padx)
    return frame, label


def add_picker_header_cell(parent, text, width, bg="#181818", fg="#c7ced8", anchor="e"):
    return add_picker_cell(
        parent,
        text,
        width,
        PICKER_HEADER_HEIGHT,
        fg,
        bg,
        anchor=anchor,
        font=("Segoe UI", 8, "bold"),
        padx=(5, 5),
    )


def add_picker_table_header(kind):
    row = tk.Frame(picker_inner, bg="#181818", height=PICKER_HEADER_HEIGHT)
    row.pack(fill="x", padx=8, pady=(0, 2))
    row.pack_propagate(False)

    if kind == "flash":
        columns = [
            ("Название", PICKER_NAME_COL_WIDTH, "#181818", "#aeb7c6", "w"),
            ("60 мин", PICKER_FLASH_HISTORY_COL_WIDTH, "#d69d34", "#111111", "e"),
            ("Продажа", PICKER_FLASH_PRICE_COL_WIDTH, "#08aeca", "#111111", "e"),
            ("Покупка", PICKER_FLASH_PRICE_COL_WIDTH, "#08aeca", "#111111", "e"),
            ("Предл.", PICKER_FLASH_ORDER_COL_WIDTH, "#181818", "#aeb7c6", "e"),
            ("Запр.", PICKER_FLASH_ORDER_COL_WIDTH, "#181818", "#aeb7c6", "e"),
            ("ROI", PICKER_FLASH_ROI_COL_WIDTH, "#7ac36f", "#111111", "e"),
            ("Прибыль", PICKER_PROFIT_COL_WIDTH, "#f0cf23", "#111111", "w"),
        ]
    else:
        columns = [
            ("Предмет", PICKER_DECOR_NAME_COL_WIDTH, "#181818", "#aeb7c6", "w"),
            ("Прибыль", PICKER_DECOR_VALUE_COL_WIDTH, "#181818", "#67e86f", "e"),
            ("Цена", PICKER_DECOR_VALUE_COL_WIDTH, "#181818", "#dfe7f3", "e"),
            ("ROI", PICKER_DECOR_VALUE_COL_WIDTH, "#181818", "#67e86f", "e"),
        ]

    for text, width, bg, fg, anchor in columns:
        add_picker_header_cell(row, text, width, bg=bg, fg=fg, anchor=anchor)


def measure_picker_header(text, minimum):
    try:
        font = tkfont.Font(family="Segoe UI", size=8, weight="bold")
        return max(minimum, font.measure(text) + 24)
    except Exception:
        return minimum


def get_picker_table_inner_width():
    return PICKER_WIDTH - 36


def get_picker_columns(kind):
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

    name_width = max(
        measure_picker_header(name_title, name_min_width),
        get_picker_table_inner_width() - sum(column["width"] for column in value_columns),
    )
    return [
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


def get_picker_column_map(kind):
    return {column["key"]: column for column in get_picker_columns(kind)}


def add_picker_table_header(kind):
    row = tk.Frame(picker_inner, bg="#181818", height=PICKER_HEADER_HEIGHT)
    row.pack(fill="x", padx=8, pady=(0, 2))
    row.pack_propagate(False)

    for column in get_picker_columns(kind):
        add_picker_header_cell(
            row,
            column["title"],
            column["width"],
            bg=column["bg"],
            fg=column["fg"],
            anchor=column["anchor"],
        )


def get_price_for_rarity(prices, rarity_id):
    return prices.get(rarity_id, prices.get(str(rarity_id)))


def add_picker_decor_prices(prices):
    row = tk.Frame(picker_inner, bg="#101418", height=42)
    row.pack(fill="x", padx=8, pady=(0, 4))
    row.pack_propagate(False)

    title = tk.Label(
        row,
        text="По цене продажи:",
        fg="#c7ced8",
        bg="#101418",
        anchor="w",
        font=("Segoe UI", 9, "bold"),
    )
    title.pack(side="left", fill="y", padx=(10, 8))

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
        chip = tk.Frame(row, bg="#151b21", height=28)
        chip.pack(side="left", padx=(0, 6), pady=7)

        label = tk.Label(
            chip,
            text=f'{style["short"]} {format_picker_number(price)}',
            fg=style["color"],
            bg="#151b21",
            anchor="center",
            font=("Segoe UI", 9, "bold"),
        )
        label.pack(fill="both", expand=True, padx=8)


def add_picker_value_cell(
    row,
    text,
    width,
    fg="#dfe7f3",
    bg="#101418",
    hover_bg="#1b242c",
    anchor="e",
    font=("Segoe UI", 9, "bold"),
    padx=(6, 6),
):
    frame, label = add_picker_cell(
        row,
        text,
        width,
        PICKER_ROW_HEIGHT,
        fg,
        bg,
        anchor=anchor,
        font=font,
        padx=padx,
    )
    return {
        "widgets": (frame, label),
        "base_bg": bg,
        "hover_bg": hover_bg,
    }


def add_picker_item_row(item):
    kind = get_picker_item_kind(item)
    row = tk.Frame(picker_inner, bg="#101418", height=PICKER_ROW_HEIGHT, cursor="hand2")
    row.pack(fill="x", padx=8, pady=1)
    row.pack_propagate(False)

    cells = []
    column_map = get_picker_column_map(kind)
    if kind == "flash":
        cells.extend(
            [
                add_picker_value_cell(
                    row,
                    item["name"],
                    column_map["name"]["width"],
                    fg="#f0cf23",
                    anchor="w",
                    font=("Segoe UI", 9, "bold"),
                    padx=(8, 5),
                ),
                add_picker_value_cell(
                    row,
                    format_picker_number(item.get("history_sell")),
                    column_map["history_sell"]["width"],
                    fg="#111111",
                    bg="#d69d34",
                    hover_bg="#e9b64d",
                ),
                add_picker_value_cell(
                    row,
                    format_picker_number(item.get("sell")),
                    column_map["sell"]["width"],
                    fg="#111111",
                    bg="#08aeca",
                    hover_bg="#21c2dd",
                ),
                add_picker_value_cell(
                    row,
                    format_picker_number(item.get("buy")),
                    column_map["buy"]["width"],
                    fg="#111111",
                    bg="#08aeca",
                    hover_bg="#21c2dd",
                ),
                add_picker_value_cell(
                    row,
                    format_picker_int(item.get("sell_orders")),
                    column_map["sell_orders"]["width"],
                ),
                add_picker_value_cell(
                    row,
                    format_picker_int(item.get("buy_orders")),
                    column_map["buy_orders"]["width"],
                ),
                add_picker_value_cell(
                    row,
                    format_picker_roi(item),
                    column_map["roi"]["width"],
                    fg="#111111",
                    bg="#7ac36f",
                    hover_bg="#8dd982",
                    anchor="center",
                ),
                add_picker_value_cell(
                    row,
                    format_picker_profit(item),
                    column_map["profit"]["width"],
                    fg="#111111",
                    bg="#f0cf23",
                    hover_bg="#ffe04c",
                    anchor="w",
                    padx=(7, 5),
                ),
            ]
        )
    else:
        cells.extend(
            [
                add_picker_value_cell(
                    row,
                    item["name"],
                    column_map["name"]["width"],
                    fg=get_picker_rarity_color(item),
                    anchor="w",
                    font=("Segoe UI", 9, "bold"),
                    padx=(8, 5),
                ),
                add_picker_value_cell(
                    row,
                    format_picker_profit(item),
                    column_map["profit"]["width"],
                    fg="#67e86f",
                ),
                add_picker_value_cell(
                    row,
                    format_picker_number(item.get("price")),
                    column_map["price"]["width"],
                ),
                add_picker_value_cell(
                    row,
                    format_picker_roi(item),
                    column_map["roi"]["width"],
                    fg="#67e86f",
                ),
            ]
        )

    clickable_widgets = [row]
    for cell in cells:
        clickable_widgets.extend(cell["widgets"])

    def on_enter(event):
        row.configure(bg="#1b242c")
        for cell in cells:
            for widget in cell["widgets"]:
                widget.configure(bg=cell["hover_bg"])

    def on_leave(event):
        row.configure(bg="#101418")
        for cell in cells:
            for widget in cell["widgets"]:
                widget.configure(bg=cell["base_bg"])

    def on_click(event):
        paste_item_name(item["name"])

    for widget in clickable_widgets:
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<Button-1>", on_click)
        widget.bind("<ButtonRelease-1>", on_click)


def populate_picker():
    clear_picker_rows()

    current_section = None
    header_section = None
    for item in picker_items:
        if item.get("separator"):
            add_picker_separator(item["section"])
            current_section = item["section"]
            header_section = None
            continue

        if item.get("decor_prices"):
            add_picker_decor_prices(item.get("prices", {}))
            continue

        if item.get("section") != current_section:
            add_picker_separator(item["section"])
            current_section = item["section"]
            header_section = None

        if current_section != header_section:
            add_picker_table_header(get_picker_item_kind(item))
            header_section = current_section

        add_picker_item_row(item)

    picker_inner.update_idletasks()
    picker_canvas.configure(scrollregion=picker_canvas.bbox("all"))

    if picker_status is not None:
        picker_status.configure(text="")


def create_picker_window():
    global picker_canvas, picker_canvas_window, picker_inner, picker_status
    global picker_timer_label, picker_window

    if picker_window is not None:
        return

    picker_window = tk.Toplevel(root)
    picker_window.withdraw()
    picker_window.title(ITEM_PICKER_TITLE)
    picker_window.overrideredirect(True)
    picker_window.configure(bg="#30363d")
    picker_window.attributes("-topmost", True)
    picker_window.protocol("WM_DELETE_WINDOW", picker_window.withdraw)
    picker_window.bind("<Escape>", lambda event: picker_window.withdraw())

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
    picker_timer_label.pack(fill="both", expand=True)

    list_frame = tk.Frame(body, bg="#0b0f14")
    list_frame.pack(side="top", fill="both", expand=True)

    picker_canvas = tk.Canvas(
        list_frame,
        bg="#0b0f14",
        highlightthickness=0,
        bd=0,
    )
    scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=picker_canvas.yview)
    picker_canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    picker_canvas.pack(side="left", fill="both", expand=True)

    picker_inner = tk.Frame(picker_canvas, bg="#0b0f14")
    picker_canvas_window = picker_canvas.create_window(
        (0, 0),
        window=picker_inner,
        anchor="nw",
    )

    def on_canvas_configure(event):
        picker_canvas.itemconfigure(picker_canvas_window, width=event.width)

    def on_mousewheel(event):
        picker_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    picker_canvas.bind("<Configure>", on_canvas_configure)
    picker_window.bind("<MouseWheel>", on_mousewheel)

    picker_status = None
    update_picker_timer_label()
    apply_no_activate(picker_window)


def show_picker():
    global picker_target_hwnd

    foreground_hwnd = ctypes.windll.user32.GetForegroundWindow()
    if foreground_hwnd and not is_own_overlay_hwnd(foreground_hwnd):
        picker_target_hwnd = foreground_hwnd
    elif last_alert_context_hwnd:
        picker_target_hwnd = last_alert_context_hwnd
    create_picker_window()

    if picker_window.state() != "withdrawn":
        picker_window.withdraw()
        return

    position_picker_window()
    show_tk_window_no_activate(picker_window)
    update_picker_timer_label()

    if picker_items:
        populate_picker()
    else:
        show_picker_message("Загрузка...")

    if not picker_refreshing:
        threading.Thread(
            target=lambda: refresh_picker_and_repaint(force=True),
            daemon=True,
        ).start()


def hotkey_worker():
    try:
        if not ctypes.windll.user32.RegisterHotKey(
            None,
            PICKER_HOTKEY_ID,
            0,
            PICKER_HOTKEY_VK,
        ):
            log_error("hotkey", "RegisterHotKey failed for ё / `")
            return

        msg = MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY and msg.wParam == PICKER_HOTKEY_ID:
                hotkey_q.put("picker")
    except Exception as e:
        log_error("hotkey", f"Hotkey worker failed: {e}")


def check_hotkeys():
    while not hotkey_q.empty():
        event = hotkey_q.get()
        if event == "picker":
            show_picker()

    root.after(50, check_hotkeys)


def keep_on_top():
    try:
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
show_overlay()
root.after(500, make_task_manager_app)

load_picker_cache()
threading.Thread(target=timer_worker, daemon=True).start()
threading.Thread(target=hotkey_worker, daemon=True).start()
threading.Thread(target=picker_refresh_worker, daemon=True).start()

keep_on_top()
update_label()
check_hotkeys()
root.mainloop()
