"""Shared JY branding for all desktop control panels."""

import os
import tkinter as tk


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "jysecai-logo.png"))


def apply_window_icon(root):
    """Apply the shared JY PNG as the window and taskbar icon."""
    try:
        icon = tk.PhotoImage(file=ICON_PATH)
        root.iconphoto(True, icon)
        root._jysecai_window_icon = icon
        return True
    except (tk.TclError, OSError):
        return False
