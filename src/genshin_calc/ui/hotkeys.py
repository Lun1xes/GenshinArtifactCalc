"""Layout-agnostic hotkey handler for Windows.

Binds Ctrl+A, Ctrl+C, Ctrl+V, and Ctrl+X globally so they function seamlessly
whether the active Windows keyboard layout is Russian, English, or any other.
"""
from __future__ import annotations

import tkinter as tk
from typing import Any, Optional


def setup_layout_agnostic_hotkeys(root: Any) -> None:
    """Register global layout-agnostic Control key shortcuts on root."""
    
    def handle_control_keys(event: Any) -> Optional[str]:
        return handle_control_event(root, event)

    root.bind_all("<Control-KeyPress>", handle_control_keys)
    root._handle_control_keys = lambda event: handle_control_event(root, event)


def handle_control_event(root: Any, event: Any) -> Optional[str]:
    """Handle virtual keycodes 65, 67, 86, 88 across all layouts."""
    keycode = getattr(event, "keycode", 0)
    widget = getattr(event, "widget", None)

    # Some widgets are CTkEntry wrappers; resolve underlying tk.Entry if available
    target_widget = widget
    if hasattr(widget, "_entry"):
        target_widget = widget._entry
    elif hasattr(widget, "_textbox"):
        target_widget = widget._textbox

    # VK_A = 65 (Select All)
    if keycode == 65:
        if target_widget and hasattr(target_widget, "select_range"):
            try:
                target_widget.select_range(0, "end")
                target_widget.icursor("end")
                return "break"
            except Exception:
                pass
        elif target_widget and hasattr(target_widget, "tag_add"):
            try:
                target_widget.tag_add("sel", "1.0", "end")
                return "break"
            except Exception:
                pass

    # VK_C = 67 (Copy)
    elif keycode == 67:
        if target_widget:
            try:
                selected_text = ""
                if hasattr(target_widget, "selection_get"):
                    selected_text = target_widget.selection_get()
                elif hasattr(target_widget, "get") and hasattr(target_widget, "select_present") and target_widget.select_present():
                    first = target_widget.index("sel.first")
                    last = target_widget.index("sel.last")
                    selected_text = target_widget.get()[first:last]
                if selected_text:
                    root.clipboard_clear()
                    root.clipboard_append(selected_text)
                    return "break"
            except Exception:
                pass

    # VK_V = 86 (Paste)
    elif keycode == 86:
        if target_widget:
            try:
                clip = root.clipboard_get()
                if clip:
                    if hasattr(target_widget, "selection_present") and target_widget.selection_present():
                        target_widget.delete("sel.first", "sel.last")
                    if hasattr(target_widget, "insert"):
                        idx = target_widget.index("insert") if hasattr(target_widget, "index") else "end"
                        target_widget.insert(idx, clip)
                        # Notify parent CTkEntry if needed
                        if hasattr(widget, "_activate_placeholder"):
                            widget._activate_placeholder()
                    return "break"
            except Exception:
                pass

    # VK_X = 88 (Cut)
    elif keycode == 88:
        if target_widget:
            try:
                selected_text = ""
                if hasattr(target_widget, "selection_present") and target_widget.selection_present():
                    first = target_widget.index("sel.first")
                    last = target_widget.index("sel.last")
                    if hasattr(target_widget, "get"):
                        selected_text = target_widget.get()[first:last]
                    target_widget.delete("sel.first", "sel.last")
                elif hasattr(target_widget, "selection_get"):
                    selected_text = target_widget.selection_get()
                    if hasattr(target_widget, "delete"):
                        target_widget.delete("sel.first", "sel.last")
                if selected_text:
                    root.clipboard_clear()
                    root.clipboard_append(selected_text)
                return "break"
            except Exception:
                return "break"

    return None
