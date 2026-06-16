import ctypes
import math
import time
import tkinter as tk

from timer_app.winapi import SWP_NOACTIVATE
from timer_app.windows import (
    apply_no_focus_clickthrough,
    geometry_from_rect,
    get_window_hwnd,
    show_tk_window_no_activate,
)


def calculate_alert_pulse(pattern):
    cycle = sum(duration for _, duration, _ in pattern)
    position = time.monotonic() % cycle

    for mode, duration, peak in pattern:
        if position < duration:
            if duration <= 0:
                return peak

            progress = position / duration
            eased = progress * progress * (3 - 2 * progress)
            if mode == "rise":
                return peak * eased
            if mode == "fall":
                return peak * (1 - eased)
            return peak

        position -= duration

    return 0


def get_pulse_alpha(min_alpha, max_alpha, pulse):
    pulse = max(0, min(1, pulse))
    return min_alpha + (max_alpha - min_alpha) * pulse


def configure_task_manager_app(root, app_id):
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

    try:
        apply_no_focus_clickthrough(root, show_in_task_manager=False)
    except Exception:
        pass


def show_overlay_window(root):
    show_tk_window_no_activate(root)


def apply_window_region(root):
    pass


def create_monitor_alert_window(
    root,
    monitor_rect,
    title,
    transparent_color,
    border_color,
    alpha,
    border_thickness,
    log_error_callback,
    log_context,
    log_message,
):
    left, top, right, bottom = monitor_rect
    width = right - left
    height = bottom - top
    scale = max(1.0, root.winfo_fpixels("1i") / 96)
    thickness = round(border_thickness * scale)

    alert_window = tk.Toplevel(root)
    alert_window.withdraw()
    alert_window.title(title)
    alert_window.overrideredirect(True)
    alert_window.configure(bg=transparent_color)
    alert_window.attributes("-transparentcolor", transparent_color)
    alert_window.attributes("-topmost", True)
    alert_window.attributes("-alpha", alpha)
    alert_window.geometry(geometry_from_rect(monitor_rect))

    alert_canvas = tk.Canvas(
        alert_window,
        width=width,
        height=height,
        bg=transparent_color,
        highlightthickness=0,
        bd=0,
    )
    alert_canvas.pack(fill="both", expand=True)
    border_items = create_monitor_border_items(
        alert_canvas,
        width,
        height,
        thickness,
        border_color,
    )
    alert_window.update_idletasks()

    try:
        apply_no_focus_clickthrough(alert_window)
        hwnd = get_window_hwnd(alert_window)
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            -1,
            left,
            top,
            width,
            height,
            SWP_NOACTIVATE,
        )
    except Exception as error:
        log_error_callback(log_context, f"{log_message}: {error}")

    return alert_window, alert_canvas, border_items


def create_monitor_border_items(canvas, width, height, thickness, color):
    return [
        canvas.create_rectangle(
            0,
            0,
            width,
            thickness,
            fill=color,
            outline="",
        ),
        canvas.create_rectangle(
            0,
            height - thickness,
            width,
            height,
            fill=color,
            outline="",
        ),
        canvas.create_rectangle(
            0,
            thickness,
            thickness,
            height - thickness,
            fill=color,
            outline="",
        ),
        canvas.create_rectangle(
            width - thickness,
            thickness,
            width,
            height - thickness,
            fill=color,
            outline="",
        ),
    ]


def configure_notch_dpi_sizes(
    root,
    canvas,
    base_notch_width,
    base_notch_height,
    base_notch_radius,
    base_font_pixels,
):
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(root.winfo_id())
    except Exception:
        try:
            dpi = ctypes.windll.user32.GetDpiForSystem()
        except Exception:
            dpi = root.winfo_fpixels("1i")

    scale = max(1.0, dpi / 96)
    notch_width = round(base_notch_width * scale)
    notch_height = round(base_notch_height * scale)
    notch_radius = round(base_notch_radius * scale)
    font_pixels = round(base_font_pixels * scale)
    overlay_width = root.winfo_screenwidth()
    notch_x = (overlay_width - notch_width) // 2
    canvas.config(width=overlay_width, height=notch_height)

    return overlay_width, notch_x, notch_width, notch_height, notch_radius, font_pixels


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


def create_notch_items(
    canvas,
    overlay_width,
    notch_x,
    notch_width,
    notch_height,
    notch_radius,
    alert_bg,
    normal_bg,
    normal_fg,
    font_pixels,
):
    alert_strip = canvas.create_rectangle(
        0,
        0,
        overlay_width,
        notch_height,
        fill=alert_bg,
        outline="",
        state="hidden",
    )
    notch_item = canvas.create_polygon(
        rounded_bottom_rect_points(
            notch_x,
            0,
            notch_width,
            notch_height,
            notch_radius,
        ),
        fill=normal_bg,
        outline="",
    )
    timer_text = canvas.create_text(
        notch_x + notch_width // 2,
        notch_height // 2,
        text="--:--",
        fill=normal_fg,
        font=("Segoe UI", -font_pixels),
    )

    return alert_strip, [notch_item], timer_text


def set_canvas_items_fill(canvas, items, color):
    for item in items:
        canvas.itemconfig(item, fill=color)
