import json
import os
from pathlib import Path
import re
import threading
import time
import urllib.request


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
MARKET_MINUTES_ACTION = "00a3c6f09401f51e0f2f5197309fad70a0f23590be"
FLASH_ANALYSIS_MINUTES = 60
FLASH_MIN_PROFIT = 1
FLASH_MIN_REQUESTS = 0
FLASH_MIN_BUYER_RATIO = 0
FILTERS_CACHE_SECONDS = 1.5
PICKER_DECOR_CATEGORIES = {6}
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

filters_cache_lock = threading.Lock()
filters_cache = None
filters_cache_at = 0


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
            except (ValueError, OverflowError):
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
        except (json.JSONDecodeError, RecursionError):
            return None
    if value in ("s", "b"):
        return value

    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (ValueError, OverflowError):
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
    except OSError:
        return filters

    for path in files:
        try:
            data = path.read_bytes()
        except OSError:
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
            except (TypeError, ValueError, OverflowError):
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

    with filters_cache_lock:
        if (
            not force
            and filters_cache is not None
            and time.monotonic() - filters_cache_at <= FILTERS_CACHE_SECONDS
        ):
            return clone_filters(filters_cache)

        filters = read_crossoutcore_filters()
        filters_cache = clone_filters(filters)
        filters_cache_at = time.monotonic()

    return filters


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
    except json.JSONDecodeError:
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
        except (TypeError, ValueError, OverflowError):
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
