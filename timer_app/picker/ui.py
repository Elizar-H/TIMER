"""Small canvas primitives used by the Picker UI."""


def fit_canvas_text(text, font, max_width):
    text = "" if text is None else str(text)
    if font.measure(text) <= max_width:
        return text

    ellipsis = "..."
    max_width = max(0, max_width - font.measure(ellipsis))
    while text and font.measure(text) > max_width:
        text = text[:-1]
    return text + ellipsis if text else ellipsis


def draw_rounded_rect(canvas, x1, y1, x2, y2, radius, fill, outline=""):
    if canvas is None:
        return

    radius = max(1, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    canvas.create_rectangle(
        x1 + radius,
        y1,
        x2 - radius,
        y2,
        fill=fill,
        outline=outline,
    )
    canvas.create_rectangle(
        x1,
        y1 + radius,
        x2,
        y2 - radius,
        fill=fill,
        outline=outline,
    )
    canvas.create_oval(
        x1,
        y1,
        x1 + radius * 2,
        y1 + radius * 2,
        fill=fill,
        outline=outline,
    )
    canvas.create_oval(
        x2 - radius * 2,
        y1,
        x2,
        y1 + radius * 2,
        fill=fill,
        outline=outline,
    )
    canvas.create_oval(
        x1,
        y2 - radius * 2,
        x1 + radius * 2,
        y2,
        fill=fill,
        outline=outline,
    )
    canvas.create_oval(
        x2 - radius * 2,
        y2 - radius * 2,
        x2,
        y2,
        fill=fill,
        outline=outline,
    )


def draw_rounded_outline(
    canvas,
    x1,
    y1,
    x2,
    y2,
    radius,
    color,
    width=1,
):
    if canvas is None:
        return

    radius = max(1, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    canvas.create_line(
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        fill=color,
        width=width,
    )
    canvas.create_line(
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        fill=color,
        width=width,
    )
    canvas.create_line(
        x1 + radius,
        y2,
        x2 - radius,
        y2,
        fill=color,
        width=width,
    )
    canvas.create_line(
        x1,
        y1 + radius,
        x1,
        y2 - radius,
        fill=color,
        width=width,
    )
    canvas.create_arc(
        x1,
        y1,
        x1 + radius * 2,
        y1 + radius * 2,
        start=90,
        extent=90,
        style="arc",
        outline=color,
        width=width,
    )
    canvas.create_arc(
        x2 - radius * 2,
        y1,
        x2,
        y1 + radius * 2,
        start=0,
        extent=90,
        style="arc",
        outline=color,
        width=width,
    )
    canvas.create_arc(
        x2 - radius * 2,
        y2 - radius * 2,
        x2,
        y2,
        start=270,
        extent=90,
        style="arc",
        outline=color,
        width=width,
    )
    canvas.create_arc(
        x1,
        y2 - radius * 2,
        x1 + radius * 2,
        y2,
        start=180,
        extent=90,
        style="arc",
        outline=color,
        width=width,
    )


def draw_cell(
    canvas,
    x,
    y,
    width,
    height,
    text,
    font,
    fg="#dfe7f3",
    bg="#101418",
    anchor="e",
    padx=7,
):
    if canvas is None:
        return

    canvas.create_rectangle(
        x,
        y,
        x + width,
        y + height,
        fill=bg,
        outline="#0d1115",
        width=1,
    )

    if anchor == "center":
        text_x = x + width / 2
        text_anchor = "center"
        max_width = width - padx * 2
    elif anchor == "w":
        text_x = x + padx
        text_anchor = "w"
        max_width = width - padx * 2
    else:
        text_x = x + width - padx
        text_anchor = "e"
        max_width = width - padx * 2

    canvas.create_text(
        text_x,
        y + height / 2,
        text=fit_canvas_text(text, font, max_width),
        fill=fg,
        anchor=text_anchor,
        font=font,
    )


def get_hover_background(kind, key, default_bg):
    if key == "history_sell":
        return "#e1aa3f"
    if kind == "flash" and key in ("sell", "buy"):
        return "#18bfd8"
    if kind == "flash" and key == "roi":
        return "#88d47e"
    if kind == "flash" and key == "profit":
        return "#f6d847"
    return "#16202a" if default_bg == "#101418" else default_bg
