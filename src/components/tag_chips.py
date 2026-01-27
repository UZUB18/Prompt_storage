"""Tag chips input component."""
from __future__ import annotations

import re
import customtkinter as ctk
from typing import Callable, List, Optional


class TagChip(ctk.CTkFrame):
    """Single tag chip with remove button."""

    def __init__(
        self,
        master,
        text: str,
        on_remove: Callable[[str], None],
        colors: dict,
        **kwargs,
    ):
        super().__init__(master, fg_color=colors["pill_bg"], corner_radius=10, **kwargs)
        self._text = text
        self._on_remove = on_remove
        self._colors = colors

        label = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["text_secondary"],
        )
        label.pack(side="left", padx=(8, 4), pady=3)

        remove_btn = ctk.CTkButton(
            self,
            text="\u00D7",
            width=18,
            height=18,
            corner_radius=9,
            fg_color="transparent",
            hover_color=colors["surface"],
            text_color=colors["text_muted"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            border_width=0,
            command=self._handle_remove,
        )
        remove_btn.pack(side="left", padx=(0, 6), pady=2)

        # Make chip focusable for clicks
        for widget in (self, label, remove_btn):
            widget.bind("<Button-1>", lambda _e: None)

    def _handle_remove(self):
        self._on_remove(self._text)


class TagChipsInput(ctk.CTkFrame):
    """Multi-tag input with removable chips."""

    def __init__(
        self,
        master,
        colors: dict,
        on_change: Optional[Callable[[], None]] = None,
        placeholder_text: str = "Add tags…",
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=colors["surface"],
            border_width=1,
            border_color=colors["border"],
            corner_radius=10,
            **kwargs,
        )
        self._colors = colors
        self._on_change = on_change
        self._tags: List[str] = []
        self._chips: List[TagChip] = []

        self.grid_columnconfigure(0, weight=1)

        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.grid(row=0, column=0, sticky="ew", padx=6, pady=6)

        self.entry = ctk.CTkEntry(
            self.inner,
            height=28,
            fg_color=colors["surface"],
            border_width=0,
            text_color=colors["text_primary"],
            placeholder_text=placeholder_text,
            width=120,
        )
        self.entry.bind("<Return>", self._on_return)
        self.entry.bind("<KP_Enter>", self._on_return)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<BackSpace>", self._on_backspace)

        self.inner.bind("<Configure>", lambda _e: self._layout())
        self.bind("<Configure>", lambda _e: self._layout())
        self.bind("<Button-1>", lambda _e: self.entry.focus_set())

        self._layout()

    def get_tags(self) -> List[str]:
        return list(self._tags)

    def set_tags(self, tags: List[str], notify: bool = False):
        self._clear_tags()
        for tag in tags:
            self._add_tag(tag, notify=False)
        if notify:
            self._emit_change()

    def _emit_change(self):
        if self._on_change:
            self._on_change()

    def _normalize(self, tag: str) -> str:
        return tag.strip()

    def _has_tag(self, tag: str) -> bool:
        lower = tag.lower()
        return any(existing.lower() == lower for existing in self._tags)

    def _add_tag(self, tag: str, notify: bool = True):
        clean = self._normalize(tag)
        if not clean or self._has_tag(clean):
            return
        chip = TagChip(self.inner, clean, self._remove_tag, self._colors)
        self._tags.append(clean)
        self._chips.append(chip)
        self._layout()
        if notify:
            self._emit_change()

    def _remove_tag(self, tag: str):
        for idx, existing in enumerate(self._tags):
            if existing == tag:
                self._tags.pop(idx)
                chip = self._chips.pop(idx)
                chip.destroy()
                self._layout()
                self._emit_change()
                break

    def _clear_tags(self):
        for chip in self._chips:
            chip.destroy()
        self._chips.clear()
        self._tags.clear()
        self._layout()

    def _extract_tags(self, force: bool = False) -> List[str]:
        text = self.entry.get()
        if not text.strip():
            return []

        if force:
            parts = re.split(r"[,;\n]+", text)
            self.entry.delete(0, "end")
            return [p.strip() for p in parts if p.strip()]

        if any(sep in text for sep in (",", ";", "\n")):
            parts = re.split(r"[,;\n]", text)
            pending = parts[-1]
            tags = [p.strip() for p in parts[:-1] if p.strip()]
            self.entry.delete(0, "end")
            if pending.strip():
                self.entry.insert(0, pending.strip())
            return tags

        return []

    def _commit_entry(self, force: bool = False):
        for tag in self._extract_tags(force=force):
            self._add_tag(tag, notify=True)

    def _on_return(self, _event=None):
        self._commit_entry(force=True)
        return "break"

    def _on_focus_out(self, _event=None):
        self._commit_entry(force=True)

    def _on_key_release(self, _event=None):
        self._commit_entry(force=False)

    def _on_backspace(self, _event=None):
        if self.entry.get():
            return None
        if self._tags:
            self._remove_tag(self._tags[-1])
            return "break"
        return None

    def _layout(self):
        widgets = self._chips + [self.entry]
        for widget in widgets:
            widget.grid_forget()

        max_width = self.inner.winfo_width()
        if max_width <= 1:
            self.after(10, self._layout)
            return

        row = 0
        col = 0
        x = 0
        pad_x = 6
        pad_y = 6
        available = max_width - pad_x

        for widget in widgets:
            widget.update_idletasks()
            width = widget.winfo_reqwidth()
            if x + width > available and x > 0:
                row += 1
                col = 0
                x = 0
            widget.grid(row=row, column=col, padx=(0, pad_x), pady=(0, pad_y), sticky="w")
            x += width + pad_x
            col += 1
