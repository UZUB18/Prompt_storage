"""Dialog components - Apple 2026 Edition."""
import customtkinter as ctk
from typing import Callable, Dict, List

from ..models import Prompt, Category


class NewPromptDialog(ctk.CTkToplevel):
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
        self.colors = colors

        self.title("New Prompt")
        self.geometry("520x680")
        self.resizable(False, False)
        self.configure(fg_color=colors["bg"])

        self.transient(master)
        self.grab_set()

        # Card container
        card = ctk.CTkFrame(
            self,
            fg_color=colors["surface"],
            corner_radius=16,
        )
        card.pack(fill="both", expand=True, padx=20, pady=20)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=28, pady=28)

        # Title
        title = ctk.CTkLabel(
            content,
            text="Create New Prompt",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=colors["text_primary"],
        )
        title.pack(anchor="w", pady=(0, 24))

        # Name field
        name_label = ctk.CTkLabel(
            content,
            text="NAME",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["text_muted"],
            anchor="w",
        )
        name_label.pack(fill="x", pady=(0, 8), padx=4)

        self.name_entry = ctk.CTkEntry(
            content,
            height=44,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=12,
            text_color=colors["text_primary"],
            placeholder_text="Enter prompt name...",
        )
        self.name_entry.pack(fill="x", pady=(0, 20))

        # Category field
        cat_label = ctk.CTkLabel(
            content,
            text="CATEGORY",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["text_muted"],
            anchor="w",
        )
        cat_label.pack(fill="x", pady=(0, 8), padx=4)

        self.category_var = ctk.StringVar(value=Category.OTHER.value)
        # CTkOptionMenu doesn't render an entry-like border by default; wrap it.
        cat_outer = ctk.CTkFrame(
            content,
            fg_color=colors["surface"],
            corner_radius=12,
            border_width=1,
            border_color=colors["border"],
        )
        cat_outer.pack(fill="x", pady=(0, 20))
        self.category_dropdown = ctk.CTkOptionMenu(
            cat_outer,
            values=[c.value for c in Category],
            variable=self.category_var,
            height=42,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=colors["surface"],
            text_color=colors["text_primary"],
            button_color=colors["surface"],
            button_hover_color=colors["bg"],
            dropdown_fg_color=colors["surface"],
            dropdown_text_color=colors["text_primary"],
            dropdown_hover_color=colors["accent_glow"],
            corner_radius=11,
        )
        self.category_dropdown.pack(fill="x", padx=1, pady=1)

        # Tags field
        tags_label = ctk.CTkLabel(
            content,
            text="TAGS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["text_muted"],
            anchor="w",
        )
        tags_label.pack(fill="x", pady=(0, 8), padx=4)

        self.tags_entry = ctk.CTkEntry(
            content,
            height=44,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=12,
            text_color=colors["text_primary"],
            placeholder_text="Comma-separated tags...",
        )
        self.tags_entry.pack(fill="x", pady=(0, 20))

        # Content field
        content_label = ctk.CTkLabel(
            content,
            text="CONTENT",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["text_muted"],
            anchor="w",
        )
        content_label.pack(fill="x", pady=(0, 8), padx=4)

        self.content_text = ctk.CTkTextbox(
            content,
            height=140,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=colors["surface"],
            text_color=colors["text_primary"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=12,
            wrap="word",
        )
        self.content_text.pack(fill="x", pady=(0, 24))

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            height=44,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color="transparent",
            hover_color=colors["border"],
            text_color=colors["text_secondary"],
            border_width=1,
            border_color=colors["border"],
            command=self.destroy,
        )
        cancel_btn.pack(side="left")

        create_btn = ctk.CTkButton(
            btn_frame,
            text="Create",
            width=100,
            height=44,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            command=self._on_create,
        )
        create_btn.pack(side="right")

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
            tags=[t.strip() for t in self.tags_entry.get().split(",") if t.strip()],
        )

        self.on_create(prompt)
        self.destroy()


class VariableInputDialog(ctk.CTkToplevel):
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
        self.colors = colors
        self.variables = variables
        self.entries = {}

        self.title("Variables Required")
        height = min(600, 220 + len(variables) * 90)
        self.geometry(f"450x{height}")
        self.resizable(True, True)
        self.configure(fg_color=colors["bg"])
        
        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 450) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"+{x}+{y}")

        self.transient(master)
        self.grab_set()

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

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            height=44,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color="transparent",
            hover_color=colors["border"],
            text_color=colors["text_secondary"],
            border_width=1,
            border_color=colors["border"],
            command=self.destroy,
        )
        cancel_btn.pack(side="left")

        submit_btn = ctk.CTkButton(
            btn_frame,
            text="Insert",
            width=100,
            height=44,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            command=self._on_submit,
        )
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


class UnsavedChangesDialog(ctk.CTkToplevel):
    """Dialog for unsaved changes confirmation."""

    def __init__(self, master, colors: Dict[str, str], **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.result = "cancel"

        self.title("Unsaved Changes")
        self.geometry("420x220")
        self.resizable(False, False)
        self.configure(fg_color=colors["bg"])

        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 420) // 2
        y = (self.winfo_screenheight() - 220) // 2
        self.geometry(f"+{x}+{y}")

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

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=90,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=colors["border"],
            text_color=colors["text_secondary"],
            border_width=1,
            border_color=colors["border"],
            command=self._on_cancel,
        )
        cancel_btn.pack(side="left")

        discard_btn = ctk.CTkButton(
            btn_frame,
            text="Discard",
            width=90,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color="#FEE2E2",
            text_color=colors["danger"],
            border_width=1,
            border_color=colors["border"],
            command=self._on_discard,
        )
        discard_btn.pack(side="left", padx=(8, 0))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            width=90,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            command=self._on_save,
        )
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


class RenamePromptDialog(ctk.CTkToplevel):
    """Dialog for renaming a prompt."""

    def __init__(self, master, colors: Dict[str, str], current_name: str, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.result = None

        self.title("Rename Prompt")
        self.geometry("420x200")
        self.resizable(False, False)
        self.configure(fg_color=colors["bg"])

        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 420) // 2
        y = (self.winfo_screenheight() - 200) // 2
        self.geometry(f"+{x}+{y}")

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

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=90,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=colors["border"],
            text_color=colors["text_secondary"],
            border_width=1,
            border_color=colors["border"],
            command=self._on_cancel,
        )
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            width=90,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            command=self._on_save,
        )
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


class FindReplaceDialog(ctk.CTkToplevel):
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
        self.colors = colors
        self.on_find = on_find
        self.on_replace = on_replace
        self.on_replace_all = on_replace_all
        self.show_replace = show_replace

        self.title("Find" + (" & Replace" if show_replace else ""))
        self.geometry("420x220" if show_replace else "420x170")
        self.resizable(False, False)
        self.configure(fg_color=colors["bg"])

        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        width = 420
        height = 220 if show_replace else 170
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

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

        find_btn = ctk.CTkButton(
            btn_frame,
            text="Find Next",
            width=100,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            command=self._on_find,
        )
        find_btn.pack(side="left")

        if show_replace:
            replace_btn = ctk.CTkButton(
                btn_frame,
                text="Replace",
                width=90,
                height=32,
                corner_radius=8,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color=colors["surface"],
                hover_color=colors["border"],
                text_color=colors["text_secondary"],
                border_width=1,
                border_color=colors["border"],
                command=self._on_replace,
            )
            replace_btn.pack(side="left", padx=(8, 0))

            replace_all_btn = ctk.CTkButton(
                btn_frame,
                text="Replace All",
                width=100,
                height=32,
                corner_radius=8,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color=colors["surface"],
                hover_color=colors["border"],
                text_color=colors["text_secondary"],
                border_width=1,
                border_color=colors["border"],
                command=self._on_replace_all,
            )
            replace_all_btn.pack(side="left", padx=(8, 0))

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            width=80,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=colors["border"],
            text_color=colors["text_secondary"],
            border_width=1,
            border_color=colors["border"],
            command=self.destroy,
        )
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


class ConfirmDialog(ctk.CTkToplevel):
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
        self.colors = colors
        self.result = "cancel"

        self.title(title)
        self.geometry("420x210")
        self.resizable(False, False)
        self.configure(fg_color=colors["bg"])

        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 420) // 2
        y = (self.winfo_screenheight() - 210) // 2
        self.geometry(f"+{x}+{y}")

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

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=cancel_text,
            width=90,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=colors["border"],
            text_color=colors["text_secondary"],
            border_width=1,
            border_color=colors["border"],
            command=self._on_cancel,
        )
        cancel_btn.pack(side="left")

        confirm_btn = ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            width=110,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            command=self._on_confirm,
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
