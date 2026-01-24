"""Prompt list component - Apple 2026 Edition."""
import customtkinter as ctk
from typing import List, Optional, Callable, Dict
from datetime import datetime

from ..models import Prompt, Category


class PromptListItem(ctk.CTkFrame):
    """Individual prompt list item with Apple-style design."""

    def __init__(
        self,
        master,
        prompt: Prompt,
        on_select: Callable[[Prompt], None],
        colors: Dict[str, str],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.prompt = prompt
        self.on_select = on_select
        self.colors = colors
        self.selected = False

        self.configure(
            fg_color="transparent",
            corner_radius=12,
            cursor="hand2",
        )

        # Container with padding
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=12)

        # Accent bar (left-side indicator)
        self.accent_bar = ctk.CTkFrame(
            self,
            width=3,
            fg_color="transparent",
            corner_radius=2,
        )
        self.accent_bar.place(x=0, rely=0.2, relheight=0.6)

        # Name (heading style)
        self.name_label = ctk.CTkLabel(
            container,
            text=prompt.name,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=colors["text_primary"],
            anchor="w",
        )
        self.name_label.pack(fill="x")

        # Meta row: Category badge + timestamp
        meta_frame = ctk.CTkFrame(container, fg_color="transparent")
        meta_frame.pack(fill="x", pady=(6, 0))

        # Category badge (pill style)
        self.category_badge = ctk.CTkLabel(
            meta_frame,
            text=prompt.category.value,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=colors["accent"],
            fg_color=colors["category_bg"],
            corner_radius=6,
            padx=8,
            pady=2,
        )
        self.category_badge.pack(side="left")

        # Timestamp
        time_text = self._format_time(prompt.updated_at)
        self.time_label = ctk.CTkLabel(
            meta_frame,
            text=time_text,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=colors["text_muted"],
        )
        self.time_label.pack(side="left", padx=(8, 0))

        # Bind events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        container.bind("<Button-1>", self._on_click)
        self.name_label.bind("<Button-1>", self._on_click)
        meta_frame.bind("<Button-1>", self._on_click)
        self.category_badge.bind("<Button-1>", self._on_click)
        self.time_label.bind("<Button-1>", self._on_click)

    def _format_time(self, iso_time: str) -> str:
        """Format timestamp to relative time."""
        try:
            dt = datetime.fromisoformat(iso_time)
            now = datetime.now()
            delta = now - dt
            
            if delta.days > 0:
                return f"{delta.days}d ago"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600}h ago"
            elif delta.seconds > 60:
                return f"{delta.seconds // 60}m ago"
            else:
                return "Just now"
        except:
            return ""

    def _on_enter(self, event=None):
        if not self.selected:
            self.configure(fg_color=self.colors["surface"])

    def _on_leave(self, event=None):
        if not self.selected:
            self.configure(fg_color="transparent")

    def _on_click(self, event=None):
        self.on_select(self.prompt)

    def set_selected(self, selected: bool):
        self.selected = selected
        if selected:
            self.configure(
                fg_color=self.colors["surface"],
                border_width=1,
                border_color=self.colors["accent"],
            )
            self.accent_bar.configure(fg_color=self.colors["accent"])
        else:
            self.configure(
                fg_color="transparent",
                border_width=0,
            )
            self.accent_bar.configure(fg_color="transparent")


class PromptList(ctk.CTkScrollableFrame):
    """Scrollable prompt list with Apple-style items."""

    def __init__(
        self,
        master,
        on_select: Callable[[Prompt], None],
        colors: Dict[str, str],
        **kwargs
    ):
        super().__init__(
            master,
            fg_color="transparent",
            scrollbar_button_color=colors["border"],
            scrollbar_button_hover_color=colors["text_muted"],
            **kwargs
        )
        self.on_select = on_select
        self.colors = colors
        self.items: List[PromptListItem] = []
        self.prompts: List[Prompt] = []
        self.filtered_prompts: List[Prompt] = []
        self.selected_prompt: Optional[Prompt] = None
        self.search_term = ""
        self.category_filter: Optional[Category] = None

    def set_prompts(self, prompts: List[Prompt]):
        """Set prompts and rebuild list."""
        self.prompts = prompts
        self._apply_filters()

    def set_search(self, term: str):
        """Set search term."""
        self.search_term = term.lower()
        self._apply_filters()

    def set_category_filter(self, category: Optional[Category]):
        """Set category filter."""
        self.category_filter = category
        self._apply_filters()

    def _apply_filters(self):
        """Apply search and category filters."""
        filtered = self.prompts

        if self.search_term:
            filtered = [
                p for p in filtered
                if self.search_term in p.name.lower()
                or self.search_term in p.content.lower()
                or any(self.search_term in t.lower() for t in p.tags)
            ]

        if self.category_filter:
            filtered = [p for p in filtered if p.category == self.category_filter]

        self.filtered_prompts = filtered
        self._rebuild_list()

    def _rebuild_list(self):
        """Rebuild the list UI."""
        # Clear existing items
        for item in self.items:
            item.destroy()
        self.items.clear()

        # Create new items
        for prompt in self.filtered_prompts:
            item = PromptListItem(
                self,
                prompt=prompt,
                on_select=self._on_item_select,
                colors=self.colors,
            )
            item.pack(fill="x", pady=2)
            self.items.append(item)

            if self.selected_prompt and prompt.id == self.selected_prompt.id:
                item.set_selected(True)

    def _on_item_select(self, prompt: Prompt):
        """Handle item selection."""
        self.selected_prompt = prompt

        for item in self.items:
            item.set_selected(item.prompt.id == prompt.id)

        self.on_select(prompt)
