from dataclasses import dataclass
import re


@dataclass
class PickerPasteState:
    """Last paste marker and paste request captured after a refresh."""

    last_at: float = 0
    last_name: str | None = None
    refresh_name: str | None = None
    refresh_row_index: int | None = None

    def remember(self, name, now):
        self.last_at = now
        self.last_name = name

    def clear_refresh(self):
        self.refresh_name = None
        self.refresh_row_index = None

    def queue_refresh(self, name, row_index):
        self.refresh_name = name
        self.refresh_row_index = row_index


def normalize_game_search_text(text):
    return re.sub(r"[\u00a0\u202f\u2007]+", " ", str(text)).strip()


def get_picker_item_match_name(name):
    """Returns the existing normalized, case-sensitive Picker match name."""
    if not name:
        return None

    match_name = normalize_game_search_text(name)
    return match_name or None


def get_selected_picker_item_name(rows, selected_row_index):
    """Returns the selected item name for a valid Picker item row."""
    if selected_row_index is None:
        return None
    if selected_row_index < 0 or selected_row_index >= len(rows):
        return None

    row = rows[selected_row_index]
    item = row.get("item")
    if row.get("type") != "item" or not item:
        return None

    return item.get("name")


def find_picker_row_by_item_name(rows, item_name):
    """Returns the first Picker item row with the same normalized name."""
    match_name = get_picker_item_match_name(item_name)
    if not match_name:
        return None

    for row_index, row in enumerate(rows):
        item = row.get("item")
        if row.get("type") != "item" or not item:
            continue

        if get_picker_item_match_name(item.get("name")) == match_name:
            return row_index

    return None


def run_picker_action_when_ready(ensure_market_ready, ready_action):
    """Runs a Picker continuation after its single market-readiness callback."""
    if not ensure_market_ready():
        return False
    ready_action()
    return True
