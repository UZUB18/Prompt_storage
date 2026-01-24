"""Main application window - Apple 2026 Edition."""
import customtkinter as ctk
from tkinter import filedialog
from typing import Optional
from datetime import datetime

from .models import Prompt, Category
from .storage import Storage
from .components.prompt_list import PromptList
from .components.prompt_editor import PromptEditor
from .components.dialogs import NewPromptDialog
from .components.toast import Toast


class PromptLibraryApp(ctk.CTk):
    """Main application window with Apple 2026 design."""

    # Design tokens - Apple 2026 Edition
    COLORS = {
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
        "text_primary": "#1D1D1F",     # Near-black
        "text_secondary": "#6E6E73",   # Gray
        "text_muted": "#86868B",       # Light gray
        "category_bg": "#F3EBFF",      # Light violet background
    }

    def __init__(self):
        super().__init__()

        # Configure appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("Prompt Library Pro")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.configure(fg_color=self.COLORS["bg"])

        # State
        self.storage = Storage()
        self.prompts = self.storage.load_prompts()
        self.current_prompt: Optional[Prompt] = None
        self.has_unsaved_changes = False
        self.active_filter = "All"

        # Build UI
        self._build_ui()
        self._refresh_list()

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
        sidebar.grid_rowconfigure(4, weight=1)  # Prompt list expands

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

        # Row 1: Search field
        self.search_entry = ctk.CTkEntry(
            sidebar,
            height=36,
            placeholder_text="🔍 Search...",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=self.COLORS["surface"],
            border_color=self.COLORS["border"],
            border_width=1,
            corner_radius=10,
            text_color=self.COLORS["text_primary"],
        )
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # Row 2: Segmented filter control (compact)
        filter_container = ctk.CTkFrame(
            sidebar,
            fg_color="#E5E5EA",
            corner_radius=8,
            height=32,
        )
        filter_container.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        filter_container.grid_propagate(False)
        filter_container.grid_columnconfigure((0,1,2,3), weight=1)

        self.filter_buttons = {}
        # Use shorter display names that fit better
        self.filter_map = {
            "All": None,
            "Pers": "Persona",
            "Sys": "System Prompt",
            "Tmpl": "Template",
        }
        
        for i, (display_name, cat_value) in enumerate(self.filter_map.items()):
            is_active = display_name == "All"
            btn = ctk.CTkButton(
                filter_container,
                text=display_name,
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if is_active else "normal"),
                fg_color=self.COLORS["surface"] if is_active else "transparent",
                hover_color=self.COLORS["surface"],
                text_color=self.COLORS["accent"] if is_active else self.COLORS["text_secondary"],
                border_width=0,
                command=lambda d=display_name: self._on_filter(d),
            )
            btn.grid(row=0, column=i, sticky="ew", padx=2, pady=2)
            self.filter_buttons[display_name] = btn

        # Row 3: Count label
        self.count_label = ctk.CTkLabel(
            sidebar,
            text="0 PROMPTS",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.COLORS["text_muted"],
        )
        self.count_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 6))

        # Row 4: Prompt list (EXPANDS)
        self.prompt_list = PromptList(
            sidebar,
            on_select=self._on_prompt_select,
            colors=self.COLORS,
        )
        self.prompt_list.grid(row=4, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # Row 5: Footer actions
        footer = ctk.CTkFrame(
            sidebar, 
            fg_color=self.COLORS["sidebar_bg"],
            corner_radius=0,
            height=56,
        )
        footer.grid(row=5, column=0, sticky="ew")
        footer.grid_propagate(False)

        # Top border for footer
        footer_border = ctk.CTkFrame(footer, height=1, fg_color=self.COLORS["border"])
        footer_border.pack(fill="x", side="top")

        btn_container = ctk.CTkFrame(footer, fg_color="transparent")
        btn_container.pack(fill="both", expand=True, padx=16, pady=12)

        import_btn = ctk.CTkButton(
            btn_container,
            text="↑ Import",
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
            text="↓ Export",
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
            on_change=self._on_editor_change,
            colors=self.COLORS,
        )
        self.editor.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

    def _refresh_list(self):
        """Refresh the prompt list."""
        self.prompts = self.storage.load_prompts()
        self.prompt_list.set_prompts(self.prompts)
        self._update_count()

    def _update_count(self):
        """Update prompt count."""
        count = len(self.prompt_list.filtered_prompts)
        total = len(self.prompts)
        if count == total:
            self.count_label.configure(text=f"{count} PROMPTS")
        else:
            self.count_label.configure(text=f"{count} OF {total} PROMPTS")

    def _on_search(self, event=None):
        """Handle search."""
        self.prompt_list.set_search(self.search_entry.get())
        self._update_count()

    def _on_filter(self, display_name: str):
        """Handle filter chip click."""
        self.active_filter = display_name
        
        # Update chip styles
        for name, btn in self.filter_buttons.items():
            if name == display_name:
                btn.configure(
                    fg_color=self.COLORS["surface"],
                    text_color=self.COLORS["accent"],
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.COLORS["text_secondary"],
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
                )

        # Apply filter using the mapped category value
        cat_value = self.filter_map.get(display_name)
        if cat_value is None:
            self.prompt_list.set_category_filter(None)
        else:
            self.prompt_list.set_category_filter(Category(cat_value))
        self._update_count()

    def _on_prompt_select(self, prompt: Prompt):
        """Handle prompt selection."""
        self.current_prompt = prompt
        self.has_unsaved_changes = False
        self.editor.set_prompt(prompt)

    def _on_new_prompt(self):
        """Open new prompt dialog."""
        dialog = NewPromptDialog(self, on_create=self._create_prompt, colors=self.COLORS)
        dialog.focus()

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

    def _on_import(self):
        """Import prompts."""
        filepath = filedialog.askopenfilename(
            title="Import Prompts",
            filetypes=[("JSON files", "*.json")],
        )
        if filepath:
            count = self.storage.import_from_file(filepath)
            self._refresh_list()
            self._show_toast(f"Imported {count} prompts")

    def _show_toast(self, message: str):
        """Show toast notification."""
        Toast(self, message, colors=self.COLORS)


def run():
    """Run the application."""
    app = PromptLibraryApp()
    app.mainloop()
