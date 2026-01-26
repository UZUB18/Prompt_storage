"""Main application window - Apple 2026 Edition."""
import customtkinter as ctk
from tkinter import filedialog
from typing import Optional
from pathlib import Path
import shutil

from .models import Prompt, Category
from .storage import Storage
from .config import (
    get_data_dir,
    set_data_dir,
    get_sort_option,
    set_sort_option,
    get_theme,
    set_theme,
    get_ui_scale,
    set_ui_scale,
)
from .resources import resource_path
from .components.prompt_list import PromptList
from .components.prompt_editor import PromptEditor
from .components.dialogs import NewPromptDialog, UnsavedChangesDialog, RenamePromptDialog, ConfirmDialog
from .components.toast import Toast


class PromptLibraryApp(ctk.CTk):
    """Main application window with Apple 2026 design."""

    # Design tokens - Apple 2026 Edition
    LIGHT_COLORS = {
        # Light mode (default for this design)
        "bg": "#F5F5F7",              # Apple Silver/Light Gray
        "surface": "#FFFFFF",          # Pure white cards
        "sidebar_bg": "#FAFAFA",       # Slightly off-white sidebar
        "card": "#FFFFFF",             # White cards
        "input": "#FFFFFF",            # White inputs
        "border": "#E5E5E5",           # Light borders
        "accent": "#8B5CF6",           # Violet (from mockup)
        "accent_hover": "#7C3AED",     # Darker violet
        "accent_glow": "#E9DEFF",      # Light violet (no alpha)
        "success": "#28C840",          # Apple Green
        "danger": "#FF5F57",           # Apple Red
        "warning": "#F59E0B",          # Amber
        "text_primary": "#1D1D1F",     # Near-black
        "text_secondary": "#6E6E73",   # Gray
        "text_muted": "#86868B",       # Light gray
        "category_bg": "#F2F2F4",      # Neutral pill background
        "pill_bg": "#F2F2F4",
        "toast_bg": "#1D1D1F",
        "toast_text": "#FFFFFF",
    }

    DARK_COLORS = {
        "bg": "#0F0F10",
        "surface": "#1A1A1D",
        "sidebar_bg": "#151517",
        "card": "#1A1A1D",
        "input": "#1E1E21",
        "border": "#2E2E33",
        "accent": "#8B5CF6",
        "accent_hover": "#7C3AED",
        "accent_glow": "#2B2440",
        "success": "#2BD24A",
        "danger": "#FF6B63",
        "warning": "#F59E0B",
        "text_primary": "#F5F5F7",
        "text_secondary": "#C7C7CC",
        "text_muted": "#9A9AA0",
        "category_bg": "#2A2A2E",
        "pill_bg": "#2A2A2E",
        "toast_bg": "#F5F5F7",
        "toast_text": "#0F0F10",
    }

    def __init__(self):
        super().__init__()

        # Configure appearance
        self.theme = get_theme()
        if self.theme not in ("light", "dark"):
            self.theme = "light"
        ctk.set_appearance_mode(self.theme)
        ctk.set_default_color_theme("blue")

        # UI scaling (apply before building widgets)
        self.ui_scale_pref = get_ui_scale()
        self._apply_ui_scaling(self.ui_scale_pref)

        self.COLORS = self._get_theme_colors()
        self.title("Prompt Library Pro")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.configure(fg_color=self.COLORS["bg"])
        try:
            self.iconbitmap(str(resource_path("prompt_library.ico")))
        except Exception:
            # Not critical (e.g., missing icon on some platforms / window managers)
            pass

        # State
        data_dir = get_data_dir()
        self.storage = Storage(data_dir=data_dir) if data_dir else Storage()
        self.prompts = self.storage.load_prompts()
        self.current_prompt: Optional[Prompt] = None
        self.has_unsaved_changes = False
        self.active_filter = "All"
        self._search_after_id = None
        self.filter_buttons: dict[str, ctk.CTkButton] = {}
        self.filter_map: dict[str, Optional[str]] = {}
        self.filter_labels: dict[str, str] = {}
        self.filter_order: list[str] = []

        # Build UI
        self._build_ui()
        self._refresh_list()
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self._bind_shortcuts()

    def _get_theme_colors(self) -> dict:
        return self.DARK_COLORS if self.theme == "dark" else self.LIGHT_COLORS

    def _round_scale(self, value: float) -> float:
        # Round to nearest 0.05 for stability
        return max(0.75, min(2.5, round(value / 0.05) * 0.05))

    def _compute_auto_scale(self) -> float:
        # Prefer actual DPI when available (helps on 4K/high-DPI monitors).
        try:
            ppi = float(self.winfo_fpixels("1i"))
        except Exception:
            ppi = 96.0
        dpi_scale = ppi / 96.0

        # Also consider resolution: big/high-res monitors often benefit from larger UI.
        try:
            w = int(self.winfo_screenwidth())
        except Exception:
            w = 1920

        if w >= 3840:
            res_scale = 1.50
        elif w >= 2560:
            res_scale = 1.25
        elif w >= 1920:
            res_scale = 1.10
        else:
            res_scale = 1.00

        return self._round_scale(max(dpi_scale, res_scale, 1.0))

    def _apply_ui_scaling(self, pref: str):
        # pref is "auto" or a float-as-string like "1.25"
        if isinstance(pref, str) and pref.strip().lower() == "auto":
            scale = self._compute_auto_scale()
        else:
            try:
                scale = float(pref)
            except Exception:
                scale = self._compute_auto_scale()
            scale = self._round_scale(scale)

        try:
            ctk.set_widget_scaling(scale)
            ctk.set_window_scaling(scale)
        except Exception:
            pass

    def _build_ui(self):
        """Build the application UI."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        """Build Apple-style navigation sidebar with auto-sizing."""
        # Use grid column configure for sidebar sizing
        self.grid_columnconfigure(0, weight=0, minsize=300)
        
        sidebar = ctk.CTkFrame(
            self,
            fg_color=self.COLORS["sidebar_bg"],
            corner_radius=0,
            border_width=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Use grid layout for sidebar contents
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(6, weight=1)  # Prompt list expands

        # Sidebar right border (subtle)
        border_frame = ctk.CTkFrame(
            sidebar,
            width=1,
            fg_color=self.COLORS["border"],
            corner_radius=0,
        )
        border_frame.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

        # Row 0: Header with title and add button
        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(20, 16))

        title = ctk.CTkLabel(
            header,
            text="Library",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.COLORS["text_primary"],
        )
        title.pack(side="left")

        # Add button (violet circle)
        new_btn = ctk.CTkButton(
            header,
            text="+",
            width=32,
            height=32,
            corner_radius=16,
            font=ctk.CTkFont(size=18),
            fg_color=self.COLORS["accent"],
            hover_color=self.COLORS["accent_hover"],
            command=self._on_new_prompt,
        )
        new_btn.pack(side="right")

        # Row 1: Search field + clear button
        search_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            height=36,
            placeholder_text="Search...",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=self.COLORS["surface"],
            border_color=self.COLORS["border"],
            border_width=1,
            corner_radius=10,
            text_color=self.COLORS["text_primary"],
            textvariable=self.search_entry_var,
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        self.clear_search_btn = ctk.CTkButton(
            search_frame,
            text="x",
            width=36,
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=self.COLORS["surface"],
            hover_color=self.COLORS["border"],
            text_color=self.COLORS["text_muted"],
            border_width=1,
            border_color=self.COLORS["border"],
            command=self._clear_search,
            state="disabled",
        )
        self.clear_search_btn.grid(row=0, column=1)

        # Row 2: Segmented filter control (compact)
        filter_container = ctk.CTkFrame(
            sidebar,
            fg_color=self.COLORS["input"],
            corner_radius=10,
            height=32,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        filter_container.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        filter_container.grid_propagate(False)
        filter_container.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.filter_map = {
            "All": None,
            "Persona": "Persona",
            "System": "System Prompt",
            "Template": "Template",
            "Other": "Other",
        }
        self.filter_labels = {
            "All": "All",
            "Persona": "Persona",
            "System": "System",
            "Template": "Template",
            "Other": "Other",
        }
        self.filter_order = ["All", "Persona", "System", "Template", "Other"]

        for i, key in enumerate(self.filter_order):
            label = self.filter_labels[key]
            is_active = key == "All"
            btn = ctk.CTkButton(
                filter_container,
                text=label,
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if is_active else "normal"),
                fg_color=self.COLORS["surface"] if is_active else "transparent",
                hover_color=self.COLORS["surface"],
                text_color=self.COLORS["accent"] if is_active else self.COLORS["text_secondary"],
                border_width=0,
                command=lambda d=key: self._on_filter(d),
            )
            btn.grid(row=0, column=i, sticky="ew", padx=2, pady=2)
            self.filter_buttons[key] = btn

        # Row 3: Sort options
        sort_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        sort_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 8))
        sort_frame.grid_columnconfigure(1, weight=1)

        sort_label = ctk.CTkLabel(
            sort_frame,
            text="SORT",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.COLORS["text_muted"],
        )
        sort_label.grid(row=0, column=0, sticky="w", padx=(4, 8))

        sort_options = ["Recently updated", "Name A->Z", "Created"]
        sort_value = get_sort_option()
        if sort_value not in sort_options:
            sort_value = "Recently updated"
        self.sort_var = ctk.StringVar(value=sort_value)
        # Wrap the option menu so it visually matches CTkEntry borders.
        sort_menu_outer = ctk.CTkFrame(
            sort_frame,
            fg_color=self.COLORS["surface"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        sort_menu_outer.grid(row=0, column=1, sticky="ew")
        sort_menu_outer.grid_columnconfigure(0, weight=1)

        self.sort_menu = ctk.CTkOptionMenu(
            sort_menu_outer,
            values=sort_options,
            variable=self.sort_var,
            height=30,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=self.COLORS["surface"],
            text_color=self.COLORS["text_primary"],
            # Keep dropdown chrome neutral; use accent for primary actions only.
            button_color=self.COLORS["surface"],
            button_hover_color=self.COLORS["bg"],
            dropdown_fg_color=self.COLORS["surface"],
            dropdown_text_color=self.COLORS["text_primary"],
            dropdown_hover_color=self.COLORS["accent_glow"],
            corner_radius=9,
            command=lambda _: self._on_sort_change(),
        )
        self.sort_menu.pack(fill="x", padx=1, pady=1)

        # Row 4: Count label
        count_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        count_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 6))
        count_frame.grid_columnconfigure(0, weight=1)

        self.count_label = ctk.CTkLabel(
            count_frame,
            text="0 PROMPTS",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.COLORS["text_muted"],
        )
        self.count_label.grid(row=0, column=0, sticky="w")

        self.theme_var = ctk.BooleanVar(value=self.theme == "dark")
        self.theme_toggle = ctk.CTkSwitch(
            count_frame,
            text="Dark mode",
            variable=self.theme_var,
            onvalue=True,
            offvalue=False,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.COLORS["text_muted"],
            command=self._toggle_theme,
        )
        self.theme_toggle.grid(row=0, column=1, sticky="e")

        # UI scale control (useful on large/high-DPI monitors)
        ui_scale_frame = ctk.CTkFrame(count_frame, fg_color="transparent")
        ui_scale_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ui_scale_frame.grid_columnconfigure(1, weight=1)

        ui_scale_label = ctk.CTkLabel(
            ui_scale_frame,
            text="UI Scale",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.COLORS["text_muted"],
        )
        ui_scale_label.grid(row=0, column=0, sticky="w", padx=(0, 8))

        ui_scale_options = ["Auto", "100%", "110%", "125%", "150%", "175%", "200%"]
        pref = (get_ui_scale() or "auto").strip().lower()
        if pref == "auto":
            display = "Auto"
        else:
            try:
                display = f"{int(round(float(pref) * 100))}%"
            except Exception:
                display = "Auto"
        if display not in ui_scale_options:
            display = "Auto"

        self.ui_scale_var = ctk.StringVar(value=display)

        ui_scale_outer = ctk.CTkFrame(
            ui_scale_frame,
            fg_color=self.COLORS["surface"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        ui_scale_outer.grid(row=0, column=1, sticky="ew")
        ui_scale_outer.grid_columnconfigure(0, weight=1)

        self.ui_scale_menu = ctk.CTkOptionMenu(
            ui_scale_outer,
            values=ui_scale_options,
            variable=self.ui_scale_var,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=self.COLORS["surface"],
            text_color=self.COLORS["text_primary"],
            button_color=self.COLORS["surface"],
            button_hover_color=self.COLORS["bg"],
            dropdown_fg_color=self.COLORS["surface"],
            dropdown_text_color=self.COLORS["text_primary"],
            dropdown_hover_color=self.COLORS["accent_glow"],
            corner_radius=9,
            command=lambda _: self._on_ui_scale_change(),
        )
        self.ui_scale_menu.pack(fill="x", padx=1, pady=1)

        # Row 5: Divider between controls and list (sticky header)
        ctk.CTkFrame(sidebar, height=1, fg_color=self.COLORS["border"]).grid(
            row=5, column=0, sticky="ew", padx=16, pady=(0, 8)
        )

        # Row 6: Prompt list (EXPANDS)
        self.prompt_list = PromptList(
            sidebar,
            on_select=self._on_prompt_select,
            on_copy=self._on_prompt_list_copy,
            on_rename=self._on_prompt_list_rename,
            on_clear_search=self._clear_search,
            on_new_prompt=self._on_new_prompt,
            colors=self.COLORS,
        )
        self.prompt_list.grid(row=6, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.prompt_list.set_sort(self.sort_var.get())
        self._update_filter_counts()

        # Row 7: Footer actions
        footer = ctk.CTkFrame(
            sidebar, 
            fg_color=self.COLORS["sidebar_bg"],
            corner_radius=0,
            height=56,
        )
        footer.grid(row=7, column=0, sticky="ew")
        footer.grid_propagate(False)

        # Top border for footer
        footer_border = ctk.CTkFrame(footer, height=1, fg_color=self.COLORS["border"])
        footer_border.pack(fill="x", side="top")

        btn_container = ctk.CTkFrame(footer, fg_color="transparent")
        btn_container.pack(fill="both", expand=True, padx=16, pady=12)

        import_btn = ctk.CTkButton(
            btn_container,
            text="Import",
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.COLORS["surface"],
            hover_color=self.COLORS["border"],
            text_color=self.COLORS["text_secondary"],
            border_width=1,
            border_color=self.COLORS["border"],
            command=self._on_import,
        )
        import_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        export_btn = ctk.CTkButton(
            btn_container,
            text="Export",
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.COLORS["surface"],
            hover_color=self.COLORS["border"],
            text_color=self.COLORS["text_secondary"],
            border_width=1,
            border_color=self.COLORS["border"],
            command=self._on_export,
        )
        export_btn.pack(side="left", fill="x", expand=True)

        location_btn = ctk.CTkButton(
            btn_container,
            text="Library...",
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.COLORS["surface"],
            hover_color=self.COLORS["border"],
            text_color=self.COLORS["text_secondary"],
            border_width=1,
            border_color=self.COLORS["border"],
            command=self._on_change_library_location,
        )
        location_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

    def _build_main_area(self):
        """Build the main editor area."""
        main = ctk.CTkFrame(self, fg_color=self.COLORS["surface"], corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # Editor component
        self.editor = PromptEditor(
            main,
            on_save=self._on_save,
            on_delete=self._on_delete,
            on_copy=self._on_copy,
            on_toast=self._show_toast,
            on_change=self._on_editor_change,
            colors=self.COLORS,
        )
        self.editor.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

    def _bind_shortcuts(self):
        """Bind global keyboard shortcuts."""
        self.bind_all("<Control-n>", lambda e: self._on_new_prompt())
        self.bind_all("<Control-s>", lambda e: self._on_shortcut_save())
        self.bind_all("<Control-f>", lambda e: self._on_ctrl_f(e))
        self.bind_all("<Control-h>", lambda e: self._on_ctrl_h(e))
        self.bind_all("<Delete>", lambda e: self._on_shortcut_delete(e))
        self.bind_all("<Control-d>", lambda e: self._on_duplicate_prompt())
        self.bind_all("<Escape>", lambda e: self._on_escape())

    def _focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, "end")

    def _on_ctrl_f(self, event=None):
        widget = self.focus_get()
        if self.editor.is_content_focused(widget):
            self.editor.open_find_dialog()
            return "break"
        self._focus_search()
        return "break"

    def _on_ctrl_h(self, event=None):
        widget = self.focus_get()
        if self.editor.is_content_focused(widget):
            self.editor.open_replace_dialog()
            return "break"
        return "break"

    def _toggle_theme(self):
        self.theme = "dark" if self.theme_var.get() else "light"
        set_theme(self.theme)
        ctk.set_appearance_mode(self.theme)
        self.COLORS = self._get_theme_colors()
        self.configure(fg_color=self.COLORS["bg"])
        self._rebuild_ui()

    def _on_ui_scale_change(self):
        value = (self.ui_scale_var.get() or "Auto").strip()
        if value.lower() == "auto":
            pref = "auto"
        else:
            # "125%" -> 1.25
            try:
                pct = float(value.replace("%", "").strip())
                pref = str(pct / 100.0)
            except Exception:
                pref = "auto"

        self.ui_scale_pref = pref
        set_ui_scale(pref)
        self._apply_ui_scaling(pref)
        self._rebuild_ui()
        self._show_toast(f"UI scale: {value}")

    def _rebuild_ui(self):
        current_prompt = self.current_prompt
        editor_state = self._capture_editor_state()
        self.has_unsaved_changes = editor_state["has_unsaved_changes"]
        self.active_filter = editor_state["active_filter"]
        self.search_entry_var = None
        self.sort_var = None

        for child in self.winfo_children():
            child.destroy()

        self._build_ui()
        self._refresh_list()
        self._restore_editor_state(current_prompt, editor_state)

    def _capture_editor_state(self) -> dict:
        state = {
            "has_unsaved_changes": self.has_unsaved_changes,
            "active_filter": self.active_filter,
            "search": "",
            "sort": None,
            "draft": None,
        }
        try:
            state["search"] = self.search_entry_var.get()
        except Exception:
            state["search"] = ""
        try:
            state["sort"] = self.sort_var.get()
        except Exception:
            state["sort"] = None

        if self.current_prompt:
            state["draft"] = {
                "name": self.editor.name_entry.get().strip(),
                "category": self.editor.category_var.get(),
                "tags": self.editor.tags_entry.get(),
                "content": self.editor._get_current_content(),
                "sensitive": bool(self.editor.sensitive_var.get()),
            }
        return state

    def _restore_editor_state(self, prompt: Optional[Prompt], state: dict):
        if state.get("sort"):
            self.sort_var.set(state["sort"])
            self.prompt_list.set_sort(self.sort_var.get())

        self.search_entry_var.set(state.get("search", ""))
        self.prompt_list.set_search(state.get("search", ""))
        self._update_clear_button()

        # Restore filter selection
        active = state.get("active_filter", "All")
        if active in self.filter_buttons:
            self._on_filter(active)

        if prompt:
            self.current_prompt = prompt
            self.editor.set_prompt(prompt)
            draft = state.get("draft")
            if draft:
                self.editor.name_entry.delete(0, "end")
                self.editor.name_entry.insert(0, draft["name"])
                self.editor.category_var.set(draft["category"])
                self.editor.tags_entry.delete(0, "end")
                self.editor.tags_entry.insert(0, draft["tags"])
                self.editor.sensitive_var.set(draft["sensitive"])
                self.editor._set_current_content(draft["content"])
            self.editor.update_save_state(state.get("has_unsaved_changes", False))

    def _on_shortcut_save(self):
        if self.current_prompt:
            self.editor.save_current_prompt()

    def _on_shortcut_delete(self, event: object | None = None):
        widget = self.focus_get()
        if isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)):
            return
        if self.current_prompt:
            self._on_delete(self.current_prompt.id)

    def _on_escape(self):
        widget = self.focus_get()
        if widget is not None and widget.winfo_toplevel() is not self:
            return
        if self.search_entry_var.get():
            self._clear_search()
            return
        if widget is not self.search_entry:
            self._focus_search()

    def _refresh_list(self):
        """Refresh the prompt list."""
        self.prompts = self.storage.load_prompts()
        self.prompt_list.set_prompts(self.prompts)
        self._update_count()
        self._update_filter_counts()
        if self.storage.consume_restore_flag():
            self._show_toast("Library restored from backup")

    def _update_count(self):
        """Update prompt count."""
        count = len(self.prompt_list.filtered_prompts)
        total = len(self.prompts)
        if count == total:
            self.count_label.configure(text=f"{count} PROMPTS")
        else:
            self.count_label.configure(text=f"{count} OF {total} PROMPTS")

    def _on_search(self, event: object | None = None):
        """Handle search."""
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(200, self._apply_search)

    def _apply_search(self):
        self._search_after_id = None
        term = self.search_entry_var.get()
        self.prompt_list.set_search(term)
        self._update_count()
        self._update_filter_counts()
        self._update_clear_button()

    def _clear_search(self):
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
            self._search_after_id = None
        self.search_entry_var.set("")
        self.prompt_list.set_search("")
        self._update_count()
        self._update_filter_counts()
        self._update_clear_button()
        self.search_entry.focus_set()

    def _update_clear_button(self):
        has_text = bool(self.search_entry_var.get().strip())
        state = "normal" if has_text else "disabled"
        text_color = self.COLORS["text_secondary"] if has_text else self.COLORS["text_muted"]
        self.clear_search_btn.configure(state=state, text_color=text_color)

    def _on_sort_change(self):
        self.prompt_list.set_sort(self.sort_var.get())
        self._update_count()
        set_sort_option(self.sort_var.get())

    def _on_filter(self, display_name: str):
        """Handle filter chip click."""
        self.active_filter = display_name
        
        # Update chip styles
        for name, btn in self.filter_buttons.items():
            if name == display_name:
                btn.configure(
                    fg_color=self.COLORS["surface"],
                    text_color=self.COLORS["accent"],
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.COLORS["text_secondary"],
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
                )

        # Apply filter using the mapped category value
        cat_value = self.filter_map.get(display_name)
        if cat_value is None:
            self.prompt_list.set_category_filter(None)
        else:
            self.prompt_list.set_category_filter(Category(cat_value))
        self._update_count()
        self._update_filter_counts()

    def _update_filter_counts(self):
        """Update category filter chip labels with counts."""
        term = self.search_entry_var.get().strip().lower()

        def matches_search(prompt: Prompt) -> bool:
            if not term:
                return True
            return (
                term in prompt.name.lower()
                or term in prompt.content.lower()
                or any(term in t.lower() for t in prompt.tags)
            )

        counts: dict[str, int] = {key: 0 for key in self.filter_order}
        for prompt in self.prompts:
            if not matches_search(prompt):
                continue
            counts["All"] += 1
            if prompt.category.value == "Persona":
                counts["Persona"] += 1
            elif prompt.category.value == "System Prompt":
                counts["System"] += 1
            elif prompt.category.value == "Template":
                counts["Template"] += 1
            else:
                counts["Other"] += 1

        for key, btn in self.filter_buttons.items():
            label = self.filter_labels.get(key, key)
            btn.configure(text=f"{label} ({counts.get(key, 0)})")

    def _on_prompt_select(self, prompt: Prompt):
        """Handle prompt selection."""
        if self.current_prompt and prompt.id == self.current_prompt.id:
            return

        action = self._confirm_unsaved_changes()
        if action == "cancel":
            self.prompt_list.set_selected_prompt(self.current_prompt)
            return
        if action == "save":
            self.editor.save_current_prompt()

        self.current_prompt = prompt
        self.has_unsaved_changes = False
        self.editor.set_prompt(prompt)

    def _on_new_prompt(self):
        """Open new prompt dialog."""
        dialog = NewPromptDialog(self, on_create=self._create_prompt, colors=self.COLORS)
        dialog.focus_set()

    def _create_prompt(self, prompt: Prompt):
        """Create new prompt."""
        self.storage.add_prompt(prompt)
        self._refresh_list()
        self.editor.set_prompt(prompt)
        self._show_toast("Prompt created")

    def _on_save(self, prompt: Prompt):
        """Save prompt."""
        self.storage.update_prompt(prompt)
        self.has_unsaved_changes = False
        self._refresh_list()
        self.editor.set_prompt(prompt)
        self.editor.update_save_state(False)
        self._show_toast("Changes saved")

    def _on_delete(self, prompt_id: str):
        """Delete prompt."""
        self.storage.delete_prompt(prompt_id)
        self.editor.clear()
        self._refresh_list()
        self._show_toast("Prompt deleted")

    def _on_copy(self, content: str):
        """Copy to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(content)
        self._show_toast("Copied to clipboard")

    def _on_prompt_list_copy(self, prompt: Prompt):
        """Copy content from list context menu."""
        if prompt.sensitive:
            if not self.editor.confirm_sensitive_copy("Copy"):
                return
        self._on_copy(prompt.content)

    def _on_prompt_list_rename(self, prompt: Prompt):
        """Rename prompt from list context menu."""
        dialog = RenamePromptDialog(self, colors=self.COLORS, current_name=prompt.name)
        self.wait_window(dialog)
        new_name = dialog.result
        if not new_name or new_name == prompt.name:
            return

        if self.current_prompt and prompt.id == self.current_prompt.id and self.has_unsaved_changes:
            action = self._confirm_unsaved_changes()
            if action == "cancel":
                return
            if action == "save":
                self.editor.save_current_prompt()
            elif action == "discard":
                current_prompts = self.storage.load_prompts()
                stored = next((p for p in current_prompts if p.id == prompt.id), None)
                if stored:
                    self.current_prompt = stored
                    self.editor.set_prompt(stored)
                self.has_unsaved_changes = False
                self.editor.update_save_state(False)

        prompt.name = new_name
        self.storage.update_prompt(prompt)
        if self.current_prompt and prompt.id == self.current_prompt.id:
            self.current_prompt.name = new_name
            self.editor.name_entry.delete(0, "end")
            self.editor.name_entry.insert(0, new_name)
            self.has_unsaved_changes = False
            self.editor.update_save_state(False)
        self._refresh_list()
        self._show_toast("Prompt renamed")

    def _on_editor_change(self):
        """Handle editor content change."""
        self.has_unsaved_changes = True
        self.editor.update_save_state(True)

    def _on_export(self):
        """Export prompts."""
        filepath = filedialog.asksaveasfilename(
            title="Export Prompts",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="prompts_export.json",
        )
        if filepath:
            self.storage.export_to_file(filepath)
            self._show_toast(f"Exported {len(self.prompts)} prompts")

    def _on_duplicate_prompt(self):
        """Duplicate the current prompt."""
        if not self.current_prompt:
            return

        if self.has_unsaved_changes:
            action = self._confirm_unsaved_changes()
            if action == "cancel":
                return
            if action == "save":
                self.editor.save_current_prompt()
            elif action == "discard":
                current_prompts = self.storage.load_prompts()
                stored = next((p for p in current_prompts if p.id == self.current_prompt.id), None)
                if stored:
                    self.current_prompt = stored
                    self.editor.set_prompt(stored)
                self.has_unsaved_changes = False
                self.editor.update_save_state(False)

        name = self.editor.name_entry.get().strip() or self.current_prompt.name
        content = self.editor.content_text.get("1.0", "end-1c")
        tags = [t.strip() for t in self.editor.tags_entry.get().split(",") if t.strip()]
        category = Category(self.editor.category_var.get())

        new_prompt = Prompt(
            name=f"{name} (copy)",
            content=content,
            category=category,
            tags=tags,
        )

        self.storage.add_prompt(new_prompt)
        self._refresh_list()
        self._on_prompt_select(new_prompt)
        self._show_toast("Prompt duplicated")

    def _on_import(self):
        """Import prompts."""
        filepath = filedialog.askopenfilename(
            title="Import Prompts",
            filetypes=[("JSON files", "*.json")],
        )
        if filepath:
            try:
                count = self.storage.import_from_file(filepath)
            except ValueError as exc:
                self._show_toast(f"Import failed: {exc}")
                return
            except Exception:
                self._show_toast("Import failed: unexpected error")
                return

            self._refresh_list()
            self._show_toast(f"Imported {count} prompts")

    def _confirm_unsaved_changes(self) -> str:
        """Return user action for unsaved changes."""
        if not self.has_unsaved_changes:
            return "proceed"

        dialog = UnsavedChangesDialog(self, colors=self.COLORS)
        self.wait_window(dialog)
        return dialog.result or "cancel"

    def _on_window_close(self):
        """Handle window close with unsaved changes guard."""
        action = self._confirm_unsaved_changes()
        if action == "cancel":
            return
        if action == "save":
            self.editor.save_current_prompt()
        self.destroy()

    def _on_change_library_location(self):
        """Choose a new library storage location."""
        current_dir = self.storage.data_dir
        filepath = filedialog.askdirectory(
            title="Choose Library Location",
            mustexist=False,
        )
        if not filepath:
            return

        target_dir = Path(filepath)
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            self._show_toast("Library location failed: cannot create folder")
            return

        if target_dir.resolve() == current_dir.resolve():
            self._show_toast("Library location unchanged")
            return

        current_prompts = current_dir / "prompts.json"
        target_prompts = target_dir / "prompts.json"

        if current_prompts.exists() and not target_prompts.exists():
            try:
                shutil.copy2(current_prompts, target_prompts)
            except OSError:
                self._show_toast("Library location failed: could not copy data")
                return

        set_data_dir(str(target_dir))
        self.storage = Storage(data_dir=str(target_dir))
        self.prompts = self.storage.load_prompts()
        self.current_prompt = None
        self.editor.clear()
        self._refresh_list()
        self._show_toast("Library location updated")

    def _show_toast(self, message: str):
        """Show toast notification."""
        Toast(self, message, colors=self.COLORS)


def run():
    """Run the application."""
    app = PromptLibraryApp()
    app.mainloop()


