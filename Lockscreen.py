import ctypes
from ctypes import wintypes
#only works when run as admin... think of fix for .exe
class Lockscreen:
    def __init__(self):
        self.BlockInput = ctypes.windll.user32.BlockInput
        self.BlockInput.argtypes = [wintypes.BOOL]
        self.BlockInput.restype = wintypes.BOOL

    def block(self):
        self.BlockInput(True)

    def unblock(self):
        self.BlockInput(False)