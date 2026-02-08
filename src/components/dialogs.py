"""Dialog components - Apple 2026 Edition."""
import customtkinter as ctk
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

from ..models import Prompt, Category
from .tag_chips import TagChipsInput


class ModalDialog(ctk.CTkToplevel):
    """Shared modal behavior for consistent popup feel."""

    def _init_modal(
        self,
        master,
        colors: Dict[str, str],
        *,
        title: str,
        width: int,
        height: int,
        resizable: tuple[bool, bool] = (False, False),
        fade_in: bool = True,
    ):
        self.colors = colors
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(resizable[0], resizable[1])
        self.configure(fg_color=colors["bg"])
        self._fade_job = None
        self._alpha_supported = False
        if fade_in:
            try:
                self.attributes("-alpha", 0.0)
                self._alpha_supported = True
            except Exception:
                self._alpha_supported = False

        self.transient(master)
        self.grab_set()
        self._center_on_screen(width, height)
        self._start_fade_in()

    def _center_on_screen(self, width: int, height: int, margin: int = 40):
        screen_w = int(self.winfo_screenwidth())
        screen_h = int(self.winfo_screenheight())
        width = max(320, min(width, max(320, screen_w - margin)))
        height = max(220, min(height, max(220, screen_h - margin)))
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _auto_size_and_center(self, min_width: int = 560, min_height: int = 560, margin: int = 40):
        self.update_idletasks()
        req_w = max(min_width, int(self.winfo_reqwidth()))
        req_h = max(min_height, int(self.winfo_reqheight()))
        screen_w = int(self.winfo_screenwidth())
        screen_h = int(self.winfo_screenheight())
        max_w = max(360, screen_w - margin)
        max_h = max(320, screen_h - margin)
        width = min(req_w, max_w)
        height = min(req_h, max_h)
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _start_fade_in(self):
        if not getattr(self, "_alpha_supported", False):
            return
        self._animate_alpha(0.0)

    def _animate_alpha(self, value: float):
        if not self.winfo_exists():
            return
        next_value = min(1.0, value + 0.14)
        try:
            self.attributes("-alpha", next_value)
        except Exception:
            return
        if next_value < 1.0:
            self._fade_job = self.after(16, lambda: self._animate_alpha(next_value))

    def _btn_secondary(
        self,
        parent,
        *,
        text: str,
        command: Callable,
        width: int = 96,
        height: int = 38,
    ) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            width=width,
            height=height,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=self.colors["border"],
            text_color=self.colors["text_secondary"],
            border_width=1,
            border_color=self.colors["border"],
            command=command,
        )

    def _btn_primary(
        self,
        parent,
        *,
        text: str,
        command: Callable,
        width: int = 96,
        height: int = 38,
    ) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            width=width,
            height=height,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            command=command,
        )

    def _btn_danger(
        self,
        parent,
        *,
        text: str,
        command: Callable,
        width: int = 96,
        height: int = 38,
    ) -> ctk.CTkButton:
        hover = "#3B1F24" if self.colors.get("bg", "").lower().startswith("#0") else "#FEE2E2"
        return ctk.CTkButton(
            parent,
            text=text,
            width=width,
            height=height,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=hover,
            text_color=self.colors["danger"],
            border_width=1,
            border_color=self.colors["border"],
            command=command,
        )

    def destroy(self):
        fade_job = getattr(self, "_fade_job", None)
        if fade_job is not None:
            try:
                self.after_cancel(fade_job)
            except Exception:
                pass
            self._fade_job = None
        super().destroy()


class NewPromptDialog(ModalDialog):
    """Dialog for creating a new prompt with Apple-style design."""

    def __init__(
        self,
        master,
        on_create: Callable[[Prompt], None],
        colors: Dict[str, str],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_create = on_create
        self.custom_category = ""
        self._suppress_category_prompt = False

        self._init_modal(
            master,
            colors,
            title="New Prompt",
            width=560,
            height=640,
            resizable=(False, False),
            fade_in=True,
        )

        # Card container
        card = ctk.CTkFrame(
            self,
            fg_color=colors["surface"],
            corner_radius=16,
        )
        card.pack(fill="both", expand=True, padx=14, pady=14)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=22, pady=20)

        # Title
        title = ctk.CTkLabel(
            content,
            text="Create New Prompt",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=colors["text_primary"],
        )
        title.pack(anchor="w", pady=(0, 16))

        # Name field
        name_label = ctk.CTkLabel(
            content,
            text="NAME",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["text_muted"],
            anchor="w",
        )
        name_label.pack(fill="x", pady=(0, 6), padx=4)

        self.name_entry = ctk.CTkEntry(
            content,
            height=42,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=12,
            text_color=colors["text_primary"],
            placeholder_text="Enter prompt name...",
        )
        self.name_entry.pack(fill="x", pady=(0, 14))

        # Category field
        cat_label = ctk.CTkLabel(
            content,
            text="CATEGORY",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["text_muted"],
            anchor="w",
        )
        cat_label.pack(fill="x", pady=(0, 6), padx=4)

        self.category_var = ctk.StringVar(value=Category.OTHER.value)
        # CTkOptionMenu doesn't render an entry-like border by default; wrap it.
        cat_outer = ctk.CTkFrame(
            content,
            fg_color=colors.get("input", colors["surface"]),
            corner_radius=12,
            border_width=1,
            border_color=colors["border"],
            height=46,
        )
        cat_outer.pack(fill="x", pady=(0, 6))
        cat_outer.pack_propagate(False)
        self.category_dropdown = ctk.CTkOptionMenu(
            cat_outer,
            values=[c.value for c in Category],
            variable=self.category_var,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=colors["surface"],
            text_color=colors["text_primary"],
            button_color=colors["surface"],
            button_hover_color=colors["bg"],
            dropdown_fg_color=colors["surface"],
            dropdown_text_color=colors["text_primary"],
            dropdown_hover_color=colors["accent_glow"],
            corner_radius=10,
            command=self._on_category_changed,
        )
        self.category_dropdown.pack(fill="both", expand=True, padx=2, pady=2)

        self.custom_category_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=colors["text_muted"],
            anchor="w",
        )
        self.custom_category_label.pack(fill="x", pady=(0, 10), padx=4)
        self._update_custom_category_label()

        # Tags field
        tags_label = ctk.CTkLabel(
            content,
            text="TAGS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["text_muted"],
            anchor="w",
        )
        tags_label.pack(fill="x", pady=(0, 6), padx=4)

        self.tags_input = TagChipsInput(
            content,
            colors=colors,
            placeholder_text="Add tags (comma or Enter)...",
        )
        self.tags_input.pack(fill="x", pady=(0, 14))

        # Content field
        content_label = ctk.CTkLabel(
            content,
            text="CONTENT",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["text_muted"],
            anchor="w",
        )
        content_label.pack(fill="x", pady=(0, 6), padx=4)

        self.content_text = ctk.CTkTextbox(
            content,
            height=160,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=colors["surface"],
            text_color=colors["text_primary"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=12,
            wrap="word",
        )
        self.content_text.pack(fill="x", pady=(0, 16))

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        cancel_btn = self._btn_secondary(btn_frame, text="Cancel", command=self.destroy, width=100, height=40)
        cancel_btn.pack(side="left")

        create_btn = self._btn_primary(btn_frame, text="Create", command=self._on_create, width=100, height=40)
        create_btn.pack(side="right")

        self._auto_size_and_center(min_width=560, min_height=560, margin=40)
        self.after(100, lambda: self.name_entry.focus())

    def _on_create(self):
        """Handle create."""
        name = self.name_entry.get().strip()
        content = self.content_text.get("1.0", "end-1c").strip()

        if not name or not content:
            return

        prompt = Prompt(
            name=name,
            content=content,
            category=Category(self.category_var.get()),
            tags=self.tags_input.get_tags(),
            custom_category=self.custom_category.strip()
            if self.category_var.get() == Category.OTHER.value
            else "",
        )

        self.on_create(prompt)
        self.destroy()

    def _on_category_changed(self, selected: str):
        if self._suppress_category_prompt:
            return
        if selected != Category.OTHER.value:
            self.custom_category = ""
            self._update_custom_category_label()
            return
        self._prompt_custom_category()

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
        self._update_custom_category_label()

    def _update_custom_category_label(self):
        if self.category_var.get() == Category.OTHER.value and self.custom_category:
            self.custom_category_label.configure(text=f"Custom: {self.custom_category}")
            self.custom_category_label.pack_configure(pady=(0, 10))
        elif self.category_var.get() == Category.OTHER.value:
            self.custom_category_label.configure(text="Custom: (click Other to set)")
            self.custom_category_label.pack_configure(pady=(0, 10))
        else:
            self.custom_category_label.configure(text="")
            self.custom_category_label.pack_configure(pady=(0, 0))

class VariableInputDialog(ModalDialog):
    """Dialog for entering values for prompt variables."""

    def __init__(
        self,
        master,
        variables: List[str],
        on_submit: Callable[[Dict[str, str]], None],
        colors: Dict[str, str],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_submit = on_submit
        self.variables = variables
        self.entries = {}

        height = min(600, 220 + len(variables) * 90)
        self._init_modal(
            master,
            colors,
            title="Variables Required",
            width=450,
            height=height,
            resizable=(True, True),
            fade_in=True,
        )

        # Card
        card = ctk.CTkFrame(
            self,
            fg_color=colors["surface"],
            corner_radius=16,
        )
        card.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_frame = ctk.CTkFrame(card, fg_color="transparent")
        title_frame.pack(fill="x", padx=28, pady=(28, 12))

        title = ctk.CTkLabel(
            title_frame,
            text="Fill in Variables",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=colors["text_primary"],
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="Please provide values for the placeholders.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=colors["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        # Scrollable inputs
        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=18, pady=12)

        first_entry = None

        for var in variables:
            frame = ctk.CTkFrame(scroll, fg_color="transparent")
            frame.pack(fill="x", pady=10)

            label = ctk.CTkLabel(
                frame,
                text=var.upper(),
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=colors["text_muted"],
                anchor="w",
            )
            label.pack(fill="x", pady=(0, 6), padx=4)
            
            entry = ctk.CTkEntry(
                frame,
                height=44,
                font=ctk.CTkFont(family="Segoe UI", size=14),
                fg_color=colors["surface"],
                border_color=colors["border"],
                border_width=1,
                corner_radius=12,
                text_color=colors["text_primary"],
                placeholder_text=f"Value for {var}..."
            )
            entry.pack(fill="x")
            self.entries[var] = entry
            
            if first_entry is None:
                first_entry = entry

        # Buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=28, pady=28)

        cancel_btn = self._btn_secondary(btn_frame, text="Cancel", command=self.destroy, width=100, height=40)
        cancel_btn.pack(side="left")

        submit_btn = self._btn_primary(btn_frame, text="Insert", command=self._on_submit, width=100, height=40)
        submit_btn.pack(side="right")
        
        if first_entry:
            self.after(100, lambda: first_entry.focus())
            
        self.bind("<Return>", lambda e: self._on_submit())
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_submit(self):
        """Collect values and callback."""
        values = {}
        for var, entry in self.entries.items():
            val = entry.get().strip()
            values[var] = val
            
        self.on_submit(values)
        self.destroy()


class SnippetPickerDialog(ModalDialog):
    """Dialog for searching and inserting snippets."""

    def __init__(
        self,
        master,
        snippets: List[dict],
        colors: Dict[str, str],
        on_insert: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_insert = on_insert
        self.all_snippets = snippets
        self.filtered: List[dict] = []
        self.result_buttons: List[ctk.CTkButton] = []
        self.active_index = 0

        self._init_modal(
            master,
            colors,
            title="Insert Snippet",
            width=620,
            height=520,
            resizable=(False, False),
            fade_in=True,
        )

        card = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=16)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            content,
            text="Snippets",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=colors["text_primary"],
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            content,
            text="Search and press Enter to insert at cursor.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["text_secondary"],
        ).pack(anchor="w", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            content,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=10,
            text_color=colors["text_primary"],
            placeholder_text="Search snippets by name/category/content...",
        )
        self.search_entry.pack(fill="x", pady=(0, 12))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        self.results_frame = ctk.CTkScrollableFrame(content, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", self._on_enter)
        self.bind("<Up>", self._on_up)
        self.bind("<Down>", self._on_down)

        self.search_entry.focus_set()
        self._apply_filter("")

    def _on_search(self, _event=None):
        self._apply_filter(self.search_entry.get())

    def _apply_filter(self, term: str):
        term = term.strip().lower()
        if not term:
            self.filtered = list(self.all_snippets)
        else:
            self.filtered = [
                s
                for s in self.all_snippets
                if term in str(s.get("name", "")).lower()
                or term in str(s.get("category", "")).lower()
                or term in str(s.get("content", "")).lower()
            ]
        self._rebuild_results()

    def _rebuild_results(self):
        for child in self.results_frame.winfo_children():
            child.destroy()
        self.result_buttons.clear()

        if not self.filtered:
            ctk.CTkLabel(
                self.results_frame,
                text="No snippets found.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=self.colors["text_muted"],
            ).pack(pady=16)
            self.active_index = 0
            return

        for idx, snippet in enumerate(self.filtered):
            name = str(snippet.get("name", "Snippet"))
            category = str(snippet.get("category", "General"))
            first_line = next(
                (line.strip() for line in str(snippet.get("content", "")).splitlines() if line.strip()),
                "",
            )
            if len(first_line) > 72:
                first_line = first_line[:71].rstrip() + "..."
            label = f"{name} | {category}"
            if first_line:
                label = f"{label} | {first_line}"

            btn = ctk.CTkButton(
                self.results_frame,
                text=label,
                height=38,
                corner_radius=8,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold" if idx == 0 else "normal"),
                fg_color=self.colors["accent_glow"] if idx == 0 else self.colors["surface"],
                hover_color=self.colors["border"],
                text_color=self.colors["text_primary"],
                anchor="w",
                command=lambda s=snippet: self._insert(s),
            )
            btn.pack(fill="x", pady=4, padx=4)
            self.result_buttons.append(btn)

        self.active_index = 0
        self._highlight_active()

    def _highlight_active(self):
        for i, btn in enumerate(self.result_buttons):
            if i == self.active_index:
                btn.configure(
                    fg_color=self.colors["accent_glow"],
                    text_color=self.colors["text_primary"],
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color=self.colors["surface"],
                    text_color=self.colors["text_secondary"],
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                )

    def _on_up(self, _event=None):
        if not self.filtered:
            return "break"
        self.active_index = max(0, self.active_index - 1)
        self._highlight_active()
        return "break"

    def _on_down(self, _event=None):
        if not self.filtered:
            return "break"
        self.active_index = min(len(self.filtered) - 1, self.active_index + 1)
        self._highlight_active()
        return "break"

    def _on_enter(self, _event=None):
        if not self.filtered:
            return "break"
        self._insert(self.filtered[self.active_index])
        return "break"

    def _insert(self, snippet: dict):
        self.on_insert(str(snippet.get("content", "")))
        self.destroy()


class UnsavedChangesDialog(ModalDialog):
    """Dialog for unsaved changes confirmation."""

    def __init__(self, master, colors: Dict[str, str], **kwargs):
        super().__init__(master, **kwargs)
        self.result = "cancel"

        self._init_modal(
            master,
            colors,
            title="Unsaved Changes",
            width=420,
            height=220,
            resizable=(False, False),
            fade_in=True,
        )

        card = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=16)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)

        title = ctk.CTkLabel(
            content,
            text="Unsaved changes",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=colors["text_primary"],
        )
        title.pack(anchor="w")

        message = ctk.CTkLabel(
            content,
            text="You have unsaved changes. Save before continuing?",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=colors["text_secondary"],
            justify="left",
            wraplength=360,
        )
        message.pack(anchor="w", pady=(8, 20))

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")

        cancel_btn = self._btn_secondary(btn_frame, text="Cancel", command=self._on_cancel, width=90, height=36)
        cancel_btn.pack(side="left")

        discard_btn = self._btn_danger(btn_frame, text="Discard", command=self._on_discard, width=90, height=36)
        discard_btn.pack(side="left", padx=(8, 0))

        save_btn = self._btn_primary(btn_frame, text="Save", command=self._on_save, width=90, height=36)
        save_btn.pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_save(self):
        self.result = "save"
        self.destroy()

    def _on_discard(self):
        self.result = "discard"
        self.destroy()

    def _on_cancel(self):
        self.result = "cancel"
        self.destroy()


class RenamePromptDialog(ModalDialog):
    """Dialog for renaming a prompt."""

    def __init__(self, master, colors: Dict[str, str], current_name: str, **kwargs):
        super().__init__(master, **kwargs)
        self.result = None

        self._init_modal(
            master,
            colors,
            title="Rename Prompt",
            width=420,
            height=200,
            resizable=(False, False),
            fade_in=True,
        )

        card = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=16)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)

        title = ctk.CTkLabel(
            content,
            text="Rename prompt",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=colors["text_primary"],
        )
        title.pack(anchor="w")

        self.name_entry = ctk.CTkEntry(
            content,
            height=40,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=10,
            text_color=colors["text_primary"],
        )
        self.name_entry.pack(fill="x", pady=(12, 18))
        self.name_entry.insert(0, current_name)

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        cancel_btn = self._btn_secondary(btn_frame, text="Cancel", command=self._on_cancel, width=90, height=36)
        cancel_btn.pack(side="left")

        save_btn = self._btn_primary(btn_frame, text="Save", command=self._on_save, width=90, height=36)
        save_btn.pack(side="right")

        self.after(100, lambda: self.name_entry.focus())
        self.bind("<Return>", lambda e: self._on_save())
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_save(self):
        name = self.name_entry.get().strip()
        self.result = name
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


class FindReplaceDialog(ModalDialog):
    """Dialog for find/replace in the editor."""

    def __init__(
        self,
        master,
        colors: Dict[str, str],
        on_find: Callable[[str], bool],
        on_replace: Callable[[str, str], bool] | None = None,
        on_replace_all: Callable[[str, str], int] | None = None,
        show_replace: bool = False,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_find = on_find
        self.on_replace = on_replace
        self.on_replace_all = on_replace_all
        self.show_replace = show_replace

        width = 420
        height = 220 if show_replace else 170
        self._init_modal(
            master,
            colors,
            title="Find" + (" & Replace" if show_replace else ""),
            width=width,
            height=height,
            resizable=(False, False),
            fade_in=True,
        )

        card = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=16)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            content,
            text="FIND",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        self.find_entry = ctk.CTkEntry(
            content,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=10,
            text_color=colors["text_primary"],
        )
        self.find_entry.pack(fill="x", pady=(0, 12))

        self.replace_entry = None
        if show_replace:
            ctk.CTkLabel(
                content,
                text="REPLACE",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=colors["text_muted"],
                anchor="w",
            ).pack(fill="x", pady=(0, 6))

            self.replace_entry = ctk.CTkEntry(
                content,
                height=36,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                fg_color=colors["surface"],
                border_color=colors["border"],
                border_width=1,
                corner_radius=10,
                text_color=colors["text_primary"],
            )
            self.replace_entry.pack(fill="x", pady=(0, 12))

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(4, 0))

        find_btn = self._btn_primary(btn_frame, text="Find Next", command=self._on_find, width=100, height=32)
        find_btn.pack(side="left")

        if show_replace:
            replace_btn = self._btn_secondary(
                btn_frame, text="Replace", command=self._on_replace, width=90, height=32
            )
            replace_btn.pack(side="left", padx=(8, 0))

            replace_all_btn = self._btn_secondary(
                btn_frame, text="Replace All", command=self._on_replace_all, width=100, height=32
            )
            replace_all_btn.pack(side="left", padx=(8, 0))

        close_btn = self._btn_secondary(btn_frame, text="Close", command=self.destroy, width=80, height=32)
        close_btn.pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._on_find())
        self.find_entry.focus_set()

    def _on_find(self):
        term = self.find_entry.get().strip()
        if not term:
            return
        self.on_find(term)

    def _on_replace(self):
        if not self.replace_entry or not self.on_replace:
            return
        term = self.find_entry.get().strip()
        replacement = self.replace_entry.get()
        if not term:
            return
        self.on_replace(term, replacement)

    def _on_replace_all(self):
        if not self.replace_entry or not self.on_replace_all:
            return
        term = self.find_entry.get().strip()
        replacement = self.replace_entry.get()
        if not term:
            return
        self.on_replace_all(term, replacement)


class ConfirmDialog(ModalDialog):
    """Generic confirm dialog."""

    def __init__(
        self,
        master,
        colors: Dict[str, str],
        title: str,
        message: str,
        confirm_text: str = "Continue",
        cancel_text: str = "Cancel",
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.result = "cancel"

        self._init_modal(
            master,
            colors,
            title=title,
            width=420,
            height=210,
            resizable=(False, False),
            fade_in=True,
        )

        card = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=16)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)

        title_label = ctk.CTkLabel(
            content,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=colors["text_primary"],
        )
        title_label.pack(anchor="w")

        message_label = ctk.CTkLabel(
            content,
            text=message,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=colors["text_secondary"],
            justify="left",
            wraplength=360,
        )
        message_label.pack(anchor="w", pady=(8, 20))

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")

        cancel_btn = self._btn_secondary(
            btn_frame, text=cancel_text, command=self._on_cancel, width=90, height=36
        )
        cancel_btn.pack(side="left")

        confirm_btn = self._btn_primary(
            btn_frame, text=confirm_text, command=self._on_confirm, width=110, height=36
        )
        confirm_btn.pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _on_confirm(self):
        self.result = "confirm"
        self.destroy()

    def _on_cancel(self):
        self.result = "cancel"
        self.destroy()


class CommandPaletteDialog(ModalDialog):
    """Command palette for prompts and quick actions."""

    def __init__(
        self,
        master,
        prompts: List[Prompt],
        colors: Dict[str, str],
        on_select: Callable[[Prompt], None],
        actions: Optional[List[Dict[str, str]]] = None,
        on_action: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_select = on_select
        self.on_action = on_action
        self.all_prompts = prompts
        self.actions = actions or []
        self.filtered: List[Dict[str, Any]] = []
        self.result_buttons: List[ctk.CTkButton] = []
        self.active_index = 0

        self._init_modal(
            master,
            colors,
            title="Command Palette",
            width=600,
            height=540,
            resizable=(False, False),
            fade_in=True,
        )

        card = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=16)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            content,
            text="Command Palette",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=colors["text_primary"],
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            content,
            text="Search prompts and actions. Enter to run, Esc to close.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["text_secondary"],
        ).pack(anchor="w", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            content,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=10,
            text_color=colors["text_primary"],
            placeholder_text="Search prompts/actions...",
        )
        self.search_entry.pack(fill="x", pady=(0, 14))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        self.results_frame = ctk.CTkScrollableFrame(content, fg_color="transparent", height=320)
        self.results_frame.pack(fill="both", expand=True)

        self.empty_label = ctk.CTkLabel(
            self.results_frame,
            text="No matches.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["text_muted"],
        )

        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", self._on_enter)
        self.bind("<Up>", self._on_up)
        self.bind("<Down>", self._on_down)

        self.search_entry.focus_set()
        self._apply_filter("")

    def _on_search(self, _event=None):
        self._apply_filter(self.search_entry.get())

    def _apply_filter(self, term: str):
        term = term.strip().lower()
        prompt_results = self._build_prompt_results(term)
        action_results = self._build_action_results(term)
        self.filtered = (action_results + prompt_results)[:60]
        self._rebuild_results()

    def _build_prompt_results(self, term: str) -> List[Dict[str, Any]]:
        if term:
            prompts = [
                p
                for p in self.all_prompts
                if term in p.name.lower()
                or term in p.content.lower()
                or any(term in t.lower() for t in p.tags)
            ]
        else:
            prompts = list(self.all_prompts)
        prompts = self._sort_prompts(prompts)
        return [{"kind": "prompt", "prompt": p} for p in prompts]

    def _build_action_results(self, term: str) -> List[Dict[str, Any]]:
        results: List[tuple[int, Dict[str, str]]] = []
        for action in self.actions:
            label = str(action.get("label", ""))
            keywords = str(action.get("keywords", ""))
            haystack = f"{label} {keywords}".lower().strip()
            if term and term not in haystack:
                continue
            score = 0
            if term and haystack.startswith(term):
                score = 2
            elif term and term in label.lower():
                score = 1
            results.append((score, action))
        results.sort(key=lambda item: item[0], reverse=True)
        return [{"kind": "action", "action": action} for _, action in results]

    def _sort_prompts(self, prompts: List[Prompt]) -> List[Prompt]:
        def parse_time(value: str) -> datetime:
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return datetime.min

        pinned = [p for p in prompts if getattr(p, "pinned", False)]
        others = [p for p in prompts if not getattr(p, "pinned", False)]
        pinned_sorted = sorted(pinned, key=lambda p: parse_time(p.updated_at), reverse=True)
        others_sorted = sorted(others, key=lambda p: parse_time(p.updated_at), reverse=True)
        return pinned_sorted + others_sorted

    def _rebuild_results(self):
        for child in self.results_frame.winfo_children():
            child.destroy()
        self.result_buttons.clear()

        if not self.filtered:
            self.empty_label = ctk.CTkLabel(
                self.results_frame,
                text="No matches.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=self.colors["text_muted"],
            )
            self.empty_label.pack(pady=16)
            self.active_index = 0
            return

        for idx, result in enumerate(self.filtered):
            label = self._build_label(result)
            btn = ctk.CTkButton(
                self.results_frame,
                text=label,
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold" if idx == 0 else "normal"),
                fg_color=self.colors["accent_glow"] if idx == 0 else self.colors["surface"],
                hover_color=self.colors["border"],
                text_color=self.colors["text_primary"],
                anchor="w",
                command=lambda r=result: self._select_result(r),
            )
            btn.pack(fill="x", pady=4, padx=4)
            self.result_buttons.append(btn)

        self.active_index = 0
        self._highlight_active()

    def _build_label(self, result: Dict[str, Any]) -> str:
        if result.get("kind") == "action":
            action = result.get("action", {})
            shortcut = str(action.get("shortcut", "")).strip()
            shortcut_text = f" [{shortcut}]" if shortcut else ""
            return f"Run: {action.get('label', 'Action')}{shortcut_text}"

        prompt: Prompt = result["prompt"]
        tags = ", ".join(prompt.tags[:3])
        tag_text = f" | {tags}" if tags else ""
        pin = "* " if getattr(prompt, "pinned", False) else ""
        return f"{pin}{prompt.name} | {prompt.category.value}{tag_text}"

    def _highlight_active(self):
        for i, btn in enumerate(self.result_buttons):
            if i == self.active_index:
                btn.configure(
                    fg_color=self.colors["accent_glow"],
                    text_color=self.colors["text_primary"],
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color=self.colors["surface"],
                    text_color=self.colors["text_secondary"],
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                )

    def _on_up(self, _event=None):
        if not self.filtered:
            return "break"
        self.active_index = max(0, self.active_index - 1)
        self._highlight_active()
        return "break"

    def _on_down(self, _event=None):
        if not self.filtered:
            return "break"
        self.active_index = min(len(self.filtered) - 1, self.active_index + 1)
        self._highlight_active()
        return "break"

    def _on_enter(self, _event=None):
        if not self.filtered:
            return "break"
        self._select_result(self.filtered[self.active_index])
        return "break"

    def _select_result(self, result: Dict[str, Any]):
        if result.get("kind") == "action":
            action = result.get("action", {})
            action_id = str(action.get("id", "")).strip()
            if action_id and self.on_action:
                self.on_action(action_id)
            self.destroy()
            return

        prompt: Prompt = result["prompt"]
        self.on_select(prompt)
        self.destroy()

class PromptHistoryDialog(ModalDialog):
    """Dialog showing prompt version history."""

    def __init__(
        self,
        master,
        prompt: Prompt,
        colors: Dict[str, str],
        on_restore: Callable[[dict], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.prompt = prompt
        self.on_restore = on_restore

        self._init_modal(
            master,
            colors,
            title="Version History",
            width=620,
            height=520,
            resizable=(False, False),
            fade_in=True,
        )

        card = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=16)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)

        title = ctk.CTkLabel(
            content,
            text=f"History · {prompt.name}",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=colors["text_primary"],
        )
        title.pack(anchor="w", pady=(0, 12))

        subtitle = ctk.CTkLabel(
            content,
            text="Select a prior version to restore.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(0, 12))

        self.scroll = ctk.CTkScrollableFrame(content, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._build_list()

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack(fill="x", pady=(12, 0))

        close_btn = self._btn_secondary(btn_row, text="Close", command=self.destroy, width=90, height=36)
        close_btn.pack(side="right")

        self.bind("<Escape>", lambda _e: self.destroy())

    def _build_list(self):
        history = self.prompt.history if isinstance(self.prompt.history, list) else []
        if not history:
            empty = ctk.CTkLabel(
                self.scroll,
                text="No previous versions yet.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=self.colors["text_muted"],
            )
            empty.pack(pady=16)
            return

        for idx, version in enumerate(history, start=1):
            row = ctk.CTkFrame(self.scroll, fg_color=self.colors["surface"], corner_radius=10)
            row.pack(fill="x", pady=6, padx=2)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=12, pady=10)

            time_label = ctk.CTkLabel(
                left,
                text=self._format_time(version.get("saved_at")),
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=self.colors["text_primary"],
            )
            time_label.pack(anchor="w")

            snippet = self._build_snippet(version.get("content", ""))
            meta = self._build_meta(version)
            detail = f"{meta} · {snippet}" if snippet else meta

            detail_label = ctk.CTkLabel(
                left,
                text=detail,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=self.colors["text_muted"],
                anchor="w",
                justify="left",
                wraplength=420,
            )
            detail_label.pack(anchor="w", pady=(4, 0))

            restore_btn = self._btn_primary(
                row,
                text="Restore",
                command=lambda v=version: self._on_restore(v),
                width=80,
                height=32,
            )
            restore_btn.pack(side="right", padx=12, pady=12)

    def _on_restore(self, version: dict):
        self.on_restore(version)
        self.destroy()

    def _format_time(self, iso_time: Optional[str]) -> str:
        if not iso_time:
            return "Unknown time"
        try:
            dt = datetime.fromisoformat(iso_time)
            return dt.strftime("%b %d, %Y · %I:%M %p")
        except Exception:
            return iso_time

    def _build_snippet(self, content: str) -> str:
        content = content.strip().replace("\n", " ")
        if len(content) > 80:
            return content[:77].rstrip() + "..."
        return content

    def _build_meta(self, version: dict) -> str:
        name = version.get("name", "")
        category = version.get("category", "")
        custom_category = (version.get("custom_category", "") or "").strip()
        if category == "Other" and custom_category:
            category = f"Other · {custom_category}"
        tags = version.get("tags") or []
        tag_text = ", ".join(tags[:3])
        parts = [p for p in (name, category, tag_text) if p]
        return " · ".join(parts)


class TagInputDialog(ModalDialog):
    """Dialog for entering a single tag."""

    def __init__(
        self,
        master,
        colors: Dict[str, str],
        title: str,
        confirm_text: str,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.result: Optional[str] = None

        self._init_modal(
            master,
            colors,
            title=title,
            width=420,
            height=220,
            resizable=(False, False),
            fade_in=True,
        )

        card = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=16)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)

        title_label = ctk.CTkLabel(
            content,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=colors["text_primary"],
        )
        title_label.pack(anchor="w")

        self.entry = ctk.CTkEntry(
            content,
            height=40,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=10,
            text_color=colors["text_primary"],
            placeholder_text="Tag name...",
        )
        self.entry.pack(fill="x", pady=(12, 18))

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        cancel_btn = self._btn_secondary(btn_frame, text="Cancel", command=self._on_cancel, width=90, height=36)
        cancel_btn.pack(side="left")

        confirm_btn = self._btn_primary(
            btn_frame, text=confirm_text, command=self._on_confirm, width=90, height=36
        )
        confirm_btn.pack(side="right")

        self.after(100, lambda: self.entry.focus())
        self.bind("<Return>", lambda _e: self._on_confirm())
        self.bind("<Escape>", lambda _e: self._on_cancel())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_confirm(self):
        value = self.entry.get().strip()
        if not value:
            return
        self.result = value
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

