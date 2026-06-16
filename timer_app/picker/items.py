def has_real_picker_items(items):
    return any(
        isinstance(item, dict)
        and not item.get("separator")
        and not item.get("decor_prices")
        for item in items or []
    )


def count_real_picker_items(items):
    return sum(
        1
        for item in items or []
        if isinstance(item, dict)
        and not item.get("separator")
        and not item.get("decor_prices")
    )


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
    from timer_app.crossout import RARITY_STYLES

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


def get_price_for_rarity(prices, rarity_id):
    return prices.get(rarity_id, prices.get(str(rarity_id)))


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


def build_picker_display_rows(items, header_height, row_height):
    rows = []
    y = 0
    current_section = None
    header_section = None

    def add_row(row_type, height, **data):
        nonlocal y
        row = {"type": row_type, "y": y, "height": height, **data}
        rows.append(row)
        y += height

    for item in items:
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
            add_row("header", header_height, kind=get_picker_item_kind(item))
            header_section = current_section

        add_row("item", row_height, item=item, kind=get_picker_item_kind(item))

    return rows, y


def get_picker_canvas_row_at(rows, canvas_y):
    for index, row in enumerate(rows):
        if row["y"] <= canvas_y < row["y"] + row["height"]:
            return index, row
    return None, None


def get_picker_item_row_indices(rows):
    return [
        index
        for index, row in enumerate(rows)
        if row.get("type") == "item" and row.get("item")
    ]
