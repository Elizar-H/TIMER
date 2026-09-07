from collections.abc import Callable
from dataclasses import dataclass, field
import threading
import time


@dataclass
class SalvageRuntimeState:
    """Mutable runtime state shared by the salvage workflow."""

    running: bool = False
    finalizing: bool = False
    stop_event: threading.Event = field(default_factory=threading.Event)
    expected_cursor_pos: tuple[int, int] | None = None
    last_item_right_click_at: float = 0
    delete_was_down: bool = False
    last_delete_handled_at: float = 0
    pair_armed: bool = False
    cleanup_requested: bool = False
    restart_after_stop: bool = False
    arm_after_restart: bool = False
    finish_current_cycle_requested: bool = False
    action_hwnd: int = 0
    pair_hwnd: int = 0
    lifecycle_lock: threading.RLock = field(default_factory=threading.RLock)


@dataclass(frozen=True)
class SalvageWorkflowConfig:
    """Timing values used by the salvage workflow orchestration."""

    startup_delay_seconds: float
    post_menu_click_delay_seconds: float
    post_all_click_delay_seconds: float
    confirm_hold_seconds: float
    after_confirm_seconds: float


@dataclass(frozen=True)
class SalvageWorkflowDependencies:
    """Application operations needed to run and finalize salvage."""

    get_action_hwnd: Callable[[], int]
    schedule_ui: Callable[..., object]
    hide_picker: Callable[[], object]
    sleep_with_stop: Callable[..., bool]
    click: Callable[..., bool]
    right_click_item: Callable[..., bool]
    click_context_disassemble: Callable[..., bool]
    wait_for_confirm: Callable[..., bool]
    hold: Callable[..., bool]
    note_cursor_position: Callable[[], object]
    is_live_game_window: Callable[[int], bool]
    release_left_mouse_button: Callable[[], object]
    restore_sort_type: Callable[..., bool]
    start_workflow: Callable[..., bool]
    append_log_line: Callable[[str], object]
    log_error: Callable[[str, str], object]


class SalvageWorkflow:
    """Orchestrates one salvage worker while keeping app details external."""

    def __init__(self, state, config, dependencies):
        self.state = state
        self.config = config
        self.dependencies = dependencies

    def run(self, stop_event):
        """Runs the current salvage sequence and always finalizes its state."""
        state = self.state
        config = self.config
        dependencies = self.dependencies

        try:
            hwnd = state.action_hwnd or dependencies.get_action_hwnd()
            if not hwnd:
                dependencies.append_log_line(
                    "salvage start failed: game window not found"
                )
                return

            state.action_hwnd = hwnd
            state.expected_cursor_pos = None
            state.last_item_right_click_at = 0
            dependencies.schedule_ui(0, dependencies.hide_picker)
            dependencies.sleep_with_stop(
                config.startup_delay_seconds,
                stop_event,
            )

            if not dependencies.click("salvage.storage_tab", stop_event):
                return
            if not dependencies.click("salvage.details_tab", stop_event):
                return
            if not dependencies.click("salvage.decor_category", stop_event):
                return
            if not dependencies.click("salvage.sort_dropdown", stop_event):
                return
            if not dependencies.click("salvage.sort_new_option", stop_event):
                return

            if state.finish_current_cycle_requested:
                return

            while (
                not stop_event.is_set()
                and not state.finish_current_cycle_requested
                and dependencies.is_live_game_window(state.action_hwnd)
            ):
                if not dependencies.right_click_item(
                    "salvage.first_item",
                    stop_event,
                ):
                    break
                if not dependencies.click_context_disassemble(stop_event):
                    break
                if (
                    config.post_menu_click_delay_seconds > 0
                    and not dependencies.sleep_with_stop(
                        config.post_menu_click_delay_seconds,
                        stop_event,
                        mouse_guard=True,
                    )
                ):
                    break

                if not dependencies.wait_for_confirm(stop_event):
                    dependencies.append_log_line(
                        "salvage stopped: confirm button not found"
                    )
                    with state.lifecycle_lock:
                        # An empty list can resemble a menu to the pixel probe.
                        # Return to resources unless the user cancelled the run.
                        if not stop_event.is_set():
                            state.cleanup_requested = True
                    break

                if not dependencies.click("salvage.all_button", stop_event):
                    break
                if not dependencies.sleep_with_stop(
                    config.post_all_click_delay_seconds,
                    stop_event,
                    mouse_guard=True,
                ):
                    break
                if not dependencies.hold(
                    "salvage.confirm_button",
                    config.confirm_hold_seconds,
                    stop_event=stop_event,
                    mouse_guard=True,
                    before_hold=dependencies.note_cursor_position,
                ):
                    break
                if not dependencies.sleep_with_stop(
                    config.after_confirm_seconds,
                    stop_event,
                    mouse_guard=True,
                ):
                    break
                if state.finish_current_cycle_requested:
                    break
        except Exception as error:
            dependencies.log_error(
                "salvage",
                f"Salvage loop failed: {error}",
            )
        finally:
            with state.lifecycle_lock:
                state.finalizing = True
                was_cancelled = stop_event.is_set()
                should_cleanup = state.cleanup_requested
                should_restart = was_cancelled and state.restart_after_stop
                should_arm_after_restart = state.arm_after_restart
                action_hwnd = state.action_hwnd

            try:
                dependencies.release_left_mouse_button()
                if should_cleanup:
                    dependencies.restore_sort_type(hwnd=action_hwnd)
            except Exception as error:
                dependencies.log_error(
                    "salvage_cleanup",
                    f"Salvage cleanup failed: {error}",
                )
            finally:
                with state.lifecycle_lock:
                    state.running = False
                    state.action_hwnd = 0
                    state.cleanup_requested = False
                    state.restart_after_stop = False
                    state.arm_after_restart = False
                    state.finish_current_cycle_requested = False
                    stop_event.clear()
                    state.finalizing = False

            if should_restart:
                try:
                    dependencies.schedule_ui(
                        0,
                        lambda: dependencies.start_workflow(
                            arm_pair=should_arm_after_restart
                        ),
                    )
                except Exception as error:
                    dependencies.log_error(
                        "salvage_restart",
                        f"Salvage restart schedule failed: {error}",
                    )


def is_context_light_pixel(rgb, min_channel, max_channel_spread):
    """Returns whether a sampled context-menu pixel matches the light style."""
    if rgb is None:
        return False

    return (
        min(rgb) >= min_channel
        and max(rgb) - min(rgb) <= max_channel_spread
    )


def select_context_disassemble_point(
    stop_event,
    *,
    fallback_point,
    monotonic,
    get_choices,
    get_wait_seconds,
    get_poll_seconds,
    get_action_hwnd,
    is_live_window,
    first_light_sample,
    sleep_with_stop,
    append_log_line,
    request_finish_current_cycle,
):
    """Selects the current disassemble option using the existing probe order."""
    started_at = monotonic()
    deadline = started_at + max(0.0, get_wait_seconds())
    probe_log_parts = []

    while not stop_event.is_set() and is_live_window(get_action_hwnd()):
        top_probe, top_click = get_choices()[0]
        bottom_probe, bottom_click = get_choices()[1]

        top_hit, top_rgb = first_light_sample(top_probe)
        bottom_hit, bottom_rgb = first_light_sample(bottom_probe)
        probe_log_parts = [
            f"{top_probe}={top_rgb}",
            f"{bottom_probe}={bottom_rgb}",
        ]

        if top_hit is not None:
            return top_click
        if bottom_hit is not None:
            return bottom_click

        remaining_seconds = deadline - monotonic()
        if remaining_seconds <= 0:
            break

        wait_for_next_probe = min(
            max(0.001, get_poll_seconds()),
            remaining_seconds,
        )
        if not sleep_with_stop(
            wait_for_next_probe,
            stop_event,
            mouse_guard=True,
        ):
            return None

    elapsed_ms = round((monotonic() - started_at) * 1000)
    append_log_line(
        "salvage context probe "
        + " ".join(probe_log_parts)
        + f" finish_after_fallback_step elapsed_ms={elapsed_ms}"
    )
    request_finish_current_cycle(cleanup=True)
    return fallback_point


def wait_for_confirm_available(
    stop_event,
    *,
    monotonic,
    get_wait_seconds,
    get_poll_seconds,
    get_action_hwnd,
    is_live_window,
    confirm_available,
    sleep_with_stop,
):
    """Waits for salvage confirmation using the existing polling order."""
    deadline = monotonic() + max(0.0, get_wait_seconds())

    while not stop_event.is_set() and is_live_window(get_action_hwnd()):
        if confirm_available():
            return True

        remaining_seconds = deadline - monotonic()
        if remaining_seconds <= 0:
            return False

        if not sleep_with_stop(
            min(get_poll_seconds(), remaining_seconds),
            stop_event,
            mouse_guard=True,
        ):
            return False

    return False


def has_cursor_moved(expected_pos, current_pos, threshold_pixels):
    if expected_pos is None or current_pos is None:
        return False

    dx = abs(current_pos[0] - expected_pos[0])
    dy = abs(current_pos[1] - expected_pos[1])
    return dx > threshold_pixels or dy > threshold_pixels


def wait_while_mouse_button_held(
    seconds,
    stop_event=None,
    mouse_guard=False,
    cursor_moved=None,
    on_mouse_cancel=None,
):
    end_at = time.monotonic() + max(0, seconds)
    while time.monotonic() < end_at:
        if stop_event is not None and stop_event.is_set():
            return False
        if mouse_guard and cursor_moved is not None and cursor_moved():
            if on_mouse_cancel is not None:
                on_mouse_cancel()
            return False
        time.sleep(0.01)
    return True


def sleep_with_stop(
    seconds,
    stop_event,
    mouse_guard=False,
    cursor_moved=None,
    on_mouse_cancel=None,
):
    end_at = time.monotonic() + max(0, seconds)
    while time.monotonic() < end_at:
        if stop_event.is_set():
            return False
        if mouse_guard and cursor_moved is not None and cursor_moved():
            if on_mouse_cancel is not None:
                on_mouse_cancel()
            return False
        time.sleep(min(0.02, max(0, end_at - time.monotonic())))
    return not stop_event.is_set()


def remaining_cooldown_seconds(last_action_at, min_interval_seconds):
    since_last_action = time.monotonic() - last_action_at
    if since_last_action < min_interval_seconds:
        return min_interval_seconds - since_last_action
    return 0
