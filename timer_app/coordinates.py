import json
from copy import deepcopy


DEFAULT_PIXEL_BASE_WIDTH = 3840
DEFAULT_PIXEL_BASE_HEIGHT = 2160


def _pixel_point(x, y, description):
    return {
        "x": x,
        "y": y,
        "description": description,
    }


DEFAULT_COORDINATES = {
    "picker.window_anchor": _pixel_point(
        1121,
        318,
        "Picker window anchor near the in-game search area.",
    ),
    "picker.search_field": _pixel_point(
        941,
        367,
        "Click point inside the in-game search field.",
    ),
    "market.open_card": _pixel_point(
        2074,
        607,
        "Open the selected market item card.",
    ),
    "market.buy_button": _pixel_point(
        265,
        1953,
        "Buy button on a market item card.",
    ),
    "market.order_button": _pixel_point(
        1978,
        1410,
        "Create order button in the market quantity dialog.",
    ),
    "market.quantity_plus": _pixel_point(
        2008,
        1106,
        "Increase market order quantity.",
    ),
    "market.quantity_minus": _pixel_point(
        1801,
        1106,
        "Decrease market order quantity.",
    ),
    "market.market_tab": _pixel_point(
        1471,
        71,
        "Market tab in the item details view.",
    ),
    "market.details_tab": _pixel_point(
        1617,
        190,
        "Details tab in the market view.",
    ),
    "market.sell_button": _pixel_point(
        1409,
        1959,
        "Sell button on the market item screen.",
    ),
    "market.sell_price_field": _pixel_point(
        1900,
        813,
        "Price field in the sell dialog.",
    ),
    "market.sell_all_button": _pixel_point(
        2218,
        1190,
        "All quantity button in the sell dialog.",
    ),
    "market.sell_confirm_button": _pixel_point(
        1987,
        1500,
        "Confirm button in the sell dialog.",
    ),
    "salvage.storage_tab": _pixel_point(
        1654,
        79,
        "Storage tab before salvage actions.",
    ),
    "salvage.details_tab": _pixel_point(
        1256,
        181,
        "Details tab before salvage actions.",
    ),
    "salvage.pre_decor_category": _pixel_point(
        1628,
        364,
        "TODO_NAMING_REVIEW: preliminary click before selecting decor category.",
    ),
    "salvage.decor_category": _pixel_point(
        1311,
        364,
        "Decor category in storage.",
    ),
    "salvage.sort_dropdown": _pixel_point(
        3419,
        367,
        "Sort dropdown in storage.",
    ),
    "salvage.sort_new_option": _pixel_point(
        3366,
        940,
        "Sort by newest option.",
    ),
    "salvage.sort_type_option": _pixel_point(
        3371,
        465,
        "Sort by type option.",
    ),
    "salvage.first_item": _pixel_point(
        257,
        691,
        "First salvageable item in the storage list.",
    ),
    "salvage.selected_item": _pixel_point(
        257,
        691,
        "Selected salvage item in the storage list.",
    ),
    "salvage.context_disassemble": _pixel_point(
        230,
        1310,
        "Disassemble action in the item context menu.",
    ),
    "salvage.context_disassemble_probe_top": _pixel_point(
        271,
        1221,
        "White pixel probe for the upper disassemble menu option.",
    ),
    "salvage.context_disassemble_option_top": _pixel_point(
        230,
        1315,
        "Upper disassemble menu option selected when the upper probe is white.",
    ),
    "salvage.context_disassemble_probe_bottom": _pixel_point(
        271,
        1317,
        "White pixel probe for the lower disassemble menu option.",
    ),
    "salvage.context_disassemble_option_bottom": _pixel_point(
        231,
        1402,
        "Lower disassemble menu option selected when the lower probe is white.",
    ),
    "salvage.all_button": _pixel_point(
        1934,
        1019,
        "All button in the disassemble dialog.",
    ),
    "salvage.confirm_button": _pixel_point(
        1921,
        1469,
        "Confirm button in the disassemble dialog.",
    ),
    "salvage.stop_finish_click": _pixel_point(
        1519,
        362,
        "TODO_NAMING_REVIEW: P014 final click after stopping salvage.",
    ),
}

LEGACY_COORDINATE_NAMES = {
    "PICKER_GAME_SEARCH_X_RATIO / PICKER_GAME_SEARCH_Y_RATIO": "picker.window_anchor",
    "PICKER_GAME_SEARCH_CLICK_X_RATIO / PICKER_GAME_SEARCH_CLICK_Y_RATIO": "picker.search_field",
    "GAME_OPEN_CARD_X_RATIO / GAME_OPEN_CARD_Y_RATIO": "market.open_card",
    "GAME_BUY_BUTTON_X_RATIO / GAME_BUY_BUTTON_Y_RATIO": "market.buy_button",
    "GAME_ORDER_BUTTON_X_RATIO / GAME_ORDER_BUTTON_Y_RATIO": "market.order_button",
    "GAME_QUANTITY_PLUS_X_RATIO / GAME_QUANTITY_PLUS_Y_RATIO": "market.quantity_plus",
    "GAME_QUANTITY_MINUS_X_RATIO / GAME_QUANTITY_MINUS_Y_RATIO": "market.quantity_minus",
    "GAME_MARKET_TAB_X_RATIO / GAME_MARKET_TAB_Y_RATIO": "market.market_tab",
    "GAME_DETAILS_TAB_X_RATIO / GAME_DETAILS_TAB_Y_RATIO": "market.details_tab",
    "GAME_SELL_BUTTON_X_RATIO / GAME_SELL_BUTTON_Y_RATIO": "market.sell_button",
    "GAME_SELL_PRICE_CLICK_X_RATIO / GAME_SELL_PRICE_CLICK_Y_RATIO": "market.sell_price_field",
    "GAME_SELL_ALL_BUTTON_X_RATIO / GAME_SELL_ALL_BUTTON_Y_RATIO": "market.sell_all_button",
    "GAME_SELL_CONFIRM_BUTTON_X_RATIO / GAME_SELL_CONFIRM_BUTTON_Y_RATIO": "market.sell_confirm_button",
    "SALVAGE_STORAGE_TAB_X_RATIO / SALVAGE_STORAGE_TAB_Y_RATIO": "salvage.storage_tab",
    "SALVAGE_DETAILS_TAB_X_RATIO / SALVAGE_DETAILS_TAB_Y_RATIO": "salvage.details_tab",
    "SALVAGE_PRE_DECOR_CATEGORY_X_RATIO / SALVAGE_PRE_DECOR_CATEGORY_Y_RATIO": (
        "salvage.pre_decor_category"
    ),
    "SALVAGE_DECOR_CATEGORY_X_RATIO / SALVAGE_DECOR_CATEGORY_Y_RATIO": "salvage.decor_category",
    "SALVAGE_SORT_DROPDOWN_X_RATIO / SALVAGE_SORT_DROPDOWN_Y_RATIO": "salvage.sort_dropdown",
    "SALVAGE_SORT_NEW_OPTION_X_RATIO / SALVAGE_SORT_NEW_OPTION_Y_RATIO": "salvage.sort_new_option",
    "SALVAGE_SORT_TYPE_OPTION_X_RATIO / SALVAGE_SORT_TYPE_OPTION_Y_RATIO": "salvage.sort_type_option",
    "SALVAGE_FIRST_ITEM_X_RATIO / SALVAGE_FIRST_ITEM_Y_RATIO": "salvage.first_item",
    "SALVAGE_SELECT_ITEM_X_RATIO / SALVAGE_SELECT_ITEM_Y_RATIO": "salvage.selected_item",
    "SALVAGE_CONTEXT_DISASSEMBLE_X_RATIO / SALVAGE_CONTEXT_DISASSEMBLE_Y_RATIO": (
        "salvage.context_disassemble"
    ),
    "SALVAGE_ALL_BUTTON_X_RATIO / SALVAGE_ALL_BUTTON_Y_RATIO": "salvage.all_button",
    "SALVAGE_CONFIRM_BUTTON_X_RATIO / SALVAGE_CONFIRM_BUTTON_Y_RATIO": "salvage.confirm_button",
    "P014": "salvage.stop_finish_click",
}

TODO_NAMING_REVIEW = (
    "SALVAGE_PRE_DECOR_CATEGORY_X_RATIO / SALVAGE_PRE_DECOR_CATEGORY_Y_RATIO",
    "P014",
)

LEGACY_COORDINATE_SETTINGS = {
    "game_search.window_x_ratio": ("picker.window_anchor", "x_ratio"),
    "game_search.window_y_ratio": ("picker.window_anchor", "y_ratio"),
    "game_search.click_x_ratio": ("picker.search_field", "x_ratio"),
    "game_search.click_y_ratio": ("picker.search_field", "y_ratio"),
    "game_actions.open_card_x_ratio": ("market.open_card", "x_ratio"),
    "game_actions.open_card_y_ratio": ("market.open_card", "y_ratio"),
    "game_actions.buy_button_x_ratio": ("market.buy_button", "x_ratio"),
    "game_actions.buy_button_y_ratio": ("market.buy_button", "y_ratio"),
    "game_actions.order_button_x_ratio": ("market.order_button", "x_ratio"),
    "game_actions.order_button_y_ratio": ("market.order_button", "y_ratio"),
    "game_actions.quantity_plus_x_ratio": ("market.quantity_plus", "x_ratio"),
    "game_actions.quantity_plus_y_ratio": ("market.quantity_plus", "y_ratio"),
    "game_actions.quantity_minus_x_ratio": ("market.quantity_minus", "x_ratio"),
    "game_actions.quantity_minus_y_ratio": ("market.quantity_minus", "y_ratio"),
    "game_actions.market_tab_x_ratio": ("market.market_tab", "x_ratio"),
    "game_actions.market_tab_y_ratio": ("market.market_tab", "y_ratio"),
    "game_actions.details_tab_x_ratio": ("market.details_tab", "x_ratio"),
    "game_actions.details_tab_y_ratio": ("market.details_tab", "y_ratio"),
    "game_actions.sell_button_x_ratio": ("market.sell_button", "x_ratio"),
    "game_actions.sell_button_y_ratio": ("market.sell_button", "y_ratio"),
    "game_actions.sell_price_click_x_ratio": ("market.sell_price_field", "x_ratio"),
    "game_actions.sell_price_click_y_ratio": ("market.sell_price_field", "y_ratio"),
    "game_actions.sell_all_button_x_ratio": ("market.sell_all_button", "x_ratio"),
    "game_actions.sell_all_button_y_ratio": ("market.sell_all_button", "y_ratio"),
    "game_actions.sell_confirm_button_x_ratio": ("market.sell_confirm_button", "x_ratio"),
    "game_actions.sell_confirm_button_y_ratio": ("market.sell_confirm_button", "y_ratio"),
    "game_actions.salvage_storage_tab_x_ratio": ("salvage.storage_tab", "x_ratio"),
    "game_actions.salvage_storage_tab_y_ratio": ("salvage.storage_tab", "y_ratio"),
    "game_actions.salvage_details_tab_x_ratio": ("salvage.details_tab", "x_ratio"),
    "game_actions.salvage_details_tab_y_ratio": ("salvage.details_tab", "y_ratio"),
    "game_actions.salvage_pre_decor_category_x_ratio": ("salvage.pre_decor_category", "x_ratio"),
    "game_actions.salvage_pre_decor_category_y_ratio": ("salvage.pre_decor_category", "y_ratio"),
    "game_actions.salvage_decor_category_x_ratio": ("salvage.decor_category", "x_ratio"),
    "game_actions.salvage_decor_category_y_ratio": ("salvage.decor_category", "y_ratio"),
    "game_actions.salvage_sort_dropdown_x_ratio": ("salvage.sort_dropdown", "x_ratio"),
    "game_actions.salvage_sort_dropdown_y_ratio": ("salvage.sort_dropdown", "y_ratio"),
    "game_actions.salvage_sort_new_option_x_ratio": ("salvage.sort_new_option", "x_ratio"),
    "game_actions.salvage_sort_new_option_y_ratio": ("salvage.sort_new_option", "y_ratio"),
    "game_actions.salvage_sort_type_option_x_ratio": ("salvage.sort_type_option", "x_ratio"),
    "game_actions.salvage_sort_type_option_y_ratio": ("salvage.sort_type_option", "y_ratio"),
    "game_actions.salvage_first_item_x_ratio": ("salvage.first_item", "x_ratio"),
    "game_actions.salvage_first_item_y_ratio": ("salvage.first_item", "y_ratio"),
    "game_actions.salvage_select_item_x_ratio": ("salvage.selected_item", "x_ratio"),
    "game_actions.salvage_select_item_y_ratio": ("salvage.selected_item", "y_ratio"),
    "game_actions.salvage_context_disassemble_x_ratio": (
        "salvage.context_disassemble",
        "x_ratio",
    ),
    "game_actions.salvage_context_disassemble_y_ratio": (
        "salvage.context_disassemble",
        "y_ratio",
    ),
    "game_actions.salvage_all_button_x_ratio": ("salvage.all_button", "x_ratio"),
    "game_actions.salvage_all_button_y_ratio": ("salvage.all_button", "y_ratio"),
    "game_actions.salvage_confirm_button_x_ratio": ("salvage.confirm_button", "x_ratio"),
    "game_actions.salvage_confirm_button_y_ratio": ("salvage.confirm_button", "y_ratio"),
}


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _point_ratio_pair(point):
    if not isinstance(point, dict):
        return None

    x_ratio = _number(point.get("x_ratio"))
    y_ratio = _number(point.get("y_ratio"))
    if x_ratio is not None and y_ratio is not None:
        return x_ratio, y_ratio

    x = _number(point.get("x", point.get("x_pixel")))
    y = _number(point.get("y", point.get("y_pixel")))
    base_width = _number(point.get("base_width", DEFAULT_PIXEL_BASE_WIDTH))
    base_height = _number(point.get("base_height", DEFAULT_PIXEL_BASE_HEIGHT))
    if (
        x is None
        or y is None
        or base_width is None
        or base_height is None
        or base_width <= 0
        or base_height <= 0
    ):
        return None

    return x / base_width, y / base_height


def _format_pixel_value(value):
    number = float(value)
    if number.is_integer():
        return int(number)
    return number


def _normalized_point(value, default):
    ratio_pair = _point_ratio_pair(value)
    if ratio_pair is None:
        return None

    description = str(value.get("description", default.get("description", "")))

    has_x_ratio = _number(value.get("x_ratio")) is not None
    has_y_ratio = _number(value.get("y_ratio")) is not None
    if has_x_ratio and has_y_ratio:
        return {
            "x_ratio": float(value["x_ratio"]),
            "y_ratio": float(value["y_ratio"]),
            "description": description,
        }

    x = _number(value.get("x", value.get("x_pixel")))
    y = _number(value.get("y", value.get("y_pixel")))
    base_width = _number(value.get("base_width", DEFAULT_PIXEL_BASE_WIDTH))
    base_height = _number(value.get("base_height", DEFAULT_PIXEL_BASE_HEIGHT))
    point = {
        "x": _format_pixel_value(x),
        "y": _format_pixel_value(y),
        "description": description,
    }
    if "base_width" in value:
        point["base_width"] = _format_pixel_value(base_width)
    if "base_height" in value:
        point["base_height"] = _format_pixel_value(base_height)
    return point


def merge_coordinates(defaults, overrides):
    result = deepcopy(defaults)
    if not isinstance(overrides, dict):
        return result

    for name, override in overrides.items():
        default = result.get(name, {})
        point = _normalized_point(override, default)
        if point is None:
            continue

        result[name] = point

    return result


def load_coordinates(path, defaults=DEFAULT_COORDINATES):
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as coordinates_file:
                return merge_coordinates(defaults, json.load(coordinates_file))

        with path.open("w", encoding="utf-8") as coordinates_file:
            json.dump(defaults, coordinates_file, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return deepcopy(defaults)


def _nested_value(data, path):
    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _load_json(path):
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as json_file:
                value = json.load(json_file)
                return value if isinstance(value, dict) else {}
    except Exception:
        pass
    return {}


def apply_legacy_coordinate_settings(coordinates, settings_path):
    settings = _load_json(settings_path)
    result = deepcopy(coordinates)

    for legacy_path, (point_name, axis) in LEGACY_COORDINATE_SETTINGS.items():
        value = _nested_value(settings, legacy_path)
        if value is None:
            continue

        try:
            result.setdefault(
                point_name,
                deepcopy(DEFAULT_COORDINATES.get(point_name, {})),
            )[axis] = float(value)
        except Exception:
            continue

    return result


def coordinate_pair(coordinates, name):
    point = coordinates.get(name) or DEFAULT_COORDINATES[name]
    ratio_pair = _point_ratio_pair(point)
    if ratio_pair is not None:
        return ratio_pair

    return _point_ratio_pair(DEFAULT_COORDINATES[name])


def coordinate_screen_point(coordinates, name):
    point = coordinates.get(name) or DEFAULT_COORDINATES[name]
    x = _number(point.get("x", point.get("x_pixel")))
    y = _number(point.get("y", point.get("y_pixel")))
    if x is not None and y is not None:
        return round(x), round(y)

    x_ratio, y_ratio = coordinate_pair(coordinates, name)
    return (
        round(DEFAULT_PIXEL_BASE_WIDTH * x_ratio),
        round(DEFAULT_PIXEL_BASE_HEIGHT * y_ratio),
    )
