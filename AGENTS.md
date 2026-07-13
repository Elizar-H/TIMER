# AGENTS.md

## Purpose and priorities

TIMER is a Windows-only Python desktop automation application for Crossout. It
contains timer, Picker, market, safe-purchase, order-waiting, salvage, hotkey,
notification, and overlay workflows. The project is maintained as a modular
monolith and is intended to remain understandable to a non-expert Python
developer.

Apply these priorities in order:

1. Follow the user's explicit request and its stated scope.
2. Preserve observable behavior and the user's data.
3. Keep the current working tree safe, including uncommitted and staged work.
4. Improve clarity, reliability, testability, and performance only where the
   behavior-preserving case is well supported.
5. Prefer a small, complete change over a broad speculative rewrite.

The current working directory, including its uncommitted changes and existing
user files, is the behavioral baseline. Do not assume that `HEAD` is the source
of truth. Communicate with the user in the language they use.

Do not launch `main.py`, `timer.py`, or any workflow that can send real mouse or
keyboard input unless the user explicitly asks for a live run. Import checks and
mocked tests are not authorization to interact with the game.

## Before making changes

For every non-trivial task:

1. Read this file completely.
2. Run `git status --short --branch` and distinguish staged, unstaged, and
   untracked files. When ignored files are relevant to the task, inspect them
   separately with `git status --short --ignored` or `git check-ignore`.
   Treat all pre-existing files and changes as user-owned.
3. Read the relevant modules, their callers, nearby tests, and any task-specific
   plan or documentation that actually exists. Do not recreate a deliberately
   deleted plan merely because an older instruction mentioned it.
4. Find the applicable entry points, shared state, worker threads, locks,
   `Event` objects, and `root.after` callbacks before changing a workflow.
5. Write down or characterize the observable invariants when the behavior is not
   already covered by tests.
6. Work in small logical stages and keep the project syntactically valid and
   importable after each stage.

If an intended cleanup might alter a click trace, timing, state transition,
thread ownership, or UI behavior, do not make it without explicit approval.
Document the risky location instead.

## Entry points and compatibility

- `main.py` is the preferred application entry point.
- `timer.py` is a compatibility entry point and must continue to work.
- Both wrappers delegate to `timer_app.app.main`.
- `timer_settings.py` is a compatibility surface for settings helpers and
  exports. Preserve existing imports from it.
- Importing a module must not start the GUI, register live hotkeys, start worker
  threads, or send input. Be aware that configuration code can read or create
  default files when those files are absent; isolate such checks in temporary
  directories when needed.

Do not break documented compatibility exports or late-bound callbacks that are
part of an active extraction seam. Internal module-level names may be changed as
part of a coordinated behavior-preserving extraction, with their local tests
updated to exercise the new boundary instead of freezing the old structure.

## Architecture and responsibility map

Keep the application a straightforward modular monolith:

- `timer_app/app.py` — composition root, Tk application orchestration, component
  binding, worker startup, and adapters between legacy callbacks and modules.
- `timer_app/config.py` — settings defaults, loading, merging, and persistence.
- `timer_app/paths.py` — project and data-file paths.
- `timer_app/log.py` — application logging.
- `timer_app/coordinates.py` — coordinate loading, validation, normalization,
  saving, and screen-point resolution.
- `timer_app/game.py` — high-level game actions using named coordinates.
- `timer_app/winapi.py` — low-level Windows API calls and input primitives.
- `timer_app/windows.py` — game-window, monitor, focus, and geometry helpers.
- `timer_app/clipboard.py` — low-level Win32 clipboard reads and writes;
  workflow-level restoration remains with the caller.
- `timer_app/hotkeys.py` — hotkey registration, the Windows message loop, and
  Picker input state. Polling coordination remains in `app.py` and uses the
  low-level key-state helper from `winapi.py`.
- `timer_app/timer.py` — timer state and timer-related logic.
- `timer_app/overlays.py` — overlays, notch, and notification presentation.
- `timer_app/crossout.py` — CrossoutCore HTTP access, parsing, filtering, and
  economic calculations.
- `timer_app/market_sell_reader.py` — OCR-based market price reading.
- `timer_app/picker/data.py` — Picker data refresh, selection state, and service
  logic.
- `timer_app/picker/cache.py` — Picker cache schema, validation, loading, and
  persistence.
- `timer_app/picker/items.py` — pure Picker row formatting and item presentation
  helpers.
- `timer_app/picker/paste.py` — Picker paste/search readiness and related state.
- `timer_app/picker/ui.py` — Picker canvas and UI primitives.
- `timer_app/actions/market.py` — market navigation, safe-purchase, order-waiting,
  and market workflow state.
- `timer_app/actions/salvage.py` — salvage workflow, state, and decisions.

Architecture rules:

- `timer_app.app` is the composition root. Extracted modules must not import it.
- Keep low-level WinAPI details out of UI and workflow modules when an existing
  helper already owns them.
- Keep Tk widget construction and drawing separate from pure parsing,
  calculations, and workflow decisions when a small extraction is sufficient.
- Pass narrow callbacks, values, or simple state objects across module
  boundaries. Do not introduce a dependency-injection container, plugin system,
  abstract factory hierarchy, service locator, or framework-style event bus.
- Do not split code into many files containing only trivial wrappers. A module
  should own a coherent responsibility.
- Do not replace the working thread/Tk model with `asyncio` merely for
  architectural uniformity.

## Behavior-preservation contract

Unless the user explicitly asks for a behavior change, do not change any of the
following:

- user-visible features or supported workflows;
- market, safe-purchase, order-waiting, salvage, Picker, timer, overlay, or
  notification algorithms;
- hotkey IDs, VK codes, registration flags, polling rules, or the handling of
  key presses, holds, repeats, and releases;
- the exact order and number of clicks, key presses, `Esc` presses, waits,
  clipboard operations, focus changes, and window switches;
- coordinate names, coordinate values, coordinate interpretation, or fallback
  behavior;
- delays, timeouts, polling intervals, hold durations, debounce windows, or
  `root.after` delays;
- URLs, request parameters, parser behavior, OCR thresholds/templates, price
  calculations, filters, rounding, or economic formulas;
- window sizes, positions, geometry, colors, fonts, table layout, topmost or
  click-through behavior, and notification/overlay lifetime;
- the schemas or compatibility semantics of `settings.json`,
  `coordinates.json`, and cache files;
- compatibility with existing settings, coordinate files, caches, `main.py`,
  `timer.py`, and `timer_settings.py`.

Performance work must remove unnecessary Python work, duplicate conversions, or
provably redundant calls. It must not make automation appear faster by reducing
stability delays or polling intervals.

Do not fix a suspected logical bug, race, dead transition, or unusual recovery
path as an incidental refactor. First capture current behavior and ask for a
separate behavior-changing task when necessary.

## Coordinates

Coordinates are data. New workflow code must use existing named points through
high-level helpers such as:

```python
game.click("market.open_card")
game.right_click("salvage.first_item")
game.hold("salvage.confirm_button", seconds=hold_seconds)
point = game.pixel_point("market.buy_button")
```

Do not add raw coordinate pairs or new direct ratio-based clicks inside workflow
logic when a named point can be used.

The canonical entries currently stored in `coordinates.json` use reference-pixel
`x` and `y` coordinates, which the coordinate subsystem resolves for the target
window or screen:

```json
{
  "market.open_card": {
    "x": 100,
    "y": 200,
    "description": "Open the selected market card"
  }
}
```

`timer_app.coordinates` also accepts legacy/alternate `x_ratio` and `y_ratio`
input. That compatibility does not authorize migrating the current file or
rewriting all entries. Preserve optional `base_width` and `base_height` fields
and all legacy fallbacks.

Never alter numeric coordinate values as part of a refactor. When an explicitly
requested rename is necessary, retain a clear mapping from every old constant or
point name to the new named point. If a point's purpose is unclear, record it for
naming review or ask the user; do not guess.

## State, threads, Tk, and WinAPI

Concurrency behavior is part of the application's observable behavior:

- Use a small class or `dataclass` only when it groups one coherent state and
  makes ownership clearer. Do not duplicate the same flag in globals and an
  object.
- Preserve lock type, acquisition/release ownership, critical-section scope,
  and failure cleanup. Some existing workflow locks are intentionally acquired
  in one function and released by a worker; do not casually replace them with a
  context manager or change `Lock` to `RLock`.
- Do not hold a lock across sleeps, UI callbacks, WinAPI calls, or game actions
  unless the existing workflow already depends on that exact scope.
- Preserve `Event` generation and cancellation semantics. A pending Picker token
  or row selection is state, not automatically a worker-cancellation mechanism.
- Preserve whether a thread is daemonized, when it is created, and whether
  duplicate starts are rejected. Do not add a thread pool or queue without a
  demonstrated need and behavior tests.
- Preserve `root.after` delays, callback order, cancellation behavior, and the
  distinction between immediate and deferred work.
- New Tk widget mutations should occur on the Tk/UI thread. Do not silently
  redesign legacy cross-thread behavior during an unrelated refactor.
- Keep blocking HTTP, OCR, polling, sleeps, and game automation out of the UI
  thread unless moving them would change established sequencing and has not yet
  been characterized.
- Clipboard contents, foreground window, focus, cursor/button state, and held
  keys must be restored or released in the same circumstances as before.
- Release device contexts, opened handles, clipboard access, mouse-down events,
  and key-down events according to their WinAPI ownership contract, normally in
  `finally` blocks. Do not close borrowed HWND values returned by lookup APIs.
- Cache only stable data or values valid for one atomic probe. Do not reuse a
  foreground HWND, live geometry, or pixel result across polling iterations
  without proof that invalidation preserves behavior.

Avoid broad concurrency improvements that change shutdown behavior,
single-flight rules, cancellation, or error recovery unless they are the stated
task.

## Data files, runtime files, and assets

- `settings.json` and `coordinates.json` are tracked user/runtime data. Preserve
  their format, values, ordering where practical, defaults, and auto-creation
  behavior. Tests must not overwrite the real files.
- `timer_items_cache.json` and `timer.log` are ignored runtime files. Preserve
  the cache schema, version handling, timestamps, and compatibility behavior.
- `tests/` is intentionally ignored in this checkout and contains local helper
  and characterization tests. It may be run and minimally extended, but do not
  delete it, force-add it, or treat its ignored status as accidental.
- `Tools/digit_templates_pure_white/` contains tracked OCR templates. Do not
  rename, regenerate, relocate, or normalize those assets without an explicit
  OCR task and live validation.
- Keep text files UTF-8. Avoid mechanical JSON reformatting or key reordering
  when no data-format change was requested.

The application has Windows-specific runtime behavior and may load optional
third-party packages, such as Pillow, only in the feature that needs them. Do not
add a dependency or packaging system solely to support a refactor or lint run.

## Errors and logging

- Narrow `except Exception` only when the complete set of expected exceptions
  and the required cleanup behavior are known. Broad catches at workflow,
  WinAPI, shutdown, and best-effort UI boundaries can be intentional.
- Never lose cleanup while making exception handling more precise.
- Do not silently swallow newly introduced failures. Use the existing logging
  helpers for important worker and workflow errors, while avoiding recursive
  logging failures or noisy messages inside fast polling loops.
- Preserve return values, fallback paths, retry counts, and user notifications
  on errors.
- Do not restructure a game algorithm solely to make it easier to mock. Prefer
  small boundary patches or characterization tests.

## Code style

Follow PEP 8 and Google-style naming conventions:

- modules, functions, and variables: `lower_snake_case`;
- classes: `CapitalizedWords`;
- real constants only: `ALL_CAPS`.

Prefer readable, domain-level names over abbreviations and overlong names that
encode implementation details. Coordinate data keys such as
`"market.sell_confirm_button"` are domain identifiers and are not Python
constant names.

Keep functions focused, dependencies visible, and control flow straightforward.
Comments should explain why a sequence, delay, compatibility adapter, or unusual
state transition exists; do not restate the code. Avoid clever metaprogramming,
premature generic helpers, and speculative abstractions.

Use `rg` or `rg --files` for repository searches. Use `apply_patch` for manual
file edits. Preserve unrelated formatting and user changes.

## Tests and safe test doubles

Use the existing local tests. Add only the smallest tests directly needed for
the current change:

- prefer pure tests for settings, coordinates, parsing, calculations, caches,
  and Picker row generation;
- use characterization tests for click/key/focus/clipboard sequences that
  cannot run without Crossout;
- patch WinAPI, Tk, HTTP, OCR, clipboard, sleeping, and input boundaries so a
  test cannot interact with the real desktop;
- use temporary directories/files for settings, coordinates, and caches;
- assert the exact action trace when sequencing is critical;
- do not update an expected trace merely to make a changed implementation pass.

Do not build a large test framework, add a GUI automation dependency, or require
Crossout for the normal test suite.

## Git safety

- Never run destructive or state-rewriting commands such as `git reset`,
  `git checkout --`, `git restore`, `git clean`, `git stash`, or an unsolicited
  rebase.
- Never modify, move, or delete `.git`.
- Do not commit, push, force-add ignored files, stage, or unstage changes unless
  the user explicitly requests that exact Git operation.
- Preserve the index. A staged deletion or staged modification is a user change;
  do not restore, restage, or convert it to an unstaged change.
- Preserve untracked and ignored files. Do not overwrite files by copying a
  version from `HEAD` over the working tree.
- Touch only files required by the task. If an existing user edit overlaps the
  requested change and cannot be safely preserved, stop and explain the
  conflict.
- Before and after work, inspect `git status --short --branch`. Review the
  relevant unstaged and staged diffs separately when necessary.

## Required checks

Run checks in proportion to the change. After Python changes, the syntax check is
mandatory:

```powershell
py -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('.').rglob('*.py')]; print('syntax ok')"
```

Validate the user JSON files after changes that can affect configuration or
coordinates, and before handing off a larger refactor:

```powershell
py -m json.tool settings.json
py -m json.tool coordinates.json
```

When `tests/` is present, run the existing suite:

```powershell
py -m unittest discover -s tests -q
```

For a broad module-boundary change, run an import check without starting the
application. The following command imports `timer_app.app`, whose configuration
initialization can create missing settings or coordinate files. Run it only when
both tracked JSON files exist and are intended to remain present; otherwise use
the existing mocked import test, if available, or an isolated temporary copy:

```powershell
py -c "import importlib, pkgutil, timer_app; names = [m.name for m in pkgutil.walk_packages(timer_app.__path__, timer_app.__name__ + '.')] + ['main', 'timer', 'timer_settings']; [importlib.import_module(name) for name in names]; print(f'imports ok: {len(names)} modules')"
```

Also run:

```powershell
git diff --check
```

Do not install a linter, formatter, or other dependency merely to claim an
additional check. If a check fails, stop unrelated edits, determine whether the
failure is caused by the new change, the baseline, or an incorrect invocation,
fix regressions introduced by the work, rerun the relevant checks, and report
anything unresolved accurately.

## What requires manual validation

The following cannot be fully proven by import or mocked unit tests and should
be listed in the handoff when touched:

- locating, focusing, minimizing, restoring, and switching the Crossout window;
- real hotkey registration and press/hold/release behavior;
- the exact live sequence and timing of clicks, keys, `Esc`, waits, and clipboard
  restoration;
- pixel colors, monitor scaling, coordinate resolution, and OCR accuracy at the
  supported resolutions;
- safe-purchase, order-completion, market navigation, Picker paste, and salvage
  flows against the current game UI;
- overlay/notch placement, topmost/click-through behavior, and Tk responsiveness;
- race behavior during rapid repeated hotkeys, cancellation, shutdown, and
  simultaneous background refreshes;
- live CrossoutCore availability and response variations.

Never claim these were verified unless they were actually exercised in the live
environment with the user's authorization.

## Completion and handoff

Leave the project in a runnable state and stop at the requested stage. Report:

1. what was changed and why;
2. which files and responsibilities were affected;
3. which automated checks were run and their results;
4. what still requires manual validation;
5. any risky areas deliberately left unchanged;
6. final `git status --short --branch` and a concise `git diff --stat` when the
   task involved repository changes;
7. confirmation that no commit or push was made unless explicitly requested.

For behavior-preserving refactors, explicitly confirm that user functionality,
algorithms, coordinates, hotkeys/VK codes, timings, UI, and user-file formats
were intentionally left unchanged.
