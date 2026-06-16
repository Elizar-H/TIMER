import ctypes
import queue
import threading

from timer_app.winapi import (
    MSG,
    VK_DELETE,
    VK_DOWN,
    VK_END,
    VK_LEFT,
    VK_RIGHT,
    VK_UP,
    WM_APP_HOTKEY_COMMAND,
    WM_HOTKEY,
)


PICKER_HOTKEY_ID = 7311
PICKER_OPEN_END_HOTKEY_ID = 7316
PICKER_HOTKEY_VK = 0xC0
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


class HotkeyWorker:
    def __init__(self, log_error):
        self._events = queue.Queue()
        self._commands = queue.Queue()
        self._log_error = log_error
        self._thread_id = None
        self._picker_navigation_registered = False

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def drain_events(self):
        while not self._events.empty():
            yield self._events.get()

    def set_picker_navigation(self, enabled):
        command = "register_picker_nav" if enabled else "unregister_picker_nav"
        self._commands.put(command)
        self._wake()

    def _wake(self):
        if self._thread_id:
            try:
                ctypes.windll.user32.PostThreadMessageW(
                    self._thread_id,
                    WM_APP_HOTKEY_COMMAND,
                    0,
                    0,
                )
            except Exception:
                pass

    def _process_commands(self):
        while not self._commands.empty():
            command = self._commands.get()

            if command == "register_picker_nav" and not self._picker_navigation_registered:
                registered_ids = []
                for hotkey_id, vk, _event_name in PICKER_ACTION_HOTKEYS:
                    if ctypes.windll.user32.RegisterHotKey(None, hotkey_id, 0, vk):
                        registered_ids.append(hotkey_id)
                    else:
                        break

                self._picker_navigation_registered = len(registered_ids) == len(
                    PICKER_ACTION_HOTKEYS
                )
                if not self._picker_navigation_registered:
                    for hotkey_id in registered_ids:
                        ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
                    self._log_error(
                        "picker_nav_hotkey",
                        "RegisterHotKey failed for picker action keys",
                    )

            elif command == "unregister_picker_nav" and self._picker_navigation_registered:
                for hotkey_id, _vk, _event_name in PICKER_ACTION_HOTKEYS:
                    ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
                self._picker_navigation_registered = False

    def _register_base_hotkeys(self):
        if not ctypes.windll.user32.RegisterHotKey(
            None,
            PICKER_HOTKEY_ID,
            0,
            PICKER_HOTKEY_VK,
        ):
            self._log_error("hotkey", "RegisterHotKey failed for ё / `")
            return False
        if not ctypes.windll.user32.RegisterHotKey(
            None,
            PICKER_OPEN_END_HOTKEY_ID,
            0,
            VK_END,
        ):
            self._log_error("hotkey", "RegisterHotKey failed for End")
        if not ctypes.windll.user32.RegisterHotKey(
            None,
            SALVAGE_HOTKEY_ID,
            0,
            VK_DELETE,
        ):
            self._log_error("hotkey", "RegisterHotKey failed for Delete")

        return True

    def _emit_hotkey_event(self, hotkey_id):
        if hotkey_id == PICKER_HOTKEY_ID:
            self._events.put("picker")
        elif hotkey_id == PICKER_OPEN_END_HOTKEY_ID:
            self._events.put("picker_end_open")
        elif hotkey_id == SALVAGE_HOTKEY_ID:
            self._events.put("salvage_toggle")
        else:
            for picker_hotkey_id, _vk, event_name in PICKER_ACTION_HOTKEYS:
                if hotkey_id == picker_hotkey_id:
                    self._events.put(event_name)
                    break

    def _run(self):
        try:
            self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
            if not self._register_base_hotkeys():
                return

            msg = MSG()
            while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_APP_HOTKEY_COMMAND:
                    self._process_commands()
                elif msg.message == WM_HOTKEY:
                    self._emit_hotkey_event(msg.wParam)
        except Exception as e:
            self._log_error("hotkey", f"Hotkey worker failed: {e}")
