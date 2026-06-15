import json
from copy import deepcopy


DEFAULT_COORDINATES = {
    "picker.window_anchor": {
        "x_ratio": 0.292,
        "y_ratio": 0.147,
        "description": "Picker window anchor near the in-game search area.",
    },
    "picker.search_field": {
        "x_ratio": 0.245,
        "y_ratio": 0.17,
        "description": "Click point inside the in-game search field.",
    },
    "market.open_card": {
        "x_ratio": 0.54,
        "y_ratio": 0.281,
        "description": "Open the selected market item card.",
    },
    "market.buy_button": {
        "x_ratio": 0.069,
        "y_ratio": 0.904,
        "description": "Buy button on a market item card.",
    },
    "market.order_button": {
        "x_ratio": 0.515,
        "y_ratio": 0.653,
        "description": "Create order button in the market quantity dialog.",
    },
    "market.quantity_plus": {
        "x_ratio": 0.523,
        "y_ratio": 0.512,
        "description": "Increase market order quantity.",
    },
    "market.quantity_minus": {
        "x_ratio": 0.469,
        "y_ratio": 0.512,
        "description": "Decrease market order quantity.",
    },
    "market.market_tab": {
        "x_ratio": 0.383,
        "y_ratio": 0.033,
        "description": "Market tab in the item details view.",
    },
    "market.details_tab": {
        "x_ratio": 0.421,
        "y_ratio": 0.088,
        "description": "Details tab in the market view.",
    },
    "market.sell_button": {
        "x_ratio": 0.36692708333333335,
        "y_ratio": 0.9069444444444444,
        "description": "Sell button on the market item screen.",
    },
    "market.sell_price_field": {
        "x_ratio": 0.4947916666666667,
        "y_ratio": 0.3763888888888889,
        "description": "Price field in the sell dialog.",
    },
    "market.sell_all_button": {
        "x_ratio": 0.5776041666666667,
        "y_ratio": 0.5509259259259259,
        "description": "All quantity button in the sell dialog.",
    },
    "market.sell_confirm_button": {
        "x_ratio": 0.5174479166666667,
        "y_ratio": 0.6944444444444444,
        "description": "Confirm button in the sell dialog.",
    },
    "salvage.storage_tab": {
        "x_ratio": 0.43072916666666666,
        "y_ratio": 0.03657407407407407,
        "description": "Storage tab before salvage actions.",
    },
    "salvage.details_tab": {
        "x_ratio": 0.32708333333333334,
        "y_ratio": 0.0837962962962963,
        "description": "Details tab before salvage actions.",
    },
    "salvage.pre_decor_category": {
        "x_ratio": 0.4239583333333333,
        "y_ratio": 0.1685185185185185,
        "description": "TODO_NAMING_REVIEW: preliminary click before selecting decor category.",
    },
    "salvage.decor_category": {
        "x_ratio": 0.34140625,
        "y_ratio": 0.1685185185185185,
        "description": "Decor category in storage.",
    },
    "salvage.sort_dropdown": {
        "x_ratio": 0.8903645833333333,
        "y_ratio": 0.1699074074074074,
        "description": "Sort dropdown in storage.",
    },
    "salvage.sort_new_option": {
        "x_ratio": 0.8765625,
        "y_ratio": 0.4351851851851852,
        "description": "Sort by newest option.",
    },
    "salvage.sort_type_option": {
        "x_ratio": 0.8778645833333334,
        "y_ratio": 0.2152777777777778,
        "description": "Sort by type option.",
    },
    "salvage.first_item": {
        "x_ratio": 0.06692708333333333,
        "y_ratio": 0.3199074074074074,
        "description": "First salvageable item in the storage list.",
    },
    "salvage.selected_item": {
        "x_ratio": 0.06692708333333333,
        "y_ratio": 0.3199074074074074,
        "description": "Selected salvage item in the storage list.",
    },
    "salvage.context_disassemble": {
        "x_ratio": 0.059895833333333336,
        "y_ratio": 0.6064814814814815,
        "description": "Disassemble action in the item context menu.",
    },
    "salvage.all_button": {
        "x_ratio": 0.5036458333333333,
        "y_ratio": 0.47175925925925927,
        "description": "All button in the disassemble dialog.",
    },
    "salvage.confirm_button": {
        "x_ratio": 0.5002604166666667,
        "y_ratio": 0.6800925925925926,
        "description": "Confirm button in the disassemble dialog.",
    },
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
}

TODO_NAMING_REVIEW = (
    "SALVAGE_PRE_DECOR_CATEGORY_X_RATIO / SALVAGE_PRE_DECOR_CATEGORY_Y_RATIO",
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


def _valid_point(value):
    return (
        isinstance(value, dict)
        and isinstance(value.get("x_ratio"), (int, float))
        and isinstance(value.get("y_ratio"), (int, float))
    )


def merge_coordinates(defaults, overrides):
    result = deepcopy(defaults)
    if not isinstance(overrides, dict):
        return result

    for name, override in overrides.items():
        default = result.get(name, {})
        if not _valid_point(override):
            continue

        result[name] = {
            "x_ratio": float(override["x_ratio"]),
            "y_ratio": float(override["y_ratio"]),
            "description": str(
                override.get("description", default.get("description", ""))
            ),
        }

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
    return float(point["x_ratio"]), float(point["y_ratio"])
