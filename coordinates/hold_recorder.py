# hold_recorder.py

import time
import json
import ctypes
from pathlib import Path

from pynput import mouse, keyboard

try:
    import pyperclip
except ImportError:
    pyperclip = None


# Чтобы координаты совпадали с реальными пикселями Windows
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


OUT_JSON = Path("holds.json")
OUT_PY = Path("holds.py")

holds = []

ctrl_pressed = False
hold_start_time = None
hold_start_pos = None


def load_holds():
    global holds

    if OUT_JSON.exists():
        try:
            holds = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        except Exception:
            holds = []


def save_holds():
    OUT_JSON.write_text(
        json.dumps(holds, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )

    lines = [
        "# Автоматически созданный файл удержаний",
        "# Формат: NAME = (x, y, seconds)",
        "",
    ]

    for h in holds:
        lines.append(f'{h["name"]} = ({h["x"]}, {h["y"]}, {h["duration"]})')

    OUT_PY.write_text("\n".join(lines), encoding="utf-8")


def copy_to_clipboard(text):
    if pyperclip:
        pyperclip.copy(text)


def add_hold(x, y, duration):
    name = f"HOLD_{len(holds) + 1:03d}"
    duration = round(duration, 3)

    item = {
        "name": name,
        "x": int(x),
        "y": int(y),
        "duration": duration,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    holds.append(item)
    save_holds()

    text = f"{name} = ({int(x)}, {int(y)}, {duration})"
    copy_to_clipboard(text)

    print(f"Записано удержание: {text}")


def reset_holds():
    global holds

    holds = []
    save_holds()

    print("Все удержания сброшены.")


def is_ctrl_key(key):
    return key in (
        keyboard.Key.ctrl,
        keyboard.Key.ctrl_l,
        keyboard.Key.ctrl_r,
    )


def on_key_press(key):
    global ctrl_pressed

    if is_ctrl_key(key):
        ctrl_pressed = True

    # Ctrl + R — сброс всех удержаний
    try:
        if ctrl_pressed and key.char.lower() == "r":
            reset_holds()
    except AttributeError:
        pass


def on_key_release(key):
    global ctrl_pressed

    if is_ctrl_key(key):
        ctrl_pressed = False


def on_mouse_click(x, y, button, pressed):
    global hold_start_time, hold_start_pos

    if button != mouse.Button.left:
        return

    # Ctrl + зажатие ЛКМ — начало записи удержания
    if pressed and ctrl_pressed:
        hold_start_time = time.perf_counter()
        hold_start_pos = (x, y)

        print(f"Начало удержания: ({int(x)}, {int(y)})")

    # Отпустил ЛКМ — конец записи
    elif not pressed:
        if hold_start_time is None or hold_start_pos is None:
            return

        duration = time.perf_counter() - hold_start_time
        start_x, start_y = hold_start_pos

        add_hold(start_x, start_y, duration)

        hold_start_time = None
        hold_start_pos = None


def main():
    load_holds()

    print("Сборщик удержаний запущен.")
    print()
    print("Ctrl + зажать ЛКМ — начать замер удержания")
    print("Отпустить ЛКМ    — закончить замер и записать")
    print("Ctrl + R         — сбросить все удержания")
    print("Ctrl + C в терминале — выйти")
    print()
    print("Файлы:")
    print("holds.json — полный список")
    print("holds.py   — готовые переменные для кода")
    print()

    keyboard_listener = keyboard.Listener(
        on_press=on_key_press,
        on_release=on_key_release
    )

    mouse_listener = mouse.Listener(
        on_click=on_mouse_click
    )

    keyboard_listener.start()
    mouse_listener.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Выход...")
    finally:
        keyboard_listener.stop()
        mouse_listener.stop()


if __name__ == "__main__":
    main()