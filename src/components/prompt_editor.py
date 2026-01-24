"""Prompt editor component - Apple 2026 Edition with proper auto-sizing."""
import customtkinter as ctk
from typing import Optional, Callable, Dict
import subprocess
import urllib.parse
import os
import threading
import time

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from ..models import Prompt, Category


class PromptEditor(ctk.CTkFrame):
    """Premium prompt editor with proper auto-sizing layout."""

    def __init__(
        self,
        master,
        on_save: Callable[[Prompt], None],
        on_delete: Callable[[str], None],
        on_copy: Callable[[str], None],
        on_change: Callable[[], None],
        colors: Dict[str, str],
        **kwargs
    ):
        super().__init__(master, fg_color=colors["surface"], corner_radius=0, **kwargs)
        self.on_save = on_save
        self.on_delete = on_delete
        self.on_copy = on_copy
        self.on_change = on_change
        self.colors = colors
        self.current_prompt: Optional[Prompt] = None

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
        
        # Configure card grid - header fixed, content expands, footer fixed
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_rowconfigure(0, weight=0)  # Header - fixed
        self.card.grid_rowconfigure(1, weight=1)  # Content - expands
        self.card.grid_rowconfigure(2, weight=0)  # Footer - fixed

        # ========== HEADER ==========
        header = ctk.CTkFrame(self.card, fg_color="transparent", height=56)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 0))
        header.grid_propagate(False)

        # Left: Title
        self.title_label = ctk.CTkLabel(
            header,
            text="✏️  Edit Prompt",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=colors["text_primary"],
        )
        self.title_label.pack(side="left", pady=12)

        # Right: AI buttons + copy
        right_frame = ctk.CTkFrame(header, fg_color="transparent")
        right_frame.pack(side="right", fill="y")

        # AI Testing buttons
        ai_container = ctk.CTkFrame(right_frame, fg_color="#F5F5F7", corner_radius=8)
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

        # Copy button
        self.copy_btn = ctk.CTkButton(
            right_frame, text="📋", width=36, height=36, corner_radius=8,
            font=ctk.CTkFont(size=16),
            fg_color="transparent", hover_color="#F5F5F7",
            text_color=colors["text_secondary"],
            command=self._on_copy,
        )
        self.copy_btn.pack(side="left", pady=10)

        # ========== CONTENT (Expandable) ==========
        content = ctk.CTkFrame(self.card, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=24, pady=12)
        
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
        self.category_dropdown = ctk.CTkOptionMenu(
            cat_frame, values=[c.value for c in Category],
            variable=self.category_var, height=38,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=colors["surface"],
            text_color=colors["text_primary"],
            button_color=colors["accent"],
            button_hover_color=colors["accent_hover"],
            dropdown_fg_color=colors["surface"],
            dropdown_text_color=colors["text_primary"],
            dropdown_hover_color=colors["accent_glow"],
            corner_radius=10,
            command=lambda _: self._on_field_change(),
        )
        self.category_dropdown.pack(fill="x")

        # Row 1: Tags (spans both columns)
        tags_frame = ctk.CTkFrame(content, fg_color="transparent")
        tags_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        
        ctk.CTkLabel(
            tags_frame, text="TAGS",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=colors["text_muted"],
        ).pack(anchor="w", pady=(0, 4))
        
        self.tags_entry = ctk.CTkEntry(
            tags_frame, height=38,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=colors["surface"], border_color=colors["border"],
            border_width=1, corner_radius=10, text_color=colors["text_primary"],
            placeholder_text="Add tags separated by commas...",
        )
        self.tags_entry.pack(fill="x")
        self.tags_entry.bind("<KeyRelease>", self._on_field_change)

        # Row 2: Content label with char count
        content_header = ctk.CTkFrame(content, fg_color="transparent")
        content_header.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        
        ctk.CTkLabel(
            content_header, text="PROMPT CONTENT",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=colors["text_muted"],
        ).pack(side="left")
        
        self.char_count_label = ctk.CTkLabel(
            content_header, text="0 chars",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=colors["text_muted"],
        )
        self.char_count_label.pack(side="right")

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
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)

        # Top border
        ctk.CTkFrame(footer, height=1, fg_color=colors["border"]).pack(fill="x", side="top")

        footer_inner = ctk.CTkFrame(footer, fg_color="transparent")
        footer_inner.pack(fill="both", expand=True, padx=24)

        # State label
        self.state_label = ctk.CTkLabel(
            footer_inner, text="✓ All changes saved",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["text_muted"],
        )
        self.state_label.pack(side="left", pady=16)

        # Save button
        self.save_btn = ctk.CTkButton(
            footer_inner, text="💾 Save", width=90, height=36, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=colors["accent"], hover_color=colors["accent_hover"],
            command=self._on_save,
        )
        self.save_btn.pack(side="right", pady=12)

        # Delete button
        self.delete_btn = ctk.CTkButton(
            footer_inner, text="Delete", width=70, height=36, corner_radius=8,
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
        self.tags_entry.delete(0, "end")
        self.tags_entry.insert(0, ", ".join(prompt.tags))
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", prompt.content)

        self._update_state_label()
        self._update_char_count()

    def _update_state_label(self):
        if self.current_prompt:
            self.state_label.configure(text="✓ All changes saved", text_color=self.colors["text_muted"])

    def _update_char_count(self):
        content = self.content_text.get("1.0", "end-1c")
        self.char_count_label.configure(text=f"{len(content):,} chars")

    def update_save_state(self, has_changes: bool):
        if has_changes:
            self.state_label.configure(text="● Unsaved changes", text_color=self.colors["accent"])
        else:
            self._update_state_label()

    def clear(self):
        self.current_prompt = None
        self.card.grid_forget()
        self.empty_frame.grid(row=0, column=0, sticky="nsew")

    def _on_field_change(self, event=None):
        if self.current_prompt:
            self.on_change()
            self._update_char_count()

    def _on_save(self):
        if not self.current_prompt:
            return
        self.current_prompt.name = self.name_entry.get().strip()
        self.current_prompt.category = Category(self.category_var.get())
        self.current_prompt.tags = [t.strip() for t in self.tags_entry.get().split(",") if t.strip()]
        self.current_prompt.content = self.content_text.get("1.0", "end-1c")
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
        content = self.content_text.get("1.0", "end-1c")
        if content:
            self.on_copy(content)

    def _test_in_ai(self, service: str):
        content = self.content_text.get("1.0", "end-1c").strip()
        if not content:
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

        def open_and_paste():
            try:
                if browser_exe:
                    subprocess.Popen([browser_exe, url])
                else:
                    import webbrowser
                    webbrowser.open(url)
                time.sleep(3)
                try:
                    import pyautogui
                    pyautogui.hotkey('ctrl', 'v')
                except ImportError:
                    pass
            except Exception:
                pass

        self.clipboard_clear()
        self.clipboard_append(content)
        threading.Thread(target=open_and_paste, daemon=True).start()
