# AGENTS.md

## Project

This is a local Python desktop automation project for Crossout-related timer, picker, market and salvage workflows.

The program is currently being refactored from a large `timer.py` into a modular monolith.

Main priorities:

* do not break existing behavior;
* keep the project understandable for a non-expert human;
* make future features easy to add;
* avoid overengineering.

## Coding style

Follow PEP 8 and Google Python Style Guide naming conventions:

* modules and files: `lower_snake_case.py`;
* functions and variables: `lower_snake_case`;
* classes: `CapitalizedWords`;
* real constants only: `ALL_CAPS`.

Avoid unclear abbreviations and huge technical variable names when a human-readable name is possible.

Bad examples:

* `GAME_SELL_CONFIRM_BUTTON_X_RATIO`
* `SALVAGE_POST_MENU_CLICK_DELAY_SECONDS`
* `PICKER_GAME_SEARCH_CLICK_X_RATIO`

Good examples:

* `market.sell_confirm_button`
* `delay_after_menu_click`
* `search_field_click_point`

## Architecture

Use a modular monolith.

The project is one application, but code should be split by responsibility:

* `timer_app/app.py` — application startup and orchestration
* `timer_app/config.py` — settings loading and defaults
* `timer_app/paths.py` — project paths
* `timer_app/log.py` — logging
* `timer_app/winapi.py` — low-level WinAPI helpers
* `timer_app/windows.py` — game window and monitor helpers
* `timer_app/crossout.py` — CrossoutCore HTTP/parsing/economics
* `timer_app/coordinates.py` — coordinate loading/saving/resolving
* `timer_app/game.py` — high-level game actions by named points
* `timer_app/hotkeys.py` — hotkeys and polling
* `timer_app/overlays.py` — overlays/notch
* `timer_app/picker/` — picker cache, data, UI and paste logic
* `timer_app/actions/` — market/salvage/navigation action flows

Do not introduce DI containers, abstract factories, plugin systems or unnecessary patterns.

## Coordinates

Coordinates must be treated as data, not hardcoded logic.

Prefer named points:

```python
game.click("market.open_card")
game.click("market.buy_button")
game.hold("salvage.confirm_button", seconds=...)
game.right_click("salvage.first_item")
```

Do not add new direct usages of raw coordinate pairs like:

```python
click_game_ratio(x_ratio, y_ratio)
```

`coordinates.json` should contain named points with:

* `x_ratio`
* `y_ratio`
* `description`

Example:

```json
{
  "market.sell_confirm_button": {
    "x_ratio": 0.5174479166666667,
    "y_ratio": 0.6944444444444444,
    "description": "Confirm sell button"
  }
}
```

When renaming old coordinate variables, keep a mapping:

```text
OLD_NAME_X_RATIO / OLD_NAME_Y_RATIO -> new.named_point
```

If a point name is unclear, add it to `TODO_NAMING_REVIEW` instead of guessing.

## Compatibility

Preserve old behavior unless explicitly asked otherwise.

Do not change:

* hotkey IDs;
* VK codes;
* delays and timings;
* URLs;
* parser behavior;
* market/salvage algorithms;
* UI behavior;
* existing coordinate numeric values.

`timer.py` should remain a compatibility wrapper if possible.
`main.py` should be the preferred new entry point.

## Git safety

Never delete, move or rewrite `.git`.

Before major refactors:

* check `git status`;
* warn if there are uncommitted changes;
* work in small stages.

Do not continue to the next stage without user approval if the user asked for staged work.

## Checks

After Python changes, run a syntax check:

```powershell
py -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('.').rglob('*.py')]; print('syntax ok')"
```

After JSON changes, validate JSON:

```powershell
py -m json.tool settings.json
py -m json.tool coordinates.json
```

If a check fails, stop and explain what failed.
