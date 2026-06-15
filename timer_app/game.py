import ctypes
import time

from timer_app.coordinates import coordinate_pair
from timer_app.windows import get_hwnd_ratio_point


class GameActions:
    def __init__(
        self,
        coordinates,
        get_action_hwnd,
        get_hover_delay,
        get_mouse_click_delay,
        send_click,
        send_right_click,
        hold_left_mouse,
    ):
        self._coordinates = coordinates
        self._get_action_hwnd = get_action_hwnd
        self._get_hover_delay = get_hover_delay
        self._get_mouse_click_delay = get_mouse_click_delay
        self._send_click = send_click
        self._send_right_click = send_right_click
        self._hold_left_mouse = hold_left_mouse

    def set_coordinates(self, coordinates):
        self._coordinates = coordinates

    def point(self, point_name):
        return coordinate_pair(self._coordinates, point_name)

    def pixel_point(self, point_name, hwnd=None):
        target_hwnd = hwnd if hwnd is not None else self._get_action_hwnd()
        if not target_hwnd:
            return None

        x_ratio, y_ratio = self.point(point_name)
        return get_hwnd_ratio_point(target_hwnd, x_ratio, y_ratio)

    def move_to(self, point_name, hwnd=None):
        point = self.pixel_point(point_name, hwnd=hwnd)
        if point is None:
            return False

        ctypes.windll.user32.SetCursorPos(point[0], point[1])
        time.sleep(self._get_hover_delay())
        return True

    def click(self, point_name, hwnd=None):
        if not self.move_to(point_name, hwnd=hwnd):
            return False
        return self._send_click(self._get_mouse_click_delay())

    def right_click(self, point_name, hwnd=None):
        if not self.move_to(point_name, hwnd=hwnd):
            return False
        return self._send_right_click(self._get_mouse_click_delay())

    def hold(
        self,
        point_name,
        seconds,
        stop_event=None,
        mouse_guard=False,
        before_hold=None,
    ):
        if not self.move_to(point_name):
            return False
        if mouse_guard and before_hold is not None:
            before_hold()
        return self._hold_left_mouse(
            seconds,
            stop_event=stop_event,
            mouse_guard=mouse_guard,
        )
