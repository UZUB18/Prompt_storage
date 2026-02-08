"""Main application window - Apple 2026 Edition."""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from typing import Optional
from pathlib import Path
import shutil
import re

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
    get_preview_split_enabled,
    set_preview_split_enabled,
    get_token_count_mode,
    set_token_count_mode,
    get_ui_density_mode,
    set_ui_density_mode,
)
from .resources import resource_path
from .components.prompt_list import PromptList
from .components.prompt_editor import PromptEditor
from .components.dialogs import (
    NewPromptDialog,
    UnsavedChangesDialog,
    RenamePromptDialog,
    ConfirmDialog,
    CommandPaletteDialog,
    PromptHistoryDialog,
    TagInputDialog,
)
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
        "accent": "#2563EB",           # Native-like blue
        "accent_hover": "#1D4ED8",     # Darker blue
        "accent_glow": "#E8F0FF",      # Light blue
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
        "accent": "#4C8DFF",
        "accent_hover": "#3B7EF2",
        "accent_glow": "#1F2A3D",
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
        self._app_fade_job = None
        self._app_alpha_supported = False
        try:
            self.attributes("-alpha", 0.0)
            self._app_alpha_supported = True
        except Exception:
            self._app_alpha_supported = False
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
        self.filter_compact_labels: dict[str, str] = {}
        self.filter_tight_labels: dict[str, str] = {}
        self.filter_order: list[str] = []
        self._filter_label_mode = "full"
        self._command_palette: Optional[CommandPaletteDialog] = None
        self.preview_split_enabled = get_preview_split_enabled(False)
        self.token_count_mode = get_token_count_mode("approx")
        if self.token_count_mode not in ("approx", "exact"):
            self.token_count_mode = "approx"
        self.multi_select_mode = False
        self.ui_density_mode = get_ui_density_mode("native_lite")
        if self.ui_density_mode != "native_lite":
            self.ui_density_mode = "native_lite"
            set_ui_density_mode(self.ui_density_mode)
        self.bulk_frame = None
        self.bulk_count_label = None
        self.bulk_delete_btn = None
        self.bulk_export_btn = None
        self._dirty_ids_cache: set[str] = set()

        # Build UI
        self._build_ui()
        self._refresh_list()
        self._start_app_fade_in()
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self._bind_shortcuts()

    def _get_theme_colors(self) -> dict:
        return self.DARK_COLORS if self.theme == "dark" else self.LIGHT_COLORS

    def _btn_secondary_style(
        self,
        *,
        size: int = 11,
        weight: str = "normal",
        radius: int = 8,
        text_color: Optional[str] = None,
    ) -> dict:
        return {
            "corner_radius": radius,
            "font": ctk.CTkFont(family="Segoe UI", size=size, weight=weight),
            "fg_color": self.COLORS["surface"],
            "hover_color": self.COLORS["border"],
            "text_color": text_color or self.COLORS["text_secondary"],
            "border_width": 1,
            "border_color": self.COLORS["border"],
        }

    def _btn_primary_style(self, *, size: int = 11, weight: str = "bold", radius: int = 8) -> dict:
        return {
            "corner_radius": radius,
            "font": ctk.CTkFont(family="Segoe UI", size=size, weight=weight),
            "fg_color": self.COLORS["accent"],
            "hover_color": self.COLORS["accent_hover"],
        }

    def _btn_danger_style(self, *, size: int = 11, weight: str = "bold", radius: int = 8) -> dict:
        danger_hover = "#3B1F24" if self.theme == "dark" else "#FEE2E2"
        return {
            "corner_radius": radius,
            "font": ctk.CTkFont(family="Segoe UI", size=size, weight=weight),
            "fg_color": "transparent",
            "hover_color": danger_hover,
            "text_color": self.COLORS["danger"],
            "border_width": 1,
            "border_color": self.COLORS["border"],
        }

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
            **self._btn_primary_style(size=18, weight="normal", radius=16),
            command=self._on_new_prompt,
        )
        new_btn.pack(side="right")

        self.select_mode_btn = ctk.CTkButton(
            header,
            text="Select",
            width=70,
            height=32,
            **self._btn_secondary_style(size=11, weight="bold", radius=10),
            command=self._toggle_multi_select,
        )
        self.select_mode_btn.pack(side="right", padx=(0, 8))

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
            **self._btn_secondary_style(size=14, weight="bold", radius=10, text_color=self.COLORS["text_muted"]),
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
        self.filter_container = filter_container
        filter_container.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        filter_container.grid_propagate(False)
        for idx in range(6):
            filter_container.grid_columnconfigure(idx, weight=1, uniform="filters")

        self.filter_map = {
            "Pinned": "__pinned__",
            "All": None,
            "Persona": "Persona",
            "System": "System Prompt",
            "Template": "Template",
            "Other": "Other",
        }
        self.filter_labels = {
            "Pinned": "Pinned",
            "All": "All",
            "Persona": "Persona",
            "System": "System",
            "Template": "Template",
            "Other": "Other",
        }
        self.filter_compact_labels = {
            "Pinned": "Pin",
            "All": "All",
            "Persona": "Persona",
            "System": "System",
            "Template": "Templ",
            "Other": "Other",
        }
        self.filter_tight_labels = {
            "Pinned": "P",
            "All": "A",
            "Persona": "Per",
            "System": "Sys",
            "Template": "Tmp",
            "Other": "Oth",
        }
        self.filter_order = ["Pinned", "All", "Persona", "System", "Template", "Other"]

        for i, key in enumerate(self.filter_order):
            label = self.filter_labels[key]
            is_active = key == "All"
            btn = ctk.CTkButton(
                filter_container,
                text=label,
                width=1,
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
        self.filter_container.bind("<Configure>", self._on_filter_container_resize)

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

        # Keep UI scale value available for menu-based control.
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
            on_new_version=self._on_prompt_list_new_version,
            on_toggle_pin=self._on_prompt_list_toggle_pin,
            on_selection_change=self._on_selection_change,
            on_clear_search=self._clear_search,
            on_new_prompt=self._on_new_prompt,
            colors=self.COLORS,
        )
        self.prompt_list.grid(row=6, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.prompt_list.set_sort(self.sort_var.get())
        self._update_filter_counts()

        # Row 7: Bulk actions (hidden until multi-select)
        self.bulk_frame = ctk.CTkFrame(
            sidebar,
            fg_color=self.COLORS["sidebar_bg"],
            corner_radius=0,
            height=48,
        )
        self.bulk_frame.grid(row=7, column=0, sticky="ew")
        self.bulk_frame.grid_propagate(False)

        bulk_border = ctk.CTkFrame(self.bulk_frame, height=1, fg_color=self.COLORS["border"])
        bulk_border.pack(fill="x", side="top")

        bulk_inner = ctk.CTkFrame(self.bulk_frame, fg_color="transparent")
        bulk_inner.pack(fill="both", expand=True, padx=16, pady=8)

        # Minimal multi-select action row (keyboard handles selection mechanics).
        self.bulk_count_label = None

        self.bulk_export_btn = ctk.CTkButton(
            bulk_inner,
            text="⤓",
            width=36,
            height=28,
            **self._btn_secondary_style(size=13, weight="bold", radius=8),
            state="disabled",
            command=self._on_bulk_export,
        )
        self.bulk_export_btn.pack(side="right", padx=(0, 6))
        self._attach_hover_tooltip(self.bulk_export_btn, "Export selected")

        self.bulk_tag_btn = ctk.CTkButton(
            bulk_inner,
            text="#",
            width=36,
            height=28,
            **self._btn_secondary_style(size=13, weight="bold", radius=8),
            state="disabled",
            command=self._show_bulk_tag_menu,
        )
        self.bulk_tag_btn.pack(side="right", padx=(0, 6))
        self._attach_hover_tooltip(self.bulk_tag_btn, "Tag selected")

        self.bulk_delete_btn = ctk.CTkButton(
            bulk_inner,
            text="×",
            width=36,
            height=28,
            **self._btn_danger_style(size=14, weight="bold", radius=8),
            state="disabled",
            command=self._on_bulk_delete,
        )
        self.bulk_delete_btn.pack(side="right", padx=(0, 6))
        self._attach_hover_tooltip(self.bulk_delete_btn, "Delete selected")

        if self.multi_select_mode:
            self.bulk_frame.grid()
            self.select_mode_btn.configure(text="Done")
            self.select_mode_btn.configure(
                fg_color=self.COLORS["accent_glow"],
                text_color=self.COLORS["accent"],
            )
            self.prompt_list.set_multi_select_mode(True)
        else:
            self.bulk_frame.grid_remove()

        self.bulk_tag_menu = None

        # Row 8: Bottom utility actions (only high-value actions)
        footer = ctk.CTkFrame(
            sidebar,
            fg_color=self.COLORS["sidebar_bg"],
            corner_radius=0,
            height=52,
        )
        footer.grid(row=8, column=0, sticky="ew")
        footer.grid_propagate(False)

        footer_border = ctk.CTkFrame(footer, height=1, fg_color=self.COLORS["border"])
        footer_border.pack(fill="x", side="top")

        actions = ctk.CTkFrame(footer, fg_color="transparent")
        actions.pack(fill="both", expand=True, padx=10, pady=8)

        self.import_btn = ctk.CTkButton(
            actions,
            text="Import",
            height=30,
            **self._btn_secondary_style(size=11, radius=8),
            command=self._on_import,
        )
        self.import_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.export_btn = ctk.CTkButton(
            actions,
            text="Export",
            height=30,
            **self._btn_secondary_style(size=11, radius=8),
            command=self._on_export,
        )
        self.export_btn.pack(side="left", fill="x", expand=True, padx=4)

        self.library_btn = ctk.CTkButton(
            actions,
            text="Library...",
            height=30,
            **self._btn_secondary_style(size=11, radius=8),
            command=self._on_change_library_location,
        )
        self.library_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

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
            on_toggle_pin=self._on_prompt_list_toggle_pin,
            on_show_history=self._on_show_history,
            on_version_bump=self._on_version_bump,
            on_toast=self._show_toast,
            on_change=self._on_editor_change,
            on_autosave_draft=self._on_editor_autosave_draft,
            on_preview_toggle=self._on_editor_preview_toggle,
            colors=self.COLORS,
            preview_enabled=self.preview_split_enabled,
            token_mode=self.token_count_mode,
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
        self.bind_all("<Control-p>", lambda e: self._on_command_palette())
        self.bind_all("<Control-i>", lambda e: self._on_shortcut_snippets())
        self.bind_all("<Control-Shift-M>", lambda e: self._on_shortcut_toggle_preview())
        self.bind_all("<Control-Shift-V>", lambda e: self._on_shortcut_fill_variables())
        self.bind_all("<Control-l>", self._on_shortcut_toggle_select_mode)
        self.bind_all("<Control-a>", self._on_shortcut_select_all)
        self.bind_all("<Control-Shift-A>", self._on_shortcut_clear_selection)
        self.bind_all("<Up>", self._on_shortcut_select_up)
        self.bind_all("<Down>", self._on_shortcut_select_down)
        self.bind_all("<Shift-Up>", self._on_shortcut_select_up_extend)
        self.bind_all("<Shift-Down>", self._on_shortcut_select_down_extend)
        self.bind_all("<space>", self._on_shortcut_toggle_current_selection)
        self.bind_all("<Escape>", lambda e: self._on_escape())

    def _focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, "end")

    def _toggle_multi_select(self):
        self.multi_select_mode = not self.multi_select_mode
        self.prompt_list.set_multi_select_mode(self.multi_select_mode)
        if self.multi_select_mode:
            self.select_mode_btn.configure(text="Done")
            self.bulk_frame.grid()
            self.select_mode_btn.configure(
                fg_color=self.COLORS["accent_glow"],
                text_color=self.COLORS["accent"],
            )
        else:
            self.select_mode_btn.configure(text="Select")
            self.bulk_frame.grid_remove()
            self.select_mode_btn.configure(
                fg_color=self.COLORS["surface"],
                text_color=self.COLORS["text_secondary"],
            )
        self._on_selection_change(self.prompt_list.get_selected_prompts())

    def _is_text_input_focus(self) -> bool:
        widget = self.focus_get()
        if widget is None:
            return False
        cls = widget.winfo_class().lower()
        if cls in {"entry", "text", "tentry", "ctkentry", "ctktextbox"}:
            return True
        return False

    def _on_shortcut_toggle_select_mode(self, event=None):
        if self._is_text_input_focus():
            return
        self._toggle_multi_select()
        return "break"

    def _on_shortcut_select_all(self, event=None):
        if self._is_text_input_focus():
            return
        if not self.multi_select_mode:
            self._toggle_multi_select()
        self.prompt_list.select_all()
        return "break"

    def _on_shortcut_clear_selection(self, event=None):
        if not self.multi_select_mode:
            return
        self.prompt_list.clear_selection()
        return "break"

    def _can_handle_select_nav(self) -> bool:
        if not self.multi_select_mode:
            return False
        if self._is_text_input_focus():
            return False
        widget = self.focus_get()
        if widget is not None and widget.winfo_toplevel() is not self:
            return False
        return True

    def _on_shortcut_select_up(self, event=None):
        if not self._can_handle_select_nav():
            return
        if self.prompt_list.keyboard_move_selection(-1, extend=False):
            return "break"

    def _on_shortcut_select_down(self, event=None):
        if not self._can_handle_select_nav():
            return
        if self.prompt_list.keyboard_move_selection(1, extend=False):
            return "break"

    def _on_shortcut_select_up_extend(self, event=None):
        if not self._can_handle_select_nav():
            return
        if self.prompt_list.keyboard_move_selection(-1, extend=True):
            return "break"

    def _on_shortcut_select_down_extend(self, event=None):
        if not self._can_handle_select_nav():
            return
        if self.prompt_list.keyboard_move_selection(1, extend=True):
            return "break"

    def _on_shortcut_toggle_current_selection(self, event=None):
        if not self._can_handle_select_nav():
            return
        if self.prompt_list.keyboard_toggle_active():
            return "break"

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

    def _on_command_palette(self):
        if self._command_palette and self._command_palette.winfo_exists():
            self._command_palette.focus_set()
            return
        self._command_palette = CommandPaletteDialog(
            self,
            prompts=self.prompts,
            colors=self.COLORS,
            on_select=self._on_prompt_select,
            actions=self._get_palette_actions(),
            on_action=self._run_palette_action,
        )

    def _get_palette_actions(self) -> list[dict[str, str]]:
        return [
            {"id": "new_prompt", "label": "New prompt", "keywords": "create add", "shortcut": "Ctrl+N"},
            {"id": "duplicate_prompt", "label": "Duplicate current", "keywords": "clone copy", "shortcut": "Ctrl+D"},
            {"id": "focus_search", "label": "Focus search", "keywords": "find filter list", "shortcut": "Ctrl+F"},
            {"id": "toggle_preview", "label": "Toggle preview split", "keywords": "markdown preview split", "shortcut": "Ctrl+Shift+M"},
            {"id": "open_snippets", "label": "Insert snippet", "keywords": "snippet template quick insert", "shortcut": "Ctrl+I"},
            {"id": "fill_variables", "label": "Fill variables", "keywords": "placeholder variable", "shortcut": "Ctrl+Shift+V"},
            {"id": "toggle_token_mode", "label": "Toggle token mode", "keywords": "token count approx exact"},
            {"id": "toggle_pin", "label": "Toggle pin", "keywords": "favorite star pinned"},
        ]

    def _run_palette_action(self, action_id: str):
        if action_id == "new_prompt":
            self._on_new_prompt()
            return
        if action_id == "duplicate_prompt":
            self._on_duplicate_prompt()
            return
        if action_id == "focus_search":
            self._focus_search()
            return
        if action_id == "toggle_preview":
            self._toggle_preview()
            return
        if action_id == "open_snippets":
            self.editor.open_snippet_picker()
            return
        if action_id == "fill_variables":
            self.editor.fill_variables()
            return
        if action_id == "toggle_token_mode":
            self._toggle_token_mode()
            return
        if action_id == "toggle_pin" and self.current_prompt:
            self._on_prompt_list_toggle_pin(self.current_prompt)
            return

    def _toggle_token_mode(self):
        self.token_count_mode = "exact" if self.token_count_mode == "approx" else "approx"
        self.editor.token_mode = self.token_count_mode
        self.editor._update_char_count()
        set_token_count_mode(self.token_count_mode)
        self._show_toast(f"Token mode: {self.token_count_mode}")

    def _toggle_theme(self, theme: Optional[str] = None):
        if theme in ("light", "dark"):
            self.theme = theme
        elif self.theme == "dark":
            self.theme = "light"
        else:
            self.theme = "dark"
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
                "tags": self.editor.get_tags(),
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
            if isinstance(draft, dict):
                self.editor.set_draft(draft)
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

    def _on_shortcut_snippets(self):
        if not self.current_prompt:
            return
        self.editor.open_snippet_picker()
        return "break"

    def _on_shortcut_fill_variables(self):
        if not self.current_prompt:
            return
        self.editor.fill_variables()
        return "break"

    def _on_shortcut_toggle_preview(self):
        self._toggle_preview()
        return "break"

    def _toggle_preview(self):
        self.editor.toggle_preview()
        self.preview_split_enabled = self.editor.preview_enabled
        set_preview_split_enabled(self.preview_split_enabled)

    def _on_escape(self):
        widget = self.focus_get()
        if widget is not None and widget.winfo_toplevel() is not self:
            return
        if self.multi_select_mode:
            if self.prompt_list.get_selected_prompts():
                self.prompt_list.clear_selection()
            else:
                self._toggle_multi_select()
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
        self._refresh_dirty_prompt_markers(include_disk_drafts=True)
        self._update_count()
        self._update_filter_counts()
        if self.multi_select_mode:
            self._on_selection_change(self.prompt_list.get_selected_prompts())
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
        if cat_value == "__pinned__":
            self.prompt_list.set_pinned_only(True)
            self.prompt_list.set_category_filter(None)
        else:
            self.prompt_list.set_pinned_only(False)
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
                or term in (getattr(prompt, "custom_category", "") or "").lower()
                or any(term in t.lower() for t in prompt.tags)
            )

        counts: dict[str, int] = {key: 0 for key in self.filter_order}
        for prompt in self.prompts:
            if not matches_search(prompt):
                continue
            if prompt.pinned:
                counts["Pinned"] += 1
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
            label = self._filter_label_for_mode(key)
            count = counts.get(key, 0)
            if self._filter_label_mode == "tight":
                btn.configure(text=f"{label} {count}")
            else:
                btn.configure(text=f"{label} ({count})")

    def _filter_label_for_mode(self, key: str) -> str:
        if self._filter_label_mode == "tight":
            return self.filter_tight_labels.get(key, self.filter_labels.get(key, key))
        if self._filter_label_mode == "compact":
            return self.filter_compact_labels.get(key, self.filter_labels.get(key, key))
        return self.filter_labels.get(key, key)

    def _on_filter_container_resize(self, event):
        per_button_width = max(1, int(event.width / max(1, len(self.filter_order))))
        if per_button_width < 74:
            label_mode = "tight"
        elif per_button_width < 105:
            label_mode = "compact"
        else:
            label_mode = "full"
        if label_mode != self._filter_label_mode:
            self._filter_label_mode = label_mode
            self._update_filter_counts()

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
        draft = self.storage.load_draft(prompt.id)
        if isinstance(draft, dict) and self._draft_differs_from_prompt(prompt, draft):
            self.editor.set_draft(draft)
            self._recalculate_unsaved_state()
        else:
            # Clean up stale drafts that no longer differ from saved prompt.
            self.storage.clear_draft(prompt.id)
            self._recalculate_unsaved_state()

    def _on_new_prompt(self):
        """Open new prompt dialog."""
        dialog = NewPromptDialog(self, on_create=self._create_prompt, colors=self.COLORS)
        dialog.focus_set()

    def _create_prompt(self, prompt: Prompt):
        """Create new prompt."""
        self.storage.add_prompt(prompt)
        self._refresh_list()
        self.current_prompt = prompt
        self.has_unsaved_changes = False
        self.editor.set_prompt(prompt)
        self._show_toast("Prompt created")

    def _on_save(self, prompt: Prompt):
        """Save prompt."""
        self._save_prompt(prompt, toast_message="Changes saved")

    def _on_delete(self, prompt_id: str):
        """Delete prompt."""
        self.storage.delete_prompt(prompt_id)
        self.storage.clear_draft(prompt_id)
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

        if not self._resolve_unsaved_changes(prompt.id):
            return

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

    def _on_prompt_list_new_version(self, prompt: Prompt):
        """Create a new prompt version from list context menu."""
        if not self._resolve_unsaved_changes(prompt.id):
            return

        source_prompt = self._get_prompt_by_id(prompt.id)
        if not source_prompt:
            self._show_toast("Versioning failed: prompt not found")
            return

        self._create_new_prompt_version(source_prompt)

    def _on_selection_change(self, selected: list[Prompt]):
        count = len(selected)
        has_selected = count > 0
        if self.bulk_delete_btn:
            state = "normal" if has_selected else "disabled"
            self.bulk_delete_btn.configure(state=state)
        if self.bulk_export_btn:
            state = "normal" if has_selected else "disabled"
            self.bulk_export_btn.configure(state=state)
        if self.bulk_tag_btn:
            state = "normal" if has_selected else "disabled"
            self.bulk_tag_btn.configure(state=state)

    def _on_bulk_select_all(self):
        if not self.multi_select_mode:
            return
        self.prompt_list.select_all()

    def _on_bulk_clear(self):
        if not self.multi_select_mode:
            return
        self.prompt_list.clear_selection()

    def _on_bulk_export(self):
        if not self.multi_select_mode:
            return
        selected = self.prompt_list.get_selected_prompts()
        if not selected:
            return
        if self.current_prompt and self.current_prompt.id in {p.id for p in selected}:
            if not self._resolve_unsaved_changes(self.current_prompt.id):
                return
        filepath = filedialog.asksaveasfilename(
            title="Export Selected Prompts",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="prompts_selected.json",
        )
        if filepath:
            self.storage.export_prompts_to_file(selected, filepath)
            self._show_toast(f"Exported {len(selected)} prompts")

    def _on_bulk_delete(self):
        if not self.multi_select_mode:
            return
        selected = self.prompt_list.get_selected_prompts()
        if not selected:
            return
        if self.current_prompt and self.current_prompt.id in {p.id for p in selected}:
            if not self._resolve_unsaved_changes(self.current_prompt.id):
                return
        dialog = ConfirmDialog(
            self,
            colors=self.COLORS,
            title="Delete prompts",
            message=f"Delete {len(selected)} selected prompts? This cannot be undone.",
            confirm_text="Delete",
            cancel_text="Cancel",
        )
        self.wait_window(dialog)
        if dialog.result != "confirm":
            return
        deleted = self.storage.delete_prompts([p.id for p in selected])
        if self.current_prompt and self.current_prompt.id in {p.id for p in selected}:
            self.editor.clear()
            self.current_prompt = None
        self.prompt_list.clear_selection()
        self._refresh_list()
        self._show_toast(f"Deleted {deleted} prompts")

    def _show_bulk_tag_menu(self):
        if not self.multi_select_mode:
            return
        if self.bulk_tag_menu is None:
            import tkinter as tk

            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Add tag", command=self._on_bulk_add_tag)
            menu.add_command(label="Remove tag", command=self._on_bulk_remove_tag)
            self.bulk_tag_menu = menu
        x = self.bulk_tag_btn.winfo_rootx()
        y = self.bulk_tag_btn.winfo_rooty() + self.bulk_tag_btn.winfo_height()
        self.bulk_tag_menu.tk_popup(x, y)

    def _on_bulk_add_tag(self):
        self._bulk_tag_action("add")

    def _on_bulk_remove_tag(self):
        self._bulk_tag_action("remove")

    def _bulk_tag_action(self, mode: str):
        if not self.multi_select_mode:
            return
        selected = self.prompt_list.get_selected_prompts()
        if not selected:
            return
        if self.current_prompt and self.current_prompt.id in {p.id for p in selected}:
            if not self._resolve_unsaved_changes(self.current_prompt.id):
                return

        title = "Add tag to prompts" if mode == "add" else "Remove tag from prompts"
        confirm = "Add" if mode == "add" else "Remove"
        dialog = TagInputDialog(self, colors=self.COLORS, title=title, confirm_text=confirm)
        self.wait_window(dialog)
        tag = dialog.result
        if not tag:
            return

        for prompt in selected:
            tags = list(prompt.tags)
            if mode == "add":
                if not any(t.lower() == tag.lower() for t in tags):
                    tags.append(tag)
            else:
                tags = [t for t in tags if t.lower() != tag.lower()]
            prompt.tags = tags
            self.storage.update_prompt(prompt)
            if self.current_prompt and prompt.id == self.current_prompt.id:
                self.current_prompt.tags = tags

        self._refresh_list()
        action_label = "Added" if mode == "add" else "Removed"
        self._show_toast(f"{action_label} tag '{tag}' on {len(selected)} prompts")

    def _resolve_unsaved_changes(self, prompt_id: str) -> bool:
        if not self.has_unsaved_changes:
            return True
        if not self.current_prompt or self.current_prompt.id != prompt_id:
            return True
        action = self._confirm_unsaved_changes()
        if action == "cancel":
            return False
        if action == "save":
            self.editor.save_current_prompt()
            return True
        if action == "discard":
            current_prompts = self.storage.load_prompts()
            stored = next((p for p in current_prompts if p.id == prompt_id), None)
            if stored:
                self.current_prompt = stored
                self.editor.set_prompt(stored)
            self.has_unsaved_changes = False
            self.editor.update_save_state(False)
            return True
        return True

    def _on_prompt_list_toggle_pin(self, prompt: Prompt):
        """Toggle pinned state from list."""
        prompt.pinned = not bool(getattr(prompt, "pinned", False))
        self._save_prompt(prompt, toast_message="Pinned" if prompt.pinned else "Unpinned")

    def _on_show_history(self, prompt: Prompt):
        """Open version history for a prompt."""
        if not self._resolve_unsaved_changes(prompt.id):
            return

        PromptHistoryDialog(
            self,
            prompt=prompt,
            colors=self.COLORS,
            on_restore=lambda v: self._restore_version(prompt, v),
        )

    def _restore_version(self, prompt: Prompt, version: dict):
        """Restore a prior version of a prompt."""
        dialog = ConfirmDialog(
            self,
            colors=self.COLORS,
            title="Restore version",
            message="Replace the current prompt with this version?",
            confirm_text="Restore",
            cancel_text="Cancel",
        )
        self.wait_window(dialog)
        if dialog.result != "confirm":
            return

        prompt.name = version.get("name", prompt.name)
        prompt.content = version.get("content", prompt.content)
        category_value = version.get("category", prompt.category.value)
        try:
            prompt.category = Category(category_value)
        except Exception:
            prompt.category = Category.OTHER
        prompt.tags = list(version.get("tags", prompt.tags) or [])
        prompt.sensitive = bool(version.get("sensitive", prompt.sensitive))
        prompt.pinned = bool(version.get("pinned", prompt.pinned))
        prompt.custom_category = str(version.get("custom_category", getattr(prompt, "custom_category", "")) or "")
        self._save_prompt(prompt, toast_message="Version restored")

    def _on_version_bump(self, prompt: Prompt):
        """Create a new visible version from the current editor state."""
        if not self.current_prompt or self.current_prompt.id != prompt.id:
            return

        source_data = {
            "name": self.editor.name_entry.get().strip() or prompt.name,
            "content": self.editor._get_current_content(),
            "category": self.editor.category_var.get(),
            "custom_category": self.editor.custom_category.strip(),
            "tags": self.editor.get_tags(),
            "sensitive": bool(self.editor.sensitive_var.get()),
            "pinned": bool(prompt.pinned),
        }

        # Preserve any unsaved work on the current prompt as a draft before switching.
        if self.has_unsaved_changes:
            self.storage.save_draft(prompt.id, source_data)

        self._create_new_prompt_version(prompt, source_data=source_data)

    def _create_new_prompt_version(self, prompt: Prompt, source_data: Optional[dict] = None):
        family_id = getattr(prompt, "version_group_id", "") or prompt.id
        existing_versions = [
            p for p in self.prompts
            if (getattr(p, "version_group_id", "") or p.id) == family_id
        ]
        max_version = max(
            [max(1, int(getattr(p, "version_number", 1) or 1)) for p in existing_versions] or [1]
        )
        next_version = max_version + 1

        raw_name = (
            str(source_data.get("name", prompt.name))
            if isinstance(source_data, dict)
            else prompt.name
        )
        base_name = self._strip_version_suffix(raw_name)
        version_name = f"{base_name} v{next_version}".strip()

        raw_category = (
            source_data.get("category", prompt.category.value)
            if isinstance(source_data, dict)
            else prompt.category.value
        )
        try:
            category = Category(raw_category)
        except Exception:
            category = Category.OTHER

        tags = source_data.get("tags", prompt.tags) if isinstance(source_data, dict) else prompt.tags
        custom_category = (
            str(source_data.get("custom_category", getattr(prompt, "custom_category", "")) or "")
            if isinstance(source_data, dict)
            else str(getattr(prompt, "custom_category", "") or "")
        )
        content = (
            str(source_data.get("content", prompt.content))
            if isinstance(source_data, dict)
            else prompt.content
        )
        sensitive = (
            bool(source_data.get("sensitive", prompt.sensitive))
            if isinstance(source_data, dict)
            else bool(prompt.sensitive)
        )
        pinned = (
            bool(source_data.get("pinned", prompt.pinned))
            if isinstance(source_data, dict)
            else bool(prompt.pinned)
        )

        new_prompt = Prompt(
            name=version_name,
            content=content,
            category=category,
            tags=list(tags) if isinstance(tags, list) else [],
            custom_category=custom_category.strip() if category == Category.OTHER else "",
            sensitive=sensitive,
            pinned=pinned,
            version_group_id=family_id,
            version_number=next_version,
            previous_version_id=prompt.id,
        )

        self.storage.add_prompt(new_prompt)
        self._refresh_list()
        self.current_prompt = new_prompt
        self.has_unsaved_changes = False
        self.editor.set_prompt(new_prompt)
        self.editor.update_save_state(False)
        self.prompt_list.set_selected_prompt(new_prompt)
        self._show_toast(f"Created {version_name}")

    def _strip_version_suffix(self, name: str) -> str:
        clean = (name or "").strip()
        match = re.search(r"(?:\s+v)(\d+)$", clean, re.IGNORECASE)
        if match:
            clean = clean[: match.start()].strip()
        return clean or "Prompt"

    def _get_prompt_by_id(self, prompt_id: str) -> Optional[Prompt]:
        for prompt in self.prompts:
            if prompt.id == prompt_id:
                return prompt
        return None

    def _save_prompt(self, prompt: Prompt, toast_message: Optional[str] = "Changes saved"):
        """Persist prompt and refresh UI."""
        self.storage.update_prompt(prompt)
        self.storage.clear_draft(prompt.id)
        self.current_prompt = prompt
        self.has_unsaved_changes = False
        self._refresh_list()
        self.editor.set_prompt(prompt)
        self.editor.update_save_state(False)
        if toast_message:
            self._show_toast(toast_message)

    def _on_editor_change(self):
        """Handle editor content change."""
        self._recalculate_unsaved_state()

    def _on_editor_autosave_draft(self, prompt_id: str, draft: dict):
        if not prompt_id:
            return
        prompt = self._get_prompt_by_id(prompt_id)
        if prompt and self._draft_differs_from_prompt(prompt, draft):
            self.storage.save_draft(prompt_id, draft)
        else:
            self.storage.clear_draft(prompt_id)
        self._refresh_dirty_prompt_markers(include_disk_drafts=True)

    def _recalculate_unsaved_state(self):
        """Recompute unsaved state by comparing editor state with persisted prompt."""
        self.has_unsaved_changes = self._is_editor_modified()
        self.editor.update_save_state(self.has_unsaved_changes)
        self._refresh_dirty_prompt_markers(include_disk_drafts=False)

    def _is_editor_modified(self) -> bool:
        if not self.current_prompt:
            return False
        prompt_state = self._canonical_prompt_state(self.current_prompt)
        editor_state = self._canonical_editor_state()
        return editor_state != prompt_state

    def _draft_differs_from_prompt(self, prompt: Prompt, draft: dict) -> bool:
        prompt_state = self._canonical_prompt_state(prompt)
        draft_state = self._canonical_draft_state(draft, fallback_prompt=prompt)
        return draft_state != prompt_state

    def _canonical_prompt_state(self, prompt: Prompt) -> dict:
        category_value = prompt.category.value if isinstance(prompt.category, Category) else str(prompt.category)
        custom_category = (getattr(prompt, "custom_category", "") or "").strip()
        if category_value != Category.OTHER.value:
            custom_category = ""
        return {
            "name": (prompt.name or "").strip(),
            "category": category_value,
            "custom_category": custom_category,
            "tags": self._normalize_tags(prompt.tags),
            "content": prompt.content or "",
            "sensitive": bool(prompt.sensitive),
        }

    def _canonical_editor_state(self) -> dict:
        if not self.current_prompt:
            return {"name": "", "category": Category.OTHER.value, "tags": [], "content": "", "sensitive": False}
        category_value = self.editor.category_var.get() or Category.OTHER.value
        custom_category = (self.editor.custom_category or "").strip()
        if category_value != Category.OTHER.value:
            custom_category = ""
        return {
            "name": self.editor.name_entry.get().strip(),
            "category": category_value,
            "custom_category": custom_category,
            "tags": self._normalize_tags(self.editor.get_tags()),
            "content": self.editor._get_current_content(),
            "sensitive": bool(self.editor.sensitive_var.get()),
        }

    def _canonical_draft_state(self, draft: dict, fallback_prompt: Prompt) -> dict:
        if not isinstance(draft, dict):
            return self._canonical_prompt_state(fallback_prompt)
        category_value = str(draft.get("category", fallback_prompt.category.value) or Category.OTHER.value)
        custom_category = str(
            draft.get("custom_category", getattr(fallback_prompt, "custom_category", "")) or ""
        ).strip()
        if category_value != Category.OTHER.value:
            custom_category = ""
        return {
            "name": str(draft.get("name", fallback_prompt.name)).strip(),
            "category": category_value,
            "custom_category": custom_category,
            "tags": self._normalize_tags(draft.get("tags", fallback_prompt.tags)),
            "content": str(draft.get("content", fallback_prompt.content) or ""),
            "sensitive": bool(draft.get("sensitive", fallback_prompt.sensitive)),
        }

    def _normalize_tags(self, tags: object) -> list[str]:
        if not isinstance(tags, list):
            return []
        return [str(tag).strip() for tag in tags if str(tag).strip()]

    def _refresh_dirty_prompt_markers(self, include_disk_drafts: bool = True):
        """Mark prompts with drafts/unsaved edits in the list UI."""
        by_id = {p.id: p for p in self.prompts}

        if include_disk_drafts:
            dirty_ids: set[str] = set()
            drafts = self.storage.load_drafts()
            for prompt_id, draft in drafts.items():
                prompt = by_id.get(prompt_id)
                if prompt and self._draft_differs_from_prompt(prompt, draft):
                    dirty_ids.add(prompt_id)
            self._dirty_ids_cache = dirty_ids

        dirty_ids = {pid for pid in self._dirty_ids_cache if pid in by_id}

        if self.current_prompt and self.has_unsaved_changes:
            dirty_ids.add(self.current_prompt.id)

        self.prompt_list.set_dirty_ids(dirty_ids)

    def _on_editor_preview_toggle(self, enabled: bool):
        self.preview_split_enabled = bool(enabled)
        set_preview_split_enabled(self.preview_split_enabled)

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
        tags = self.editor.get_tags()
        category = Category(self.editor.category_var.get())
        custom_category = self.editor.custom_category.strip()

        new_prompt = Prompt(
            name=f"{name} (copy)",
            content=content,
            category=category,
            tags=tags,
            custom_category=custom_category if category == Category.OTHER else "",
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
        if self._app_fade_job is not None:
            try:
                self.after_cancel(self._app_fade_job)
            except Exception:
                pass
            self._app_fade_job = None
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

    def _start_app_fade_in(self):
        if not self._app_alpha_supported:
            return
        self._animate_app_alpha(0.0)

    def _animate_app_alpha(self, value: float):
        if not self.winfo_exists():
            return
        next_value = min(1.0, value + 0.12)
        try:
            self.attributes("-alpha", next_value)
        except Exception:
            return
        if next_value < 1.0:
            self._app_fade_job = self.after(16, lambda: self._animate_app_alpha(next_value))

    def _attach_hover_tooltip(self, widget, text: str):
        widget.bind("<Enter>", lambda e, t=text: self._schedule_tooltip(e, t))
        widget.bind("<Leave>", lambda _e: self._hide_tooltip())
        widget.bind("<ButtonPress>", lambda _e: self._hide_tooltip())

    def _schedule_tooltip(self, event, text: str):
        self._hide_tooltip()
        self._tooltip_after_id = self.after(280, lambda: self._show_tooltip(event, text))

    def _show_tooltip(self, event, text: str):
        self._tooltip_after_id = None
        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.configure(bg=self.COLORS["toast_bg"])

        label = tk.Label(
            tip,
            text=text,
            bg=self.COLORS["toast_bg"],
            fg=self.COLORS["toast_text"],
            padx=8,
            pady=4,
            font=("Segoe UI", 9),
        )
        label.pack()

        x = event.x_root
        y = event.y_root - 28
        tip.wm_geometry(f"+{x}+{y}")
        self._tooltip_window = tip

    def _hide_tooltip(self):
        if hasattr(self, "_tooltip_after_id") and self._tooltip_after_id is not None:
            try:
                self.after_cancel(self._tooltip_after_id)
            except Exception:
                pass
            self._tooltip_after_id = None
        tip = getattr(self, "_tooltip_window", None)
        if tip is not None:
            try:
                tip.destroy()
            except Exception:
                pass
            self._tooltip_window = None


def run():
    """Run the application."""
    app = PromptLibraryApp()
    app.mainloop()

