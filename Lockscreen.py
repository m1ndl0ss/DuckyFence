import ctypes
from ctypes import wintypes


class Lockscreen:
    """Thin wrapper over user32 BlockInput.

    BlockInput only takes effect when the process is elevated; without
    elevation the call fails silently and only the fullscreen challenge
    window stands between the payload and the desktop.
    """

    def __init__(self):
        self.BlockInput = ctypes.windll.user32.BlockInput
        self.BlockInput.argtypes = [wintypes.BOOL]
        self.BlockInput.restype = wintypes.BOOL

    def block(self):
        self.BlockInput(True)

    def unblock(self):
        self.BlockInput(False)
