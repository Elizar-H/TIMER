"""
Быстрый безопасный live-тестер только левой колонки «Запросы на продажу».

Что делает:
- снимает НЕ весь 4K экран, а только маленький блок продаж:
  x1=60, y1=1460, x2=892, y2=1712;
- проверяет строки снизу вверх: 4 → 3 → 2 → 1;
- как только нашёл валидную пару цена + количество, сразу останавливается;
- печатает выбранную строку, цену и количество;
- сохраняет маленький скрин блока и debug-картинки.

Чего НЕ делает:
- не нажимает клавиши;
- не кликает мышью;
- не использует clipboard;
- не нажимает Esc;
- не делает покупку.

Рядом должны лежать:
- market_digit_lab_pure_white.py
- окно с товаром.png
- digit_samples.json, если ты его используешь.
"""

from __future__ import annotations

import argparse
import ctypes
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageGrab
except ImportError as exc:
    raise SystemExit(
        "Не найден Pillow. Установи его командой:\n"
        "py -m pip install pillow"
    ) from exc

try:
    import market_digit_lab_pure_white as digit_lab
except ImportError as exc:
    raise SystemExit(
        "Рядом с этим файлом должен лежать market_digit_lab_pure_white.py.\n"
        f"Подробности: {exc}"
    ) from exc


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = SCRIPT_DIR / "market_sell_reader_fast_output"

# Абсолютная зона только левой колонки «Запросы на продажу».
SELL_BLOCK_BOX = (60, 1460, 892, 1712)  # x1, y1, x2, y2
SELL_BLOCK_W = SELL_BLOCK_BOX[2] - SELL_BLOCK_BOX[0]
SELL_BLOCK_H = SELL_BLOCK_BOX[3] - SELL_BLOCK_BOX[1]

# Относительные ROI внутри SELL_BLOCK_BOX.
# Эти значения получены из твоих исходных зон:
# price x: 60..360  -> 0..300
# qty   x: 785..892 -> 725..832
# row y: 1460..1520 -> 0..60, и далее +64.
ROW_RELATIVE_BOXES = {
    1: {"price": (0, 0, 300, 60), "qty": (725, 0, 832, 60)},
    2: {"price": (0, 64, 300, 124), "qty": (725, 64, 832, 124)},
    3: {"price": (0, 128, 300, 188), "qty": (725, 128, 832, 188)},
    4: {"price": (0, 192, 300, 252), "qty": (725, 192, 832, 252)},
}

# Для автоматики лучше требовать почти идеальное совпадение.
# У тебя pure-white режим сейчас даёт 1.000, поэтому 0.999 — нормальный строгий порог.
MIN_REQUIRED_SCORE = 0.999


@dataclass
class ReadField:
    raw: str
    digits: str
    value: int | None
    score: float
    status: str


@dataclass
class SelectedOffer:
    row: int
    price_digits: str
    price_cents: int
    qty: int
    price_score: float
    qty_score: float


def set_dpi_aware() -> None:
    """Чтобы Windows не подменял координаты при масштабировании дисплея."""
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def grab_sell_block() -> Image.Image:
    """Снимает только блок продаж, а не весь экран."""
    return ImageGrab.grab(bbox=SELL_BLOCK_BOX).convert("RGB")


def read_field(crop: Image.Image, kind: str, templates: dict[str, list[Image.Image]]) -> ReadField:
    recognition = digit_lab.recognize_field(crop, templates)
    raw = digit_lab.format_for_display(kind, recognition.digits)
    score = min(recognition.confidences, default=0.0)

    if not recognition.digits:
        return ReadField(raw="<пусто>", digits="", value=None, score=0.0, status="EMPTY")

    if "?" in recognition.digits or not recognition.digits.isdigit():
        return ReadField(raw=raw, digits=recognition.digits, value=None, score=score, status="UNKNOWN")

    if score < MIN_REQUIRED_SCORE:
        return ReadField(raw=raw, digits=recognition.digits, value=int(recognition.digits), score=score, status="LOW_SCORE")

    value = int(recognition.digits)
    if value <= 0:
        return ReadField(raw=raw, digits=recognition.digits, value=None, score=score, status="ZERO")

    return ReadField(raw=raw, digits=recognition.digits, value=value, score=score, status="READ")


def save_field_debug(
    block: Image.Image,
    row: int,
    price_crop: Image.Image,
    qty_crop: Image.Image,
    price: ReadField,
    qty: ReadField,
    debug_dir: Path,
) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    price_crop.save(debug_dir / f"row_{row}_price_original.png")
    qty_crop.save(debug_dir / f"row_{row}_qty_original.png")

    # Маски для быстрой визуальной проверки.
    for name, crop in ((f"row_{row}_price", price_crop), (f"row_{row}_qty", qty_crop)):
        mask = digit_lab.make_white_mask(crop)
        mask_image = Image.new("L", crop.size, 0)
        px = mask_image.load()
        for y, mask_row in enumerate(mask):
            for x, on in enumerate(mask_row):
                if on:
                    px[x, y] = 255
        mask_image.resize((crop.width * 4, crop.height * 4), Image.Resampling.NEAREST).save(
            debug_dir / f"{name}_mask_x4.png"
        )

    # Общая картинка блока с рамкой проверенной строки.
    annotated = block.copy()
    draw = ImageDraw.Draw(annotated)
    font = ImageFont.load_default()

    price_box = ROW_RELATIVE_BOXES[row]["price"]
    qty_box = ROW_RELATIVE_BOXES[row]["qty"]
    for box, label in (
        (price_box, f"row {row} price: {price.raw} {price.status} {price.score:.3f}"),
        (qty_box, f"row {row} qty: {qty.raw} {qty.status} {qty.score:.3f}"),
    ):
        draw.rectangle(box, outline="lime", width=2)
        draw.text((box[0], max(0, box[1] - 12)), label, fill="lime", font=font)

    annotated.resize((annotated.width * 2, annotated.height * 2), Image.Resampling.NEAREST).save(
        debug_dir / f"row_{row}_annotated_block_x2.png"
    )


def find_last_valid_sell_offer(
    block: Image.Image,
    templates: dict[str, list[Image.Image]],
    debug_dir: Path | None = None,
) -> tuple[SelectedOffer | None, list[str]]:
    """Проверяет строки 4→1 и останавливается на первой валидной паре."""
    log_lines: list[str] = []

    for row in (4, 3, 2, 1):
        price_box = ROW_RELATIVE_BOXES[row]["price"]
        qty_box = ROW_RELATIVE_BOXES[row]["qty"]

        price_crop = block.crop(price_box)
        qty_crop = block.crop(qty_box)

        price = read_field(price_crop, "price", templates)
        qty = read_field(qty_crop, "qty", templates)

        log_lines.append(
            f"строка {row}: price={price.raw} ({price.status}, {price.score:.3f}), "
            f"qty={qty.raw} ({qty.status}, {qty.score:.3f})"
        )

        if debug_dir is not None:
            save_field_debug(block, row, price_crop, qty_crop, price, qty, debug_dir)

        if price.status == "READ" and qty.status == "READ" and price.value is not None and qty.value is not None:
            return (
                SelectedOffer(
                    row=row,
                    price_digits=price.digits,
                    price_cents=price.value,
                    qty=qty.value,
                    price_score=price.score,
                    qty_score=qty.score,
                ),
                log_lines,
            )

    return None, log_lines


def format_price_from_cents(price_cents: int) -> str:
    whole, cents = divmod(price_cents, 100)
    return f"{whole},{cents:02d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Быстро читает только последнюю непустую строку продаж снизу вверх. Ничего не нажимает."
    )
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Не сохранять маски и annotated-картинки строк.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    set_dpi_aware()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = OUTPUT_ROOT / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    print("Строю шаблоны чисто белых цифр...")
    try:
        reference_path = digit_lab.DEFAULT_REFERENCE
        if not reference_path.exists():
            print(f"Не найден эталонный скрин: {reference_path}")
            return 2

        reference = Image.open(reference_path).convert("RGB")
        templates = digit_lab.build_templates(reference, run_dir)
    except Exception as exc:
        print(f"Не удалось построить шаблоны: {exc}")
        return 3

    print(f"Снимаю только зону продаж: {SELL_BLOCK_BOX} ({SELL_BLOCK_W}×{SELL_BLOCK_H})")
    try:
        block = grab_sell_block()
    except Exception as exc:
        print(f"Не удалось снять зону продаж: {exc}")
        return 4

    block_path = run_dir / "sell_block.png"
    block.save(block_path)

    if block.size != (SELL_BLOCK_W, SELL_BLOCK_H):
        print(f"Остановлено: размер блока {block.size}, ожидалось {(SELL_BLOCK_W, SELL_BLOCK_H)}")
        print(f"Сохранено для проверки: {block_path}")
        return 5

    print("Проверяю строки снизу вверх: 4 → 3 → 2 → 1")
    debug_dir = None if args.no_debug else (run_dir / "debug")
    selected, checked_lines = find_last_valid_sell_offer(block, templates, debug_dir)

    print("\nПроверенные строки:")
    for line in checked_lines:
        print("  " + line)

    print("\nИтог:")
    if selected is None:
        print("  Валидная строка продаж не найдена.")
    else:
        print(
            f"  Взята строка {selected.row}: "
            f"цена {format_price_from_cents(selected.price_cents)}, "
            f"количество {selected.qty}, "
            f"scores price={selected.price_score:.3f}, qty={selected.qty_score:.3f}"
        )

    print(f"\nПапка результата: {run_dir}")
    print(f"Скрин маленького блока: {block_path}")
    if debug_dir is not None:
        print(f"Debug: {debug_dir}")
    print("\nСкрипт ничего не нажимает: только читает экран.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
