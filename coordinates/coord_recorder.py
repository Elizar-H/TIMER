# coord_recorder.py

import json
import time
import ctypes
import queue
from pathlib import Path
import tkinter as tk

import pyautogui
from pynput import keyboard, mouse

try:
    import pyperclip
except ImportError:
    pyperclip = None


# Чтобы координаты совпадали с реальными пикселями Windows
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


OUT_JSON = Path("coords.json")
OUT_PY = Path("coords.py")

points = []
click_capture_enabled = False
dots_visible = True
running = True

ui_queue = queue.Queue()


# Данные виртуального экрана, чтобы лучше работало с несколькими мониторами
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

user32 = ctypes.windll.user32

VIRTUAL_X = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
VIRTUAL_Y = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
VIRTUAL_W = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
VIRTUAL_H = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)


def load_points():
    global points

    if OUT_JSON.exists():
        try:
            points = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        except Exception:
            points = []


def save_points():
    OUT_JSON.write_text(
        json.dumps(points, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )

    lines = [
        "# Автоматически созданный файл с координатами",
        "# Формат: NAME = (x, y)",
        "",
    ]

    for p in points:
        lines.append(f'{p["name"]} = ({p["x"]}, {p["y"]})')

    OUT_PY.write_text("\n".join(lines), encoding="utf-8")


def copy_to_clipboard(text):
    if pyperclip:
        pyperclip.copy(text)


def add_point(x, y, source="hotkey"):
    name = f"P{len(points) + 1:03d}"

    point = {
        "name": name,
        "x": int(x),
        "y": int(y),
        "source": source,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    points.append(point)
    save_points()

    text = f"{name} = ({int(x)}, {int(y)})"
    copy_to_clipboard(text)

    print(f"Записано: {text}")

    ui_queue.put(("redraw", None))


def reset_points():
    global points

    points = []
    save_points()

    print("Все координаты сброшены.")
    ui_queue.put(("redraw", None))


def record_current_position():
    x, y = pyautogui.position()
    add_point(x, y, source="hotkey")


def toggle_click_capture():
    global click_capture_enabled

    click_capture_enabled = not click_capture_enabled

    if click_capture_enabled:
        print("Режим записи по колёсику мыши: ВКЛ")
        print("Нажимай колёсико мыши, чтобы записывать координаты.")
    else:
        print("Режим записи по колёсику мыши: ВЫКЛ")


def toggle_dots_visible():
    global dots_visible

    dots_visible = not dots_visible

    if dots_visible:
        print("Красные точки: ВКЛ")
    else:
        print("Красные точки: ВЫКЛ")

    ui_queue.put(("redraw", None))


def stop_program():
    global running

    running = False
    print("Выход...")
    ui_queue.put(("exit", None))


def on_mouse_click(x, y, button, pressed):
    if not pressed:
        return

    if click_capture_enabled and button == mouse.Button.middle:
        add_point(x, y, source="middle_click")


def make_window_click_through(root):
    """
    Делает окно с точками прозрачным для кликов.
    То есть ты видишь красные точки, но мышка кликает сквозь них.
    Работает на Windows.
    """
    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())

        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOPMOST = 0x00000008
        WS_EX_TOOLWINDOW = 0x00000080

        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_TOOLWINDOW

        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    except Exception as e:
        print(f"Не удалось сделать окно прозрачным для кликов: {e}")


def create_overlay():
    root = tk.Tk()

    root.overrideredirect(True)
    root.attributes("-topmost", True)

    # Цвет, который станет полностью прозрачным
    transparent_color = "white"
    root.configure(bg=transparent_color)
    root.attributes("-transparentcolor", transparent_color)

    geometry = f"{VIRTUAL_W}x{VIRTUAL_H}{VIRTUAL_X:+d}{VIRTUAL_Y:+d}"
    root.geometry(geometry)

    canvas = tk.Canvas(
        root,
        width=VIRTUAL_W,
        height=VIRTUAL_H,
        bg=transparent_color,
        highlightthickness=0
    )
    canvas.pack(fill="both", expand=True)

    root.update()
    make_window_click_through(root)

    return root, canvas


def redraw_points(canvas):
    canvas.delete("all")

    if not dots_visible:
        return

    for p in points:
        x = p["x"] - VIRTUAL_X
        y = p["y"] - VIRTUAL_Y

        r = 6

        canvas.create_oval(
            x - r,
            y - r,
            x + r,
            y + r,
            fill="red",
            outline="black",
            width=1
        )

        canvas.create_text(
            x + 18,
            y - 10,
            text=p["name"],
            fill="red",
            anchor="w",
            font=("Arial", 10, "bold")
        )


def process_ui_queue(root, canvas):
    global running

    while not ui_queue.empty():
        command, data = ui_queue.get()

        if command == "redraw":
            redraw_points(canvas)

        elif command == "exit":
            root.destroy()
            return

    if running:
        root.after(50, process_ui_queue, root, canvas)


def print_help():
    print("Сборщик координат запущен.")
    print()
    print("Ctrl + Alt + C  — записать текущую позицию мыши")
    print("Ctrl + Alt + M  — включить/выключить запись по колёсику мыши")
    print("Ctrl + Alt + R  — сбросить все координаты")
    print("Ctrl + Alt + H  — скрыть/показать красные точки")
    print("Ctrl + Alt + Q  — выйти")
    print()
    print("Файлы:")
    print("coords.json — полный список")
    print("coords.py   — координаты для вставки в код")
    print()


def main():
    load_points()
    print_help()

    root, canvas = create_overlay()
    redraw_points(canvas)

    hotkeys = keyboard.GlobalHotKeys({
        "<ctrl>+<alt>+c": record_current_position,
        "<ctrl>+<alt>+m": toggle_click_capture,
        "<ctrl>+<alt>+r": reset_points,
        "<ctrl>+<alt>+h": toggle_dots_visible,
        "<ctrl>+<alt>+q": stop_program,
    })

    mouse_listener = mouse.Listener(on_click=on_mouse_click)

    hotkeys.start()
    mouse_listener.start()

    root.after(50, process_ui_queue, root, canvas)

    try:
        root.mainloop()
    finally:
        hotkeys.stop()
        mouse_listener.stop()


if __name__ == "__main__":
    main()