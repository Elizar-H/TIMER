from collections.abc import Callable
from dataclasses import dataclass
import threading
import time


STAGE_OPEN_CARD = "open_card"
STAGE_OPENING_CARD = "opening_card"
STAGE_BUY = "buy"
STAGE_OPENING_BUY_DIALOG = "opening_buy_dialog"
STAGE_QUANTITY = "quantity"


class OrderCompleteProbeState:
    """Thread lifecycle state for the market order-complete probe."""

    def __init__(self):
        self._running = False
        self._lock = threading.Lock()
        self._done = threading.Event()
        self._done.set()

    def try_begin(self):
        """Marks a new probe as running unless one is already active."""
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._done.clear()
            return True

    def finish(self):
        """Marks the active probe complete and releases its waiters."""
        with self._lock:
            self._running = False
            self._done.set()

    def is_running(self):
        """Returns the running flag under the lifecycle lock."""
        with self._lock:
            return self._running

    def wait(self, timeout):
        """Waits on the shared completion event without changing generations."""
        return self._done.wait(timeout)


@dataclass(frozen=True)
class OrderCompleteProbeDependencies:
    """Application operations used by the market order-complete probe."""

    monotonic: Callable[[], float]
    sleep: Callable[[float], object]
    get_wait_seconds: Callable[[], float]
    get_poll_seconds: Callable[[], float]
    get_escape_repeat_delay_seconds: Callable[[], float]
    find_initial_hwnd: Callable[[], int]
    ensure_focus: Callable[[int], int]
    read_probe: Callable[[], tuple[object, object]]
    is_order_button_held: Callable[[], bool]
    release_held_order_button: Callable[[], object]
    reset_action_stage: Callable[[], object]
    tap_escape: Callable[[], object]
    append_log_line: Callable[[str], object]


def run_order_complete_probe(dependencies):
    """Runs the existing polling and two-escape order-complete sequence."""
    deadline = dependencies.monotonic() + dependencies.get_wait_seconds()
    last_rgb = None
    target_hwnd = dependencies.find_initial_hwnd()
    focus_wait_logged = False

    while dependencies.monotonic() < deadline:
        # The market order is submitted on mouse-up, so do not time out while
        # holding the order button.
        if dependencies.is_order_button_held():
            deadline = (
                dependencies.monotonic()
                + dependencies.get_wait_seconds()
            )

        target_hwnd = dependencies.ensure_focus(target_hwnd)
        if not target_hwnd:
            if not focus_wait_logged:
                dependencies.append_log_line(
                    "market order complete probe: waiting for game focus"
                )
                focus_wait_logged = True
            dependencies.sleep(dependencies.get_poll_seconds())
            continue

        hit_point, rgb = dependencies.read_probe()
        last_rgb = rgb
        if hit_point is not None:
            dependencies.append_log_line(
                f"market order complete: esc at {hit_point} rgb={rgb}"
            )
            if dependencies.is_order_button_held():
                dependencies.release_held_order_button()
            dependencies.reset_action_stage()
            target_hwnd = dependencies.ensure_focus(target_hwnd)
            if not target_hwnd:
                dependencies.append_log_line(
                    "market order complete: esc skipped, game focus unavailable"
                )
                return
            dependencies.tap_escape()
            dependencies.sleep(
                dependencies.get_escape_repeat_delay_seconds()
            )
            dependencies.tap_escape()
            return

        dependencies.sleep(dependencies.get_poll_seconds())

    dependencies.append_log_line(
        f"market order complete probe timeout: last_rgb={last_rgb}"
    )


def matches_market_tab_active_pixel(rgb, target_rgb, tolerance):
    """Returns whether a sampled pixel matches the active market tab."""
    if rgb is None:
        return False

    red, green, blue = rgb
    target_red, target_green, target_blue = target_rgb
    return (
        abs(red - target_red) <= tolerance
        and abs(green - target_green) <= tolerance
        and abs(blue - target_blue) <= tolerance
        and red > green + 45
        and green > blue + 60
    )


def open_market_subtab(
    tab_point_name,
    subtab_name,
    *,
    is_market_view_active,
    click,
    sleep,
    get_section_delay_seconds,
    set_current_subtab,
    reset_action_stage,
):
    """Opens a market subtab using the existing click and reset sequence."""
    if is_market_view_active():
        clicked_market = True
    else:
        clicked_market = click("market.market_tab")
        if not clicked_market:
            return False
        sleep(get_section_delay_seconds())

    clicked_tab = click(tab_point_name)
    if clicked_market or clicked_tab:
        if clicked_tab:
            set_current_subtab(subtab_name)
        reset_action_stage()
    return clicked_market and clicked_tab


def navigate_back_from_market_card(get_action_hwnd, tap_escape):
    """Returns from a market card with the existing best-effort Escape tap."""
    if not get_action_hwnd():
        return False
    tap_escape()
    return True


@dataclass(frozen=True)
class SafeBuyWorkflowConfig:
    """Unchanged timing and key values used by the safe-buy workflow."""

    offer_wait_seconds: float
    offer_poll_seconds: float


@dataclass(frozen=True)
class SafeBuyWorkflowDependencies:
    """Application operations used by the safe-buy workflow."""

    wait_for_offer: Callable[[float, float], object]
    format_price: Callable[[int], str]
    get_clipboard_text: Callable[[], object]
    set_clipboard_text: Callable[[str], bool]
    monotonic_ns: Callable[[], int]
    buy_current_item: Callable[[], bool]
    wait_for_clipboard_price: Callable[[str, object], tuple[object, object]]
    click_quantity_field: Callable[[], bool]
    send_select_all: Callable[[], object]
    send_paste: Callable[[], object]
    wait_before_clipboard_restore: Callable[[], object]
    escape_once: Callable[[str], object]
    escape_four_times: Callable[[str], object]
    append_log_line: Callable[[str], object]
    log_error: Callable[[str, str], object]


def run_safe_buy_workflow(config, dependencies):
    """Runs the existing safe-buy sequence through application callbacks."""
    old_clipboard = None
    old_clipboard_saved = False
    order_window_confirmed = False

    try:
        selected = dependencies.wait_for_offer(
            config.offer_wait_seconds,
            config.offer_poll_seconds,
        )
        if selected is None:
            dependencies.append_log_line(
                "[MARKET_SAFE_BUY] no_valid_sell_offer_before_timeout"
            )
            dependencies.escape_once("no_valid_sell_offer_before_timeout")
            return

        dependencies.append_log_line(
            "[MARKET_SAFE_BUY] selected "
            f"row={selected.row} "
            f"price={dependencies.format_price(selected.price_cents)} "
            f"qty={selected.qty} "
            f"score_price={selected.price_score:.3f} "
            f"score_qty={selected.qty_score:.3f}"
        )

        selected_offer = selected
        old_clipboard = dependencies.get_clipboard_text()
        old_clipboard_saved = old_clipboard is not None
        sentinel = (
            "__MARKET_SAFE_BUY_WAITING_"
            f"{dependencies.monotonic_ns()}__"
        )
        if not dependencies.set_clipboard_text(sentinel):
            dependencies.append_log_line(
                "[MARKET_SAFE_BUY] clipboard_sentinel_set_failed"
            )
            dependencies.escape_once("clipboard_sentinel_set_failed")
            return

        if not dependencies.buy_current_item():
            dependencies.append_log_line("[MARKET_SAFE_BUY] buy_click_failed")
            dependencies.escape_once("buy_click_failed")
            return

        clipboard_text, clipboard_price_cents = (
            dependencies.wait_for_clipboard_price(
                sentinel,
                selected_offer,
            )
        )
        if clipboard_text is None:
            dependencies.append_log_line("[MARKET_SAFE_BUY] clipboard_timeout")
            dependencies.escape_four_times("clipboard_timeout")
            return

        if clipboard_price_cents is None:
            dependencies.append_log_line(
                "[MARKET_SAFE_BUY] clipboard_parse_error "
                f"value={clipboard_text!r}"
            )

        if clipboard_price_cents != selected_offer.price_cents:
            dependencies.append_log_line(
                "[MARKET_SAFE_BUY] price_mismatch "
                f"selected={selected_offer.price_cents} "
                f"clipboard={clipboard_price_cents} raw={clipboard_text!r}"
            )
            dependencies.escape_four_times("price_mismatch")
            return

        order_window_confirmed = True
        qty_text = str(selected_offer.qty)
        if not dependencies.set_clipboard_text(qty_text):
            dependencies.append_log_line(
                "[MARKET_SAFE_BUY] qty_clipboard_verify_error "
                f"expected={qty_text!r} actual=None"
            )
            dependencies.escape_four_times("qty_clipboard_set_failed")
            return

        clipboard_qty = dependencies.get_clipboard_text()
        if clipboard_qty is None or clipboard_qty.strip() != qty_text:
            dependencies.append_log_line(
                "[MARKET_SAFE_BUY] qty_clipboard_verify_error "
                f"expected={qty_text!r} actual={clipboard_qty!r}"
            )
            dependencies.escape_four_times("qty_clipboard_verify_error")
            return

        if not dependencies.click_quantity_field():
            dependencies.append_log_line(
                "[MARKET_SAFE_BUY] quantity_field_click_failed"
            )
            dependencies.escape_four_times("quantity_field_click_failed")
            return

        dependencies.send_select_all()
        dependencies.send_paste()
        dependencies.append_log_line(
            f"[MARKET_SAFE_BUY] qty_pasted qty={qty_text}"
        )
    except Exception as exc:
        dependencies.append_log_line(
            f"[MARKET_SAFE_BUY] unexpected_exception {exc}"
        )
        dependencies.log_error(
            "market_safe_buy",
            f"Safe-buy workflow failed: {exc}",
        )
        if order_window_confirmed:
            dependencies.escape_four_times("unexpected_exception")
        else:
            dependencies.escape_once("unexpected_exception")
    finally:
        if old_clipboard_saved:
            dependencies.wait_before_clipboard_restore()
            dependencies.set_clipboard_text(old_clipboard)


class MarketActionState:
    def __init__(self, max_age_seconds):
        self.max_age_seconds = max_age_seconds
        self.stage = STAGE_OPEN_CARD
        self.ready_at = 0
        self.updated_at = 0

    def set(self, stage, ready_at=0):
        self.stage = stage
        self.ready_at = ready_at
        self.updated_at = time.monotonic()

    def reset(self):
        self.set(STAGE_OPEN_CARD, 0)

    def get(self):
        now = time.monotonic()
        if (
            self.stage != STAGE_OPEN_CARD
            and self.updated_at
            and now - self.updated_at > self.max_age_seconds
        ):
            self.reset()
            return self.stage

        if self.stage == STAGE_OPENING_CARD and now >= self.ready_at:
            self.set(STAGE_BUY, 0)
        elif self.stage == STAGE_OPENING_BUY_DIALOG and now >= self.ready_at:
            self.set(STAGE_QUANTITY, 0)

        return self.stage
