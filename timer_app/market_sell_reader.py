from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import time

from timer_app.paths import APP_ROOT


PURE_WHITE_RGB = (255, 255, 255)
MIN_COMPONENT_AREA = 10
MIN_REQUIRED_SCORE = 0.999
NORM_W = 28
NORM_H = 42
NORM_PAD = 2
SELL_BLOCK_BOX = (60, 1460, 892, 1712)
SELL_BLOCK_W = SELL_BLOCK_BOX[2] - SELL_BLOCK_BOX[0]
SELL_BLOCK_H = SELL_BLOCK_BOX[3] - SELL_BLOCK_BOX[1]
TEMPLATE_DIR = APP_ROOT / "Tools" / "digit_templates_pure_white"

ROW_RELATIVE_BOXES = {
    1: {"price": (0, 0, 300, 60), "qty": (725, 0, 832, 60)},
    2: {"price": (0, 64, 300, 124), "qty": (725, 64, 832, 124)},
    3: {"price": (0, 128, 300, 188), "qty": (725, 128, 832, 188)},
    4: {"price": (0, 192, 300, 252), "qty": (725, 192, 832, 252)},
}

_templates_cache = None


@dataclass
class Component:
    x: int
    y: int
    w: int
    h: int
    area: int
    pixels: set[tuple[int, int]]


@dataclass
class Recognition:
    digits: str
    confidences: list[float]


@dataclass
class ReadField:
    digits: str
    value: int | None
    score: float
    status: str


@dataclass
class SelectedOffer:
    row: int
    price_cents: int
    qty: int
    price_score: float
    qty_score: float


def _require_pillow():
    try:
        from PIL import Image, ImageGrab
    except ImportError as exc:
        raise RuntimeError("Pillow is required for market safe-buy reading") from exc

    return Image, ImageGrab


def load_digit_templates(template_dir: Path = TEMPLATE_DIR):
    global _templates_cache

    if _templates_cache is not None:
        return _templates_cache

    Image, _ImageGrab = _require_pillow()
    templates = {}
    for digit in "0123456789":
        digit_dir = template_dir / digit
        paths = sorted(digit_dir.glob("*_normalized_x6.png"))
        if not paths:
            raise RuntimeError(f"Missing digit templates for {digit}: {digit_dir}")

        examples = []
        for path in paths:
            with Image.open(path) as template_file:
                template = template_file.convert("L")
                if template.size != (NORM_W, NORM_H):
                    template = template.resize(
                        (NORM_W, NORM_H),
                        Image.Resampling.NEAREST,
                    )
                examples.append(template.copy())
        templates[digit] = examples

    _templates_cache = templates
    return templates


def grab_sell_block():
    _Image, ImageGrab = _require_pillow()
    return ImageGrab.grab(bbox=SELL_BLOCK_BOX).convert("RGB")


def make_white_mask(image) -> list[list[bool]]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    px = rgb.load()
    pure_r, pure_g, pure_b = PURE_WHITE_RGB
    return [
        [
            px[x, y] == (pure_r, pure_g, pure_b)
            for x in range(width)
        ]
        for y in range(height)
    ]


def connected_components(mask: list[list[bool]]) -> list[Component]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    result = []

    for start_y in range(height):
        for start_x in range(width):
            if not mask[start_y][start_x] or seen[start_y][start_x]:
                continue

            queue = deque([(start_x, start_y)])
            seen[start_y][start_x] = True
            pixels = set()
            min_x = max_x = start_x
            min_y = max_y = start_y

            while queue:
                x, y = queue.popleft()
                pixels.add((x, y))
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

                for next_x, next_y in (
                    (x + 1, y),
                    (x - 1, y),
                    (x, y + 1),
                    (x, y - 1),
                ):
                    if (
                        0 <= next_x < width
                        and 0 <= next_y < height
                        and mask[next_y][next_x]
                        and not seen[next_y][next_x]
                    ):
                        seen[next_y][next_x] = True
                        queue.append((next_x, next_y))

            area = len(pixels)
            if area >= MIN_COMPONENT_AREA:
                result.append(
                    Component(
                        x=min_x,
                        y=min_y,
                        w=max_x - min_x + 1,
                        h=max_y - min_y + 1,
                        area=area,
                        pixels=pixels,
                    )
                )

    return sorted(result, key=lambda component: (component.x, component.y))


def is_decimal_comma(component: Component, components: list[Component]) -> bool:
    digit_heights = [item.h for item in components if item.h >= 20]
    typical_digit_height = max(digit_heights, default=0)
    return (
        typical_digit_height > 0
        and component.h <= typical_digit_height * 0.55
        and component.y > typical_digit_height * 0.45
    )


def component_to_image(component: Component):
    Image, _ImageGrab = _require_pillow()
    out = Image.new("L", (component.w, component.h), 0)
    out_px = out.load()
    for x, y in component.pixels:
        out_px[x - component.x, y - component.y] = 255
    return out


def normalize_symbol(component: Component):
    Image, _ImageGrab = _require_pillow()
    glyph = component_to_image(component)
    inner_w = NORM_W - 2 * NORM_PAD
    inner_h = NORM_H - 2 * NORM_PAD
    scale = min(inner_w / glyph.width, inner_h / glyph.height)
    new_w = max(1, round(glyph.width * scale))
    new_h = max(1, round(glyph.height * scale))
    glyph = glyph.resize((new_w, new_h), Image.Resampling.NEAREST)

    out = Image.new("L", (NORM_W, NORM_H), 0)
    paste_x = (NORM_W - new_w) // 2
    paste_y = (NORM_H - new_h) // 2
    out.paste(glyph, (paste_x, paste_y))
    return out


def iou_score(left, right) -> float:
    intersection = 0
    union = 0
    for left_value, right_value in zip(left.getdata(), right.getdata()):
        left_on = left_value >= 128
        right_on = right_value >= 128
        if left_on and right_on:
            intersection += 1
        if left_on or right_on:
            union += 1
    return intersection / union if union else 0.0


def classify_digit(component: Component, templates) -> tuple[str, float]:
    normalized = normalize_symbol(component)
    best_digit = "?"
    best_score = -1.0
    for digit, examples in templates.items():
        score = max(iou_score(normalized, example) for example in examples)
        if score > best_score:
            best_score = score
            best_digit = digit
    return best_digit, best_score


def recognize_field(crop, templates) -> Recognition:
    components = connected_components(make_white_mask(crop))
    digits = []
    confidences = []

    for component in components:
        if is_decimal_comma(component, components):
            continue

        digit, score = classify_digit(component, templates)
        digits.append(digit)
        confidences.append(score)

    return Recognition(digits="".join(digits), confidences=confidences)


def read_field(crop, templates) -> ReadField:
    recognition = recognize_field(crop, templates)
    score = min(recognition.confidences, default=0.0)

    if not recognition.digits:
        return ReadField(digits="", value=None, score=0.0, status="EMPTY")

    if "?" in recognition.digits or not recognition.digits.isdigit():
        return ReadField(
            digits=recognition.digits,
            value=None,
            score=score,
            status="UNKNOWN",
        )

    value = int(recognition.digits)
    if score < MIN_REQUIRED_SCORE:
        return ReadField(
            digits=recognition.digits,
            value=value,
            score=score,
            status="LOW_SCORE",
        )

    if value <= 0:
        return ReadField(
            digits=recognition.digits,
            value=None,
            score=score,
            status="ZERO",
        )

    return ReadField(
        digits=recognition.digits,
        value=value,
        score=score,
        status="READ",
    )


def find_last_valid_sell_offer(block, templates) -> SelectedOffer | None:
    for row in (4, 3, 2, 1):
        price_crop = block.crop(ROW_RELATIVE_BOXES[row]["price"])
        qty_crop = block.crop(ROW_RELATIVE_BOXES[row]["qty"])

        price = read_field(price_crop, templates)
        qty = read_field(qty_crop, templates)
        if (
            price.status == "READ"
            and qty.status == "READ"
            and price.value is not None
            and qty.value is not None
        ):
            return SelectedOffer(
                row=row,
                price_cents=price.value,
                qty=qty.value,
                price_score=price.score,
                qty_score=qty.score,
            )

    return None


def read_sell_offer_once() -> SelectedOffer | None:
    templates = load_digit_templates()
    block = grab_sell_block()
    if block.size != (SELL_BLOCK_W, SELL_BLOCK_H):
        raise RuntimeError(
            f"Unexpected sell block size {block.size}, expected "
            f"{(SELL_BLOCK_W, SELL_BLOCK_H)}"
        )
    return find_last_valid_sell_offer(block, templates)


def wait_for_valid_sell_offer(
    timeout_seconds: float,
    poll_seconds: float,
) -> SelectedOffer | None:
    deadline = time.monotonic() + max(0.0, timeout_seconds)

    while True:
        selected = read_sell_offer_once()
        if selected is not None:
            return selected

        if time.monotonic() >= deadline:
            return None

        time.sleep(max(0.0, poll_seconds))


def format_price_from_cents(price_cents: int) -> str:
    whole, cents = divmod(price_cents, 100)
    return f"{whole},{cents:02d}"
