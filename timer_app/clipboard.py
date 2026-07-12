"""Low-level Windows clipboard helpers."""

import ctypes
from ctypes import wintypes


CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


def set_clipboard_text_win32(text, log_message):
    """Places Unicode text on the clipboard through WinAPI."""
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]

    text_bytes = text.encode("utf-16-le") + b"\x00\x00"

    if not user32.OpenClipboard(0):
        log_message(f"OpenClipboard failed, err={kernel32.GetLastError()}")
        return False

    h_mem = None
    try:
        user32.EmptyClipboard()
        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
        if not h_mem:
            log_message(f"GlobalAlloc failed, err={kernel32.GetLastError()}")
            return False

        ptr = kernel32.GlobalLock(h_mem)
        if not ptr:
            log_message(f"GlobalLock failed, err={kernel32.GetLastError()}")
            kernel32.GlobalFree(h_mem)
            return False

        ctypes.memmove(ptr, text_bytes, len(text_bytes))
        kernel32.GlobalUnlock(h_mem)

        if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
            log_message(f"SetClipboardData failed, err={kernel32.GetLastError()}")
            kernel32.GlobalFree(h_mem)
            return False

        # After SetClipboardData succeeds, Windows owns the memory block.
        h_mem = None
        return True
    finally:
        user32.CloseClipboard()


def get_clipboard_text_win32():
    """Returns Unicode clipboard text through WinAPI, if available."""
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]

    if not user32.OpenClipboard(0):
        return None

    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None

        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return None

        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()
