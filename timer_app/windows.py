import ctypes
from ctypes import wintypes
from pathlib import Path
import time

from timer_app.log import log_error
from timer_app.winapi import (
    GWL_EXSTYLE,
    MONITORINFO,
    MONITORINFOF_PRIMARY,
    PROCESS_QUERY_LIMITED_INFORMATION,
    SWP_FRAMECHANGED,
    SWP_NOACTIVATE,
    SWP_NOMOVE,
    SWP_NOSIZE,
    SWP_SHOWWINDOW,
    SW_MINIMIZE,
    SW_RESTORE,
    SW_SHOW,
    SW_SHOWNOACTIVATE,
    WS_EX_APPWINDOW,
    WS_EX_NOACTIVATE,
    WS_EX_TOOLWINDOW,
    WS_EX_TRANSPARENT,
)


GAME_WINDOW_KEYWORDS = ("crossout",)


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


def is_live_game_window(hwnd):
    return is_live_window(hwnd) and is_game_window(hwnd)


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


def minimize_window(hwnd):
    if not hwnd:
        return False

    try:
        ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
        return True
    except Exception as e:
        log_error("game_window", f"Minimize failed: {e}")
        return False


def get_hwnd_rect(hwnd):
    if not hwnd:
        return None

    rect = wintypes.RECT()
    if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None

    return rect.left, rect.top, rect.right, rect.bottom


def get_hwnd_ratio_point(hwnd, x_ratio, y_ratio):
    rect = get_hwnd_rect(hwnd)
    if rect is None:
        return None

    left, top, right, bottom = rect
    width = max(1, right - left)
    height = max(1, bottom - top)
    return left + round(width * x_ratio), top + round(height * y_ratio)


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


def is_window_on_primary_monitor(hwnd, primary_monitor_rect=None):
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


def is_foreground_on_primary_monitor(primary_monitor_rect=None):
    return is_window_on_primary_monitor(get_foreground_hwnd(), primary_monitor_rect)


def get_window_hwnd(window):
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


def get_second_monitor_rect(alert_monitor_index):
    monitors = get_monitor_rects()

    if alert_monitor_index is not None:
        for monitor in monitors:
            if monitor["index"] == alert_monitor_index:
                return monitor["rect"]

        log_error(
            "monitor",
            f"Configured monitor {alert_monitor_index} was not found. "
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
