"""Prompt editor component - Apple 2026 Edition with proper auto-sizing."""
import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable, Dict
import subprocess
import os
import threading
import time
import json
import re

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from ..models import Prompt, Category
from .dialogs import FindReplaceDialog, ConfirmDialog
from .tag_chips import TagChipsInput


class PromptEditor(ctk.CTkFrame):
    """Premium prompt editor with proper auto-sizing layout."""
    _sensitive_copy_warned = False

    def __init__(
        self,
        master,
        on_save: Callable[[Prompt], None],
        on_delete: Callable[[str], None],
        on_copy: Callable[[str], None],
        on_toggle_pin: Callable[[Prompt], None],
        on_show_history: Callable[[Prompt], None],
        on_version_bump: Callable[[Prompt], None],
        on_toast: Callable[[str], None],
        on_change: Callable[[], None],
        colors: Dict[str, str],
        **kwargs
    ):
        super().__init__(master, fg_color=colors["surface"], corner_radius=0, **kwargs)
        self.on_save = on_save
        self.on_delete = on_delete
        self.on_copy = on_copy
        self.on_toggle_pin = on_toggle_pin
        self.on_show_history = on_show_history
        self.on_version_bump = on_version_bump
        self.on_toast = on_toast
        self.on_change = on_change
        self.colors = colors
        self.current_prompt: Optional[Prompt] = None
        self._find_dialog: Optional[FindReplaceDialog] = None
        self._replace_dialog: Optional[FindReplaceDialog] = None
        self._format_menu: Optional[tk.Menu] = None
        self._copy_as_menu: Optional[tk.Menu] = None
        self._content_hidden = False
        self._hidden_content_cache = ""
        self._auto_hide_after_ms = 60000
        self._auto_hide_id = None

        # Use grid for main layout - allows proper expansion
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Empty state
        self.empty_frame = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=0)
        self.empty_frame.grid(row=0, column=0, sticky="nsew")

        empty_label = ctk.CTkLabel(
            self.empty_frame,
            text="Select a prompt to edit\nor create a new one",
            font=ctk.CTkFont(family="Segoe UI", size=16),
            text_color=colors["text_muted"],
            justify="center",
        )
        empty_label.place(relx=0.5, rely=0.5, anchor="center")

        # Editor container - uses grid for expansion
        self.card = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=0)
        
        # Configure card grid - header fixed, divider, content expands, footer fixed
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_rowconfigure(0, weight=0)  # Header - fixed
        self.card.grid_rowconfigure(1, weight=0)  # Divider
        self.card.grid_rowconfigure(2, weight=1)  # Content - expands
        self.card.grid_rowconfigure(3, weight=0)  # Footer - fixed

        # ========== HEADER ==========
        header = ctk.CTkFrame(self.card, fg_color="transparent", height=56)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 0))
        header.grid_propagate(False)

        divider = ctk.CTkFrame(self.card, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, sticky="ew", padx=24, pady=(12, 6))

        # Left: Title
        self.title_label = ctk.CTkLabel(
            header,
            text="Edit Prompt",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=colors["text_primary"],
        )
        self.title_label.pack(side="left", pady=12)

        # Right: AI buttons + copy
        right_frame = ctk.CTkFrame(header, fg_color="transparent")
        right_frame.pack(side="right", fill="y")

        # AI Testing buttons
        ai_container = ctk.CTkFrame(
            right_frame,
            fg_color=colors["bg"],
            corner_radius=10,
            border_width=1,
            border_color=colors["border"],
        )
        ai_container.pack(side="left", pady=10, padx=(0, 8))

        self.gemini_btn = ctk.CTkButton(
            ai_container, text="Gemini", width=55, height=28, corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=colors["surface"], hover_color=colors["surface"],
            text_color="#4285F4", border_width=1, border_color=colors["border"],
            command=lambda: self._test_in_ai("gemini"),
        )
        self.gemini_btn.pack(side="left", padx=2, pady=3)

        self.chatgpt_btn = ctk.CTkButton(
            ai_container, text="GPT", width=40, height=28, corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent", hover_color=colors["surface"],
            text_color=colors["text_secondary"],
            command=lambda: self._test_in_ai("chatgpt"),
        )
        self.chatgpt_btn.pack(side="left", padx=2, pady=3)

        self.grok_btn = ctk.CTkButton(
            ai_container, text="Grok", width=40, height=28, corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent", hover_color=colors["surface"],
            text_color=colors["text_secondary"],
            command=lambda: self._test_in_ai("grok"),
        )
        self.grok_btn.pack(side="left", padx=2, pady=3)

        # Pin button
        self.pin_btn = ctk.CTkButton(
            right_frame,
            text="\u2606",
            width=30,
            height=28,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=colors["surface"],
            hover_color=colors["bg"],
            text_color=colors["text_muted"],
            border_width=1,
            border_color=colors["border"],
            command=self._on_toggle_pin,
        )
        self.pin_btn.pack(side="left", pady=10, padx=(0, 8))

        # Copy button
        self.copy_btn = ctk.CTkButton(
            right_frame,
            text="Copy",
            width=52,
            height=28,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=colors["surface"],
            hover_color=colors["bg"],
            text_color=colors["text_secondary"],
            border_width=1,
            border_color=colors["border"],
            command=self._on_copy,
        )
        self.copy_btn.pack(side="left", pady=10)

        self.copy_as_btn = ctk.CTkButton(
            right_frame,
            text="Copy as",
            width=74,
            height=28,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=self.colors["surface"],
            hover_color=self.colors["bg"],
            text_color=self.colors["text_secondary"],
            border_width=1,
            border_color=self.colors["border"],
            command=self._show_copy_as_menu,
        )
        self.copy_as_btn.pack(side="left", padx=(8, 0), pady=10)

        # ========== CONTENT (Expandable) ==========
        content = ctk.CTkFrame(self.card, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=24, pady=12)
        
        # Grid layout for form - content expands
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=0)  # Name/Category row
        content.grid_rowconfigure(1, weight=0)  # Tags row
        content.grid_rowconfigure(2, weight=0)  # Content label
        content.grid_rowconfigure(3, weight=1)  # Content text (EXPANDS!)

        # Row 0: Name (left) + Category (right)
        # Name
        name_frame = ctk.CTkFrame(content, fg_color="transparent")
        name_frame.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 12))
        
        ctk.CTkLabel(
            name_frame, text="NAME",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=colors["text_muted"],
        ).pack(anchor="w", pady=(0, 4))
        
        self.name_entry = ctk.CTkEntry(
            name_frame, height=38,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=colors["surface"], border_color=colors["border"],
            border_width=1, corner_radius=10, text_color=colors["text_primary"],
        )
        self.name_entry.pack(fill="x")
        self.name_entry.bind("<KeyRelease>", self._on_field_change)

        # Category
        cat_frame = ctk.CTkFrame(content, fg_color="transparent")
        cat_frame.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 12))
        
        ctk.CTkLabel(
            cat_frame, text="CATEGORY",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=colors["text_muted"],
        ).pack(anchor="w", pady=(0, 4))
        
        self.category_var = ctk.StringVar(value=Category.OTHER.value)
        # CTkOptionMenu doesn't render an entry-like border by default; wrap it.
        cat_outer = ctk.CTkFrame(
            cat_frame,
            fg_color=colors["surface"],
            corner_radius=10,
            border_width=1,
            border_color=colors["border"],
        )
        cat_outer.pack(fill="x")
        self.category_dropdown = ctk.CTkOptionMenu(
            cat_outer,
            values=[c.value for c in Category],
            variable=self.category_var,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=colors["surface"],
            text_color=colors["text_primary"],
            button_color=colors["surface"],
            button_hover_color=colors["bg"],
            dropdown_fg_color=colors["surface"],
            dropdown_text_color=colors["text_primary"],
            dropdown_hover_color=colors["accent_glow"],
            corner_radius=9,
            command=lambda _: self._on_field_change(),
        )
        self.category_dropdown.pack(fill="x", padx=1, pady=1)

        # Row 1: Tags (spans both columns)
        tags_frame = ctk.CTkFrame(content, fg_color="transparent")
        tags_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        
        ctk.CTkLabel(
            tags_frame, text="TAGS",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=colors["text_muted"],
        ).pack(anchor="w", pady=(0, 4))
        
        self.tags_input = TagChipsInput(
            tags_frame,
            colors=colors,
            on_change=self._on_field_change,
            placeholder_text="Add tags (comma or Enter)…",
        )
        self.tags_input.pack(fill="x")

        # Row 2: Content label with counts
        content_header = ctk.CTkFrame(content, fg_color="transparent")
        content_header.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        
        ctk.CTkLabel(
            content_header, text="PROMPT CONTENT",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=colors["text_muted"],
        ).pack(side="left")
        
        right_header = ctk.CTkFrame(content_header, fg_color="transparent")
        right_header.pack(side="right")

        self.sensitive_var = ctk.BooleanVar(value=False)
        self.sensitive_toggle = ctk.CTkSwitch(
            right_header,
            text="Sensitive",
            variable=self.sensitive_var,
            onvalue=True,
            offvalue=False,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=colors["text_muted"],
            command=self._on_sensitive_toggle,
        )
        self.sensitive_toggle.pack(side="left", padx=(0, 10))

        self.reveal_btn = ctk.CTkButton(
            right_header,
            text="Reveal",
            width=60,
            height=22,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            fg_color=self.colors["surface"],
            hover_color=self.colors["bg"],
            text_color=self.colors["text_secondary"],
            border_width=1,
            border_color=self.colors["border"],
            command=self._toggle_reveal,
        )
        self.reveal_btn.pack(side="left", padx=(0, 10))

        self.char_count_label = ctk.CTkLabel(
            right_header, text="0 chars",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=colors["text_muted"],
        )
        self.char_count_label.pack(side="left")

        # Row 3: Content textbox (EXPANDS to fill remaining space)
        self.content_text = ctk.CTkTextbox(
            content,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=colors["surface"], text_color=colors["text_primary"],
            border_color=colors["border"], border_width=1, corner_radius=10,
            wrap="word",
        )
        self.content_text.grid(row=3, column=0, columnspan=2, sticky="nsew")
        self.content_text.bind("<KeyRelease>", self._on_field_change)

        # ========== FOOTER (Fixed) ==========
        footer = ctk.CTkFrame(self.card, fg_color=colors["surface"], corner_radius=0, height=60)
        footer.grid(row=3, column=0, sticky="ew")
        footer.grid_propagate(False)

        # Top border
        ctk.CTkFrame(footer, height=1, fg_color=colors["border"]).pack(fill="x", side="top")

        footer_inner = ctk.CTkFrame(footer, fg_color="transparent")
        footer_inner.pack(fill="both", expand=True, padx=24)

        left_footer = ctk.CTkFrame(footer_inner, fg_color="transparent")
        left_footer.pack(side="left", pady=10)

        # State label
        self.state_label = ctk.CTkLabel(
            left_footer, text="All changes saved",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["text_muted"],
        )
        self.state_label.pack(side="left", pady=6)

        self.format_btn = ctk.CTkButton(
            left_footer,
            text="Format",
            width=70,
            height=28,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=self.colors["surface"],
            hover_color=self.colors["bg"],
            text_color=self.colors["text_secondary"],
            border_width=1,
            border_color=self.colors["border"],
            command=self._show_format_menu,
        )
        self.format_btn.pack(side="left", padx=(10, 0), pady=6)

        self.version_btn = ctk.CTkButton(
            left_footer,
            text="Version +",
            width=90,
            height=28,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=self.colors["surface"],
            hover_color=self.colors["bg"],
            text_color=self.colors["text_secondary"],
            border_width=1,
            border_color=self.colors["border"],
            command=self._on_version_bump,
        )
        self.version_btn.pack(side="left", padx=(8, 0), pady=6)

        self.history_btn = ctk.CTkButton(
            left_footer,
            text="History",
            width=80,
            height=28,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=self.colors["surface"],
            hover_color=self.colors["bg"],
            text_color=self.colors["text_secondary"],
            border_width=1,
            border_color=self.colors["border"],
            command=self._on_show_history,
        )
        self.history_btn.pack(side="left", padx=(8, 0), pady=6)

        # Save button
        self.save_btn = ctk.CTkButton(
            footer_inner, text="Save", width=90, height=36, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=colors["accent"], hover_color=colors["accent_hover"],
            command=self._on_save,
        )
        self.save_btn.pack(side="right", pady=12)

        # Delete button
        self.delete_btn = ctk.CTkButton(
            footer_inner, text="Delete", width=70, height=36, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent", hover_color="#FEE2E2",
            text_color=colors["danger"],
            command=self._on_delete,
        )
        self.delete_btn.pack(side="right", padx=(0, 8), pady=12)

    def set_prompt(self, prompt: Optional[Prompt]):
        """Set prompt to edit."""
        self.current_prompt = prompt

        if prompt is None:
            self.card.grid_forget()
            self.empty_frame.grid(row=0, column=0, sticky="nsew")
            return

        self.empty_frame.grid_forget()
        self.card.grid(row=0, column=0, sticky="nsew")

        # Populate fields
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, prompt.name)
        self.category_var.set(prompt.category.value)
        self.tags_input.set_tags(prompt.tags)
        self.sensitive_var.set(bool(prompt.sensitive))
        self._hidden_content_cache = prompt.content
        self._content_hidden = bool(prompt.sensitive)
        self._schedule_auto_hide()
        self._apply_sensitive_view()

        self._update_pin_button()
        self._update_state_label()
        self._update_char_count()

    def _update_pin_button(self):
        if not self.current_prompt:
            self.pin_btn.configure(text="\u2606", text_color=self.colors["text_muted"])
            return
        if self.current_prompt.pinned:
            self.pin_btn.configure(text="\u2605", text_color=self.colors["accent"])
        else:
            self.pin_btn.configure(text="\u2606", text_color=self.colors["text_muted"])

    def _update_state_label(self):
        if self.current_prompt:
            self.state_label.configure(text="All changes saved", text_color=self.colors["text_muted"])

    def _update_char_count(self):
        content = self._get_current_content()
        chars = len(content)
        words = len(re.findall(r"\S+", content))
        lines = 0 if not content else content.count("\n") + 1
        self.char_count_label.configure(
            text=f"{chars:,} chars • {words:,} words • {lines:,} lines"
        )

    def update_save_state(self, has_changes: bool):
        if has_changes:
            self.state_label.configure(text="Unsaved changes", text_color=self.colors["warning"])
        else:
            self._update_state_label()

    def clear(self):
        self.current_prompt = None
        self.card.grid_forget()
        self.empty_frame.grid(row=0, column=0, sticky="nsew")

    def get_tags(self) -> list[str]:
        return self.tags_input.get_tags()

    def set_tags(self, tags: list[str], notify: bool = False):
        self.tags_input.set_tags(tags, notify=notify)

    def _on_field_change(self, event=None):
        if self.current_prompt:
            self.on_change()
            self._update_char_count()

    def _on_save(self):
        if not self.current_prompt:
            return
        self.current_prompt.name = self.name_entry.get().strip()
        self.current_prompt.category = Category(self.category_var.get())
        self.current_prompt.tags = self.tags_input.get_tags()
        self.current_prompt.content = self._get_current_content()
        self.current_prompt.sensitive = bool(self.sensitive_var.get())
        self.current_prompt.update()
        self.on_save(self.current_prompt)

    def save_current_prompt(self) -> bool:
        """Save the current prompt and return True if saved."""
        if not self.current_prompt:
            return False
        self._on_save()
        return True

    def _on_delete(self):
        if self.current_prompt:
            self.on_delete(self.current_prompt.id)

    def _on_copy(self):
        content = self._get_current_content()
        if not content:
            return
        if not self._confirm_sensitive_copy("Copy"):
            return
        self.on_copy(content)

    def _on_toggle_pin(self):
        if not self.current_prompt:
            return
        self.on_toggle_pin(self.current_prompt)
        self._update_pin_button()

    def _on_show_history(self):
        if not self.current_prompt:
            return
        self.on_show_history(self.current_prompt)

    def _on_version_bump(self):
        if not self.current_prompt:
            return
        self.on_version_bump(self.current_prompt)

    def _copy_text(self, content: str, label: str):
        if not content:
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        self.on_toast(f"Copied as {label}")

    def _show_copy_as_menu(self):
        if self._copy_as_menu is None:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Plain text", command=lambda: self._copy_as("plain"))
            menu.add_command(label="Markdown code block", command=lambda: self._copy_as("markdown"))
            menu.add_command(label="JSON object", command=lambda: self._copy_as("json"))
            self._copy_as_menu = menu
        x = self.copy_as_btn.winfo_rootx()
        y = self.copy_as_btn.winfo_rooty() + self.copy_as_btn.winfo_height()
        self._copy_as_menu.tk_popup(x, y)

    def _copy_as(self, mode: str):
        content = self._get_current_content()
        if not content:
            return
        if not self._confirm_sensitive_copy("Copy"):
            return
        if mode == "markdown":
            text = f"```\n{content}\n```"
            self._copy_text(text, "Markdown")
            return
        if mode == "json":
            data = {
                "name": self.name_entry.get().strip(),
                "category": self.category_var.get(),
                "tags": self.tags_input.get_tags(),
                "sensitive": bool(self.sensitive_var.get()),
                "pinned": bool(self.current_prompt.pinned) if self.current_prompt else False,
                "content": content,
            }
            text = json.dumps(data, ensure_ascii=False, indent=2)
            self._copy_text(text, "JSON")
            return
        self._copy_text(content, "plain text")

    def _show_format_menu(self):
        if self._format_menu is None:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Trim trailing spaces", command=self._trim_trailing_spaces)
            menu.add_command(label="Normalize line endings (LF)", command=self._normalize_line_endings)
            self._format_menu = menu
        x = self.format_btn.winfo_rootx()
        y = self.format_btn.winfo_rooty() + self.format_btn.winfo_height()
        self._format_menu.tk_popup(x, y)

    def _set_content(self, content: str):
        self._set_current_content(content)

    def _trim_trailing_spaces(self):
        content = self._get_current_content()
        if not content:
            return
        lines = content.splitlines()
        trimmed = "\n".join([line.rstrip() for line in lines])
        if content.endswith("\n"):
            trimmed += "\n"
        self._set_content(trimmed)

    def _normalize_line_endings(self):
        content = self._get_current_content()
        if not content:
            return
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        self._set_content(normalized)

    def is_content_focused(self, widget) -> bool:
        if widget is None:
            return False
        inner = getattr(self.content_text, "_textbox", None)
        return widget == self.content_text or widget == inner

    def open_find_dialog(self):
        if self._find_dialog and self._find_dialog.winfo_exists():
            self._find_dialog.focus()
            return
        self._find_dialog = FindReplaceDialog(
            self,
            colors=self.colors,
            on_find=self._handle_find,
            show_replace=False,
        )

    def open_replace_dialog(self):
        if self._replace_dialog and self._replace_dialog.winfo_exists():
            self._replace_dialog.focus()
            return
        self._replace_dialog = FindReplaceDialog(
            self,
            colors=self.colors,
            on_find=self._handle_find,
            on_replace=self._handle_replace,
            on_replace_all=self._handle_replace_all,
            show_replace=True,
        )

    def _get_text_widget(self):
        return getattr(self.content_text, "_textbox", self.content_text)

    def _handle_find(self, query: str) -> bool:
        found = self._find_next(query)
        if not found:
            self.on_toast("No matches found")
        return found

    def _find_next(self, query: str) -> bool:
        if not query:
            return False
        text_widget = self._get_text_widget()
        start = text_widget.index("insert")
        idx = text_widget.search(query, start, nocase=True, stopindex="end")
        if not idx:
            idx = text_widget.search(query, "1.0", nocase=True, stopindex=start)
            if not idx:
                return False
        end = f"{idx}+{len(query)}c"
        text_widget.tag_remove("find_match", "1.0", "end")
        text_widget.tag_add("find_match", idx, end)
        text_widget.tag_config("find_match", background=self.colors["accent_glow"])
        text_widget.mark_set("insert", end)
        text_widget.see(idx)
        return True

    def _handle_replace(self, query: str, replacement: str) -> bool:
        if not query:
            return False
        text_widget = self._get_text_widget()
        ranges = text_widget.tag_ranges("find_match")
        if ranges:
            start, end = ranges[0], ranges[1]
            current = text_widget.get(start, end)
            if current.lower() == query.lower():
                text_widget.delete(start, end)
                text_widget.insert(start, replacement)
                text_widget.tag_remove("find_match", "1.0", "end")
                if self.current_prompt:
                    self.on_change()
                self._update_char_count()
                text_widget.mark_set("insert", f"{start}+{len(replacement)}c")
                return True
        if self._find_next(query):
            return self._handle_replace(query, replacement)
        self.on_toast("No matches found")
        return False

    def _handle_replace_all(self, query: str, replacement: str) -> int:
        if not query:
            return 0
        text_widget = self._get_text_widget()
        count = 0
        idx = text_widget.search(query, "1.0", nocase=True, stopindex="end")
        while idx:
            end = f"{idx}+{len(query)}c"
            text_widget.delete(idx, end)
            text_widget.insert(idx, replacement)
            count += 1
            idx = text_widget.search(query, f"{idx}+{len(replacement)}c", nocase=True, stopindex="end")
        if count:
            if self.current_prompt:
                self.on_change()
            self._update_char_count()
            self.on_toast(f"Replaced {count} matches")
        else:
            self.on_toast("No matches found")
        return count

    def _on_sensitive_toggle(self):
        if not self.current_prompt:
            return
        is_sensitive = bool(self.sensitive_var.get())
        if is_sensitive:
            self._hidden_content_cache = self._get_current_content()
            self._content_hidden = True
        else:
            self._hidden_content_cache = self._get_current_content()
            self._content_hidden = False
            if self._auto_hide_id is not None:
                try:
                    self.after_cancel(self._auto_hide_id)
                except Exception:
                    pass
                self._auto_hide_id = None
        self._apply_sensitive_view()
        self.on_change()

    def _toggle_reveal(self):
        if not self.current_prompt or not self.sensitive_var.get():
            return
        if self._content_hidden:
            self._content_hidden = False
        else:
            self._hidden_content_cache = self._get_current_content()
            self._content_hidden = True
        self._schedule_auto_hide()
        self._apply_sensitive_view()

    def _apply_sensitive_view(self):
        if self._content_hidden:
            self._hidden_content_cache = self._hidden_content_cache or self._get_current_content()
            self.content_text.configure(state="normal")
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", self._obfuscate_content(self._hidden_content_cache))
            self.content_text.configure(state="disabled")
            self.reveal_btn.configure(text="Reveal", state="normal")
        else:
            self.content_text.configure(state="normal")
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", self._hidden_content_cache)
            self.reveal_btn.configure(text="Hide" if self.sensitive_var.get() else "Reveal")
        if not self.sensitive_var.get():
            self.reveal_btn.configure(state="disabled")
        self._update_char_count()

    def _get_current_content(self) -> str:
        if self._content_hidden:
            return self._hidden_content_cache
        return self.content_text.get("1.0", "end-1c")

    def _set_current_content(self, content: str):
        if self._content_hidden:
            self._hidden_content_cache = content
            self._apply_sensitive_view()
            if self.current_prompt:
                self.on_change()
            return
        self.content_text.configure(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", content)
        if self.current_prompt:
            self.on_change()
        self._update_char_count()
        self._schedule_auto_hide()

    def _confirm_sensitive_copy(self, action: str) -> bool:
        if not self.current_prompt or not self.sensitive_var.get():
            return True
        if PromptEditor._sensitive_copy_warned:
            return True
        dialog = ConfirmDialog(
            self,
            colors=self.colors,
            title="Sensitive content",
            message=f"This prompt is marked sensitive. {action} to clipboard anyway?",
            confirm_text="Copy",
            cancel_text="Cancel",
        )
        self.wait_window(dialog)
        PromptEditor._sensitive_copy_warned = True
        return dialog.result == "confirm"

    def confirm_sensitive_copy(self, action: str = "Copy") -> bool:
        return self._confirm_sensitive_copy(action)

    def _schedule_auto_hide(self):
        if self._auto_hide_id is not None:
            try:
                self.after_cancel(self._auto_hide_id)
            except Exception:
                pass
            self._auto_hide_id = None
        if not self.sensitive_var.get():
            return
        if self._content_hidden:
            return
        self._auto_hide_id = self.after(self._auto_hide_after_ms, self._auto_hide)

    def _auto_hide(self):
        self._auto_hide_id = None
        if not self.sensitive_var.get():
            return
        if self._content_hidden:
            return
        self._hidden_content_cache = self._get_current_content()
        self._content_hidden = True
        self._apply_sensitive_view()

    def _obfuscate_content(self, content: str) -> str:
        if not content:
            return ""
        return "".join("\n" if ch == "\n" else "•" for ch in content)

    def _test_in_ai(self, service: str):
        content = self._get_current_content().strip()
        if not content:
            return
        if not self._confirm_sensitive_copy("Copy"):
            return

        brave_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ]
        
        browser_exe = None
        for path in brave_paths:
            if os.path.exists(path):
                browser_exe = path
                break

        urls = {
            "gemini": "https://gemini.google.com/app",
            "chatgpt": "https://chatgpt.com/",
            "grok": "https://grok.com/",
        }
        url = urls.get(service, urls["gemini"])

        def maybe_auto_paste():
            if os.environ.get("PROMPTLIB_AUTOPASTE") != "1":
                return
            try:
                import pyautogui
            except ImportError:
                return

            def paste():
                time.sleep(2)
                try:
                    pyautogui.hotkey("ctrl", "v")
                except Exception:
                    pass

            threading.Thread(target=paste, daemon=True).start()

        def open_url():
            try:
                if browser_exe:
                    subprocess.Popen([browser_exe, url])
                else:
                    import webbrowser
                    webbrowser.open(url)
            except Exception:
                return False
            return True

        self.clipboard_clear()
        self.clipboard_append(content)
        opened = open_url()
        if opened:
            maybe_auto_paste()
        self.on_toast("Copied; paste when ready")
