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
from .dialogs import (
    FindReplaceDialog,
    ConfirmDialog,
    VariableInputDialog,
    SnippetPickerDialog,
    TagInputDialog,
)
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
        on_autosave_draft: Callable[[str, dict], None],
        colors: Dict[str, str],
        on_preview_toggle: Optional[Callable[[bool], None]] = None,
        preview_enabled: bool = False,
        token_mode: str = "approx",
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
        self.on_autosave_draft = on_autosave_draft
        self.on_preview_toggle = on_preview_toggle
        self.colors = colors
        self.preview_enabled = bool(preview_enabled)
        self.token_mode = token_mode
        self.current_prompt: Optional[Prompt] = None
        self.custom_category = ""
        self._suppress_category_prompt = False
        self._pin_symbol = "\u2606"
        self._find_dialog: Optional[FindReplaceDialog] = None
        self._replace_dialog: Optional[FindReplaceDialog] = None
        self._format_menu: Optional[tk.Menu] = None
        self._copy_as_menu: Optional[tk.Menu] = None
        self._content_hidden = False
        self._hidden_content_cache = ""
        self._auto_hide_after_ms = 60000
        self._auto_hide_id = None
        self._draft_autosave_after_id = None
        self._snippet_dialog: Optional[SnippetPickerDialog] = None
        self.default_snippets = [
            {
                "name": "Role + Goals",
                "category": "Structure",
                "content": "## Role\nYou are ...\n\n## Goal\n...\n\n## Constraints\n- ...",
            },
            {
                "name": "Output schema",
                "category": "Structure",
                "content": "Return JSON:\n{\n  \"summary\": \"\",\n  \"actions\": []\n}",
            },
            {
                "name": "Few-shot block",
                "category": "Examples",
                "content": "### Example 1\nInput: ...\nOutput: ...\n\n### Example 2\nInput: ...\nOutput: ...",
            },
            {
                "name": "Variable starter",
                "category": "Variables",
                "content": "Project: {project}\nAudience: {audience}\nTone: {tone}\nDeliverable: {deliverable}",
            },
        ]

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

        # Right: primary actions + compact controls
        right_frame = ctk.CTkFrame(header, fg_color="transparent")
        right_frame.pack(side="right", fill="y")

        self.ai_provider_var = ctk.StringVar(value="Gemini")
        self.ai_provider_menu = ctk.CTkOptionMenu(
            right_frame,
            values=["Gemini", "GPT", "Grok"],
            variable=self.ai_provider_var,
            width=90,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=colors["surface"],
            text_color=colors["text_secondary"],
            button_color=colors["surface"],
            button_hover_color=colors["bg"],
            dropdown_fg_color=colors["surface"],
            dropdown_text_color=colors["text_primary"],
            dropdown_hover_color=colors["accent_glow"],
            corner_radius=10,
        )
        self.ai_provider_menu.pack(side="left", pady=10, padx=(0, 8))

        self.open_ai_btn = ctk.CTkButton(
            right_frame,
            text="Open in AI",
            width=84,
            height=28,
            **self._btn_secondary_style(size=11, weight="normal", radius=10),
            command=self._open_in_selected_ai,
        )
        self.open_ai_btn.pack(side="left", pady=10, padx=(0, 8))

        # Copy button
        self.copy_btn = ctk.CTkButton(
            right_frame,
            text="Copy",
            width=52,
            height=28,
            **self._btn_secondary_style(size=11, weight="bold", radius=10),
            command=self._on_copy,
        )
        self.copy_btn.pack(side="left", pady=10)

        self.preview_btn = ctk.CTkButton(
            right_frame,
            text="Preview",
            width=70,
            height=28,
            **self._btn_secondary_style(
                size=11,
                weight="normal",
                radius=10,
                fg_color=self.colors["accent_glow"] if self.preview_enabled else self.colors["surface"],
                text_color=self.colors["accent"] if self.preview_enabled else self.colors["text_secondary"],
            ),
            command=self._on_preview_button,
        )
        self.preview_btn.pack(side="left", padx=(8, 0), pady=10)

        self.overflow_btn = ctk.CTkButton(
            right_frame,
            text="\u22ef",
            width=34,
            height=28,
            **self._btn_secondary_style(size=14, weight="bold", radius=10),
            command=self._show_overflow_menu,
        )
        self.overflow_btn.pack(side="left", padx=(8, 0), pady=10)

        # ========== CONTENT (Expandable) ==========
        content = ctk.CTkFrame(self.card, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=24, pady=12)
        
        # Grid layout for form - content expands
        content.grid_columnconfigure(0, weight=0)  # Category column
        content.grid_columnconfigure(1, weight=1)  # Tags + content column
        content.grid_rowconfigure(0, weight=0)  # Name row
        content.grid_rowconfigure(1, weight=0)  # Category + tags row
        content.grid_rowconfigure(2, weight=0)  # Content label
        content.grid_rowconfigure(3, weight=1)  # Content text (EXPANDS!)

        # Row 0: Name (full width)
        name_frame = ctk.CTkFrame(content, fg_color="transparent")
        name_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        
        ctk.CTkLabel(
            name_frame, text="NAME",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=colors["text_muted"],
        ).pack(anchor="w", pady=(0, 4))
        
        self.name_entry = ctk.CTkEntry(
            name_frame, height=42,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=colors["surface"], border_color=colors["border"],
            border_width=1, corner_radius=12, text_color=colors["text_primary"],
        )
        self.name_entry.pack(fill="x")
        self.name_entry.bind("<KeyRelease>", self._on_field_change)

        # Row 1 (left): Category
        cat_frame = ctk.CTkFrame(content, fg_color="transparent")
        cat_frame.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 12))
        
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
            command=self._on_category_change,
        )
        self.category_dropdown.pack(fill="x", padx=1, pady=1)

        self.custom_category_label = ctk.CTkLabel(
            cat_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=colors["text_muted"],
            anchor="w",
        )
        self.custom_category_label.pack(fill="x", pady=(4, 0))

        # Row 1 (right): Tags
        tags_frame = ctk.CTkFrame(content, fg_color="transparent")
        tags_frame.grid(row=1, column=1, sticky="ew", pady=(0, 12))
        
        ctk.CTkLabel(
            tags_frame, text="TAGS",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=colors["text_muted"],
        ).pack(anchor="w", pady=(0, 4))
        
        self.tags_input = TagChipsInput(
            tags_frame,
            colors=colors,
            on_change=self._on_field_change,
            placeholder_text="Add tags (comma or Enter)...",
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
            **self._btn_secondary_style(size=10, weight="normal", radius=8),
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

        self.preview_text = ctk.CTkTextbox(
            content,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=colors["bg"],
            text_color=colors["text_secondary"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=10,
            wrap="word",
        )

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

        # Save button
        self.save_btn = ctk.CTkButton(
            footer_inner, text="Save", width=90, height=36,
            **self._btn_primary_style(size=13, weight="bold", radius=10),
            command=self._on_save,
        )
        self.save_btn.pack(side="right", pady=12)

        self._apply_preview_layout()
        self._refresh_preview()

    def _btn_secondary_style(
        self,
        *,
        size: int = 11,
        weight: str = "normal",
        radius: int = 10,
        fg_color: Optional[str] = None,
        text_color: Optional[str] = None,
        hover_color: Optional[str] = None,
    ) -> dict:
        return {
            "corner_radius": radius,
            "font": ctk.CTkFont(family="Segoe UI", size=size, weight=weight),
            "fg_color": fg_color or self.colors["surface"],
            "hover_color": hover_color or self.colors["border"],
            "text_color": text_color or self.colors["text_secondary"],
            "border_width": 1,
            "border_color": self.colors["border"],
        }

    def _btn_primary_style(self, *, size: int = 12, weight: str = "bold", radius: int = 10) -> dict:
        return {
            "corner_radius": radius,
            "font": ctk.CTkFont(family="Segoe UI", size=size, weight=weight),
            "fg_color": self.colors["accent"],
            "hover_color": self.colors["accent_hover"],
        }

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
        self._suppress_category_prompt = True
        self.category_var.set(prompt.category.value)
        self._suppress_category_prompt = False
        self.custom_category = (getattr(prompt, "custom_category", "") or "").strip()
        self._update_custom_category_label()
        self.tags_input.set_tags(prompt.tags)
        self.sensitive_var.set(bool(prompt.sensitive))
        self._hidden_content_cache = prompt.content
        self._content_hidden = bool(prompt.sensitive)
        self._schedule_auto_hide()
        self._apply_sensitive_view()

        self._update_pin_button()
        self._update_state_label()
        self._update_char_count()
        self._refresh_preview()

    def set_draft(self, draft: dict):
        if not self.current_prompt:
            return
        name = str(draft.get("name", self.current_prompt.name))
        category = str(draft.get("category", self.current_prompt.category.value))
        tags = draft.get("tags", self.current_prompt.tags)
        content = str(draft.get("content", self.current_prompt.content))
        sensitive = bool(draft.get("sensitive", self.current_prompt.sensitive))
        custom_category = str(
            draft.get(
                "custom_category",
                getattr(self.current_prompt, "custom_category", ""),
            )
            or ""
        )

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, name)
        self._suppress_category_prompt = True
        if category in [c.value for c in Category]:
            self.category_var.set(category)
        else:
            self.category_var.set(Category.OTHER.value)
        self._suppress_category_prompt = False
        self.custom_category = custom_category.strip()
        self._update_custom_category_label()
        self.tags_input.set_tags(list(tags) if isinstance(tags, list) else [])
        self.sensitive_var.set(sensitive)
        self._content_hidden = bool(sensitive)
        self._hidden_content_cache = content
        self._apply_sensitive_view()
        self._refresh_preview()

    def toggle_preview(self):
        self.preview_enabled = not self.preview_enabled
        self._apply_preview_layout()
        self._refresh_preview()

    def _on_preview_button(self):
        self.toggle_preview()
        if self.on_preview_toggle:
            self.on_preview_toggle(self.preview_enabled)

    def _apply_preview_layout(self):
        if self.preview_enabled:
            self.content_text.grid_configure(column=0, columnspan=1)
            self.preview_text.grid(row=3, column=1, columnspan=2, sticky="nsew", padx=(10, 0))
            self.preview_btn.configure(
                fg_color=self.colors["accent_glow"],
                text_color=self.colors["accent"],
                text="Preview On",
            )
        else:
            self.preview_text.grid_forget()
            self.content_text.grid_configure(column=0, columnspan=2)
            self.preview_btn.configure(
                fg_color=self.colors["surface"],
                text_color=self.colors["text_secondary"],
                text="Preview",
            )

    def _render_markdown_preview(self, content: str) -> str:
        lines: list[str] = []
        for raw in content.splitlines():
            line = raw.rstrip()
            if line.startswith("### "):
                lines.append(f"[H3] {line[4:]}")
            elif line.startswith("## "):
                lines.append(f"[H2] {line[3:]}")
            elif line.startswith("# "):
                lines.append(f"[H1] {line[2:]}")
            elif line.startswith("- "):
                lines.append(f"• {line[2:]}")
            elif line.startswith("```"):
                lines.append("[code block]")
            else:
                lines.append(line)
        return "\n".join(lines)

    def _refresh_preview(self):
        content = self._get_current_content()
        rendered = self._render_markdown_preview(content)
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", rendered)
        self.preview_text.configure(state="disabled")

    def _update_pin_button(self):
        if not self.current_prompt:
            self._pin_symbol = "\u2606"
            return
        if self.current_prompt.pinned:
            self._pin_symbol = "\u2605"
        else:
            self._pin_symbol = "\u2606"

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
        self.custom_category = ""
        self._update_custom_category_label()
        self.card.grid_forget()
        self.empty_frame.grid(row=0, column=0, sticky="nsew")

    def get_tags(self) -> list[str]:
        return self.tags_input.get_tags()

    def set_tags(self, tags: list[str], notify: bool = False):
        self.tags_input.set_tags(tags, notify=notify)

    def _on_category_change(self, selected: str):
        if self._suppress_category_prompt:
            return
        if selected == Category.OTHER.value:
            self._prompt_custom_category()
        else:
            self.custom_category = ""
        self._update_custom_category_label()
        self._on_field_change()

    def _prompt_custom_category(self):
        previous = self.custom_category
        dialog = TagInputDialog(
            self,
            colors=self.colors,
            title="Custom category",
            confirm_text="Use",
        )
        self.wait_window(dialog)
        if dialog.result is None:
            self.custom_category = previous
            return
        self.custom_category = (dialog.result or "").strip()

    def _update_custom_category_label(self):
        if self.category_var.get() == Category.OTHER.value and self.custom_category:
            self.custom_category_label.configure(text=f"Custom: {self.custom_category}")
        elif self.category_var.get() == Category.OTHER.value:
            self.custom_category_label.configure(text="Custom: (not set)")
        else:
            self.custom_category_label.configure(text="")

    def _on_field_change(self, event=None):
        if self.current_prompt:
            self.on_change()
            self._update_char_count()

    def _on_save(self):
        if not self.current_prompt:
            return
        self.current_prompt.name = self.name_entry.get().strip()
        self.current_prompt.category = Category(self.category_var.get())
        self.current_prompt.custom_category = (
            self.custom_category.strip()
            if self.current_prompt.category == Category.OTHER
            else ""
        )
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

    def _open_in_selected_ai(self):
        provider = (self.ai_provider_var.get() or "Gemini").strip().lower()
        provider_map = {
            "gemini": "gemini",
            "gpt": "chatgpt",
            "chatgpt": "chatgpt",
            "grok": "grok",
        }
        self._test_in_ai(provider_map.get(provider, "gemini"))

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

    def _show_overflow_menu(self):
        menu = tk.Menu(self, tearoff=0)
        pin_label = "Unpin prompt" if self.current_prompt and self.current_prompt.pinned else "Pin prompt"
        menu.add_command(label=pin_label, command=self._on_toggle_pin)
        menu.add_separator()
        menu.add_command(label="Copy as...", command=lambda: self._show_copy_as_menu(anchor=self.overflow_btn))
        menu.add_command(label="Insert snippet", command=self.open_snippet_picker)
        menu.add_command(label="Fill variables", command=self.fill_variables)
        menu.add_separator()
        menu.add_command(label="Format...", command=lambda: self._show_format_menu(anchor=self.overflow_btn))
        menu.add_command(label="Create new version", command=self._on_version_bump)
        menu.add_command(label="History", command=self._on_show_history)
        menu.add_separator()
        menu.add_command(label="Delete", command=self._on_delete)
        x = self.overflow_btn.winfo_rootx()
        y = self.overflow_btn.winfo_rooty() + self.overflow_btn.winfo_height()
        menu.tk_popup(x, y)
        menu.grab_release()

    def _show_copy_as_menu(self, anchor=None):
        if self._copy_as_menu is None:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Plain text", command=lambda: self._copy_as("plain"))
            menu.add_command(label="Markdown code block", command=lambda: self._copy_as("markdown"))
            menu.add_command(label="JSON object", command=lambda: self._copy_as("json"))
            self._copy_as_menu = menu
        anchor_widget = anchor or self.overflow_btn
        x = anchor_widget.winfo_rootx()
        y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height()
        self._copy_as_menu.tk_popup(x, y)
        self._copy_as_menu.grab_release()

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
                "custom_category": self.custom_category.strip(),
                "tags": self.tags_input.get_tags(),
                "sensitive": bool(self.sensitive_var.get()),
                "pinned": bool(self.current_prompt.pinned) if self.current_prompt else False,
                "content": content,
            }
            text = json.dumps(data, ensure_ascii=False, indent=2)
            self._copy_text(text, "JSON")
            return
        self._copy_text(content, "plain text")

    def open_snippet_picker(self):
        if self._snippet_dialog and self._snippet_dialog.winfo_exists():
            self._snippet_dialog.focus_set()
            return
        self._snippet_dialog = SnippetPickerDialog(
            self,
            snippets=self.default_snippets,
            colors=self.colors,
            on_insert=self.insert_snippet,
        )

    def insert_snippet(self, text: str):
        if not text:
            return
        textbox = getattr(self.content_text, "_textbox", self.content_text)
        try:
            if textbox.tag_ranges("sel"):
                start = textbox.index("sel.first")
                end = textbox.index("sel.last")
                textbox.delete(start, end)
                textbox.insert(start, text)
                textbox.mark_set("insert", f"{start}+{len(text)}c")
            else:
                textbox.insert("insert", text)
        except Exception:
            textbox.insert("insert", text)
        self._on_field_change()

    def fill_variables(self):
        content = self._get_current_content()
        placeholders = sorted({m.group(1) for m in re.finditer(r"\{([a-zA-Z0-9_\-]+)\}", content)})
        if not placeholders:
            self.on_toast("No {variables} found")
            return

        def handle(values: Dict[str, str]):
            updated = content
            for key, value in values.items():
                replacement = value if value else "{" + key + "}"
                updated = updated.replace("{" + key + "}", replacement)
            self._set_content(updated)

        VariableInputDialog(self, variables=placeholders, on_submit=handle, colors=self.colors)

    def _show_format_menu(self, anchor=None):
        if self._format_menu is None:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Trim trailing spaces", command=self._trim_trailing_spaces)
            menu.add_command(label="Normalize line endings (LF)", command=self._normalize_line_endings)
            self._format_menu = menu
        anchor_widget = anchor or self.overflow_btn
        x = anchor_widget.winfo_rootx()
        y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height()
        self._format_menu.tk_popup(x, y)
        self._format_menu.grab_release()

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

    # Rich Markdown preview renderer (human-friendly reading mode).
    def _configure_preview_tags(self, text_widget):
        text_widget.tag_configure("md_h1", font=("Segoe UI", 18, "bold"), foreground=self.colors["text_primary"], spacing1=8, spacing3=4)
        text_widget.tag_configure("md_h2", font=("Segoe UI", 15, "bold"), foreground=self.colors["text_primary"], spacing1=6, spacing3=4)
        text_widget.tag_configure("md_h3", font=("Segoe UI", 13, "bold"), foreground=self.colors["text_primary"], spacing1=4, spacing3=2)
        text_widget.tag_configure("md_body", font=("Segoe UI", 12), foreground=self.colors["text_secondary"])
        text_widget.tag_configure("md_bold", font=("Segoe UI", 12, "bold"))
        text_widget.tag_configure("md_italic", font=("Segoe UI", 12, "italic"))
        text_widget.tag_configure("md_inline_code", font=("Consolas", 11), background=self.colors["accent_glow"], foreground=self.colors["text_primary"])
        text_widget.tag_configure("md_code_block", font=("Consolas", 11), background=self.colors["surface"], foreground=self.colors["text_primary"], lmargin1=14, lmargin2=14, spacing1=4, spacing3=4)
        text_widget.tag_configure("md_quote", foreground=self.colors["text_muted"], lmargin1=12, lmargin2=12)
        text_widget.tag_configure("md_link", foreground=self.colors["accent"], underline=True)
        text_widget.tag_configure("md_bullet", foreground=self.colors["text_secondary"], lmargin1=8, lmargin2=20)

    def _insert_markdown_inline(self, text_widget, text: str, default_tag: str):
        token_pattern = re.compile(r"(\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`|\[[^\]]+\]\([^)]+\))")
        pos = 0
        for match in token_pattern.finditer(text):
            start, end = match.span()
            if start > pos:
                text_widget.insert("end", text[pos:start], (default_tag,))
            token = match.group(0)
            if token.startswith("**") and token.endswith("**"):
                text_widget.insert("end", token[2:-2], ("md_bold",))
            elif token.startswith("*") and token.endswith("*"):
                text_widget.insert("end", token[1:-1], ("md_italic",))
            elif token.startswith("`") and token.endswith("`"):
                text_widget.insert("end", token[1:-1], ("md_inline_code",))
            else:
                link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", token)
                if link_match:
                    text_widget.insert("end", f"{link_match.group(1)} ({link_match.group(2)})", ("md_link",))
                else:
                    text_widget.insert("end", token, (default_tag,))
            pos = end
        if pos < len(text):
            text_widget.insert("end", text[pos:], (default_tag,))

    def _refresh_preview(self):
        content = self._get_current_content()
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        text_widget = getattr(self.preview_text, "_textbox", self.preview_text)
        self._configure_preview_tags(text_widget)

        in_code_block = False
        for raw_line in content.splitlines():
            line = raw_line.rstrip("\r")
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                text_widget.insert("end", line + "\n", ("md_code_block",))
                continue

            h_match = re.match(r"^(#{1,3})\s+(.*)$", line)
            if h_match:
                level = len(h_match.group(1))
                tag = "md_h1" if level == 1 else "md_h2" if level == 2 else "md_h3"
                self._insert_markdown_inline(text_widget, h_match.group(2).strip(), tag)
                text_widget.insert("end", "\n")
                continue

            q_match = re.match(r"^>\s?(.*)$", line)
            if q_match:
                self._insert_markdown_inline(text_widget, q_match.group(1), "md_quote")
                text_widget.insert("end", "\n")
                continue

            ul_match = re.match(r"^\s*[-*+]\s+(.*)$", line)
            if ul_match:
                text_widget.insert("end", "• ", ("md_bullet",))
                self._insert_markdown_inline(text_widget, ul_match.group(1), "md_bullet")
                text_widget.insert("end", "\n")
                continue

            ol_match = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
            if ol_match:
                text_widget.insert("end", f"{ol_match.group(1)}. ", ("md_bullet",))
                self._insert_markdown_inline(text_widget, ol_match.group(2), "md_bullet")
                text_widget.insert("end", "\n")
                continue

            if not line.strip():
                text_widget.insert("end", "\n")
                continue

            self._insert_markdown_inline(text_widget, line, "md_body")
            text_widget.insert("end", "\n")

        self.preview_text.configure(state="disabled")

    # Override for throughput mode: autosave drafts + preview refresh + token counts.
    def _update_char_count(self):
        content = self._get_current_content()
        chars = len(content)
        words = len(re.findall(r"\S+", content))
        lines = 0 if not content else content.count("\n") + 1
        approx_tokens = self._estimate_tokens(content)
        token_text = f"{approx_tokens:,} tok~"
        if self.token_mode == "exact":
            exact = self._exact_tokens(content)
            if exact is not None:
                token_text = f"{exact:,} tok"
        self.char_count_label.configure(
            text=f"{chars:,} chars | {words:,} words | {lines:,} lines | {token_text}"
        )

    def _estimate_tokens(self, content: str) -> int:
        if not content:
            return 0
        return max(1, round(len(content) / 4))

    def _exact_tokens(self, content: str) -> Optional[int]:
        tokenizer = os.environ.get("PROMPTLIB_TOKENIZER", "").strip().lower()
        if tokenizer != "tiktoken":
            return None
        try:
            import tiktoken  # type: ignore

            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(content))
        except Exception:
            return None

    def _on_field_change(self, event=None):
        if self.current_prompt:
            self.on_change()
            self._update_char_count()
            self._refresh_preview()
            self._schedule_draft_autosave()

    def _schedule_draft_autosave(self):
        if not self.current_prompt:
            return
        if self._draft_autosave_after_id is not None:
            try:
                self.after_cancel(self._draft_autosave_after_id)
            except Exception:
                pass
            self._draft_autosave_after_id = None
        self._draft_autosave_after_id = self.after(450, self._autosave_draft_now)

    def _autosave_draft_now(self):
        self._draft_autosave_after_id = None
        if not self.current_prompt:
            return
        draft = {
            "name": self.name_entry.get().strip(),
            "category": self.category_var.get(),
            "custom_category": self.custom_category.strip(),
            "tags": self.tags_input.get_tags(),
            "content": self._get_current_content(),
            "sensitive": bool(self.sensitive_var.get()),
        }
        self.on_autosave_draft(self.current_prompt.id, draft)

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
        self._refresh_preview()

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
                self._schedule_draft_autosave()
            return
        self.content_text.configure(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", content)
        if self.current_prompt:
            self.on_change()
            self._schedule_draft_autosave()
        self._update_char_count()
        self._refresh_preview()
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
