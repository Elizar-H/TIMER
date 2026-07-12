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
