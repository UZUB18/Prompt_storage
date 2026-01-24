"""Prompt list component - Apple 2026 Edition."""
import customtkinter as ctk
import tkinter as tk
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
        on_context: Callable[[Prompt, object], None],
        colors: Dict[str, str],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.prompt = prompt
        self.on_select = on_select
        self.on_context = on_context
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

        # Snippet (preview)
        snippet = self._build_snippet(prompt.content)
        self.snippet_label = ctk.CTkLabel(
            container,
            text=snippet,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=colors["text_secondary"],
            anchor="w",
            justify="left",
            wraplength=220,
        )
        self.snippet_label.pack(fill="x", pady=(4, 0))

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
        self.bind("<Button-3>", self._on_right_click)
        container.bind("<Button-3>", self._on_right_click)
        self.name_label.bind("<Button-3>", self._on_right_click)
        meta_frame.bind("<Button-3>", self._on_right_click)
        self.category_badge.bind("<Button-3>", self._on_right_click)
        self.time_label.bind("<Button-3>", self._on_right_click)

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

    def _build_snippet(self, content: str) -> str:
        """Build a short preview snippet from content."""
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return ""

        first = lines[0]
        second = lines[1] if len(lines) > 1 else ""

        max_first = 110
        max_second = 90

        if len(first) > max_first:
            return first[:max_first - 3] + "..."

        if second:
            second = second if len(second) <= max_second else second[:max_second - 3] + "..."
            return f"{first} - {second}"

        return first

    def _on_enter(self, event=None):
        if not self.selected:
            self.configure(fg_color=self.colors["surface"])

    def _on_leave(self, event=None):
        if not self.selected:
            self.configure(fg_color="transparent")

    def _on_click(self, event=None):
        self.on_select(self.prompt)

    def _on_right_click(self, event=None):
        self.on_context(self.prompt, event)

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
        on_copy: Callable[[Prompt], None],
        on_rename: Callable[[Prompt], None],
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
        self.on_copy = on_copy
        self.on_rename = on_rename
        self.colors = colors
        self.items: List[PromptListItem] = []
        self.prompts: List[Prompt] = []
        self.filtered_prompts: List[Prompt] = []
        self.selected_prompt: Optional[Prompt] = None
        self.search_term = ""
        self.category_filter: Optional[Category] = None
        self.sort_option = "Recently updated"
        self.context_prompt: Optional[Prompt] = None

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self._on_context_copy)
        self.context_menu.add_command(label="Rename", command=self._on_context_rename)

        self.empty_label = ctk.CTkLabel(
            self,
            text="No prompts match your search or filter.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["text_muted"],
        )

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

    def set_sort(self, option: str):
        """Set sorting option."""
        self.sort_option = option
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

        filtered = self._apply_sort(filtered)
        self.filtered_prompts = filtered
        self._rebuild_list()

    def _apply_sort(self, prompts: List[Prompt]) -> List[Prompt]:
        """Sort prompts based on selected option."""
        if not prompts:
            return prompts

        if self.sort_option == "Name A->Z":
            return sorted(prompts, key=lambda p: p.name.lower())

        def parse_time(value: str) -> datetime:
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return datetime.min

        if self.sort_option == "Created":
            return sorted(prompts, key=lambda p: parse_time(p.created_at), reverse=True)

        # Default: Recently updated
        return sorted(prompts, key=lambda p: parse_time(p.updated_at), reverse=True)

    def _rebuild_list(self):
        """Rebuild the list UI."""
        # Clear existing items
        for item in self.items:
            item.destroy()
        self.items.clear()
        self.empty_label.pack_forget()

        # Create new items
        if not self.filtered_prompts:
            self.empty_label.pack(pady=30)
            return

        for prompt in self.filtered_prompts:
            item = PromptListItem(
                self,
                prompt=prompt,
                on_select=self._on_item_select,
                on_context=self._show_context_menu,
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

    def _show_context_menu(self, prompt: Prompt, event):
        """Show context menu for a prompt."""
        self.context_prompt = prompt
        if event is not None:
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def _on_context_copy(self):
        if self.context_prompt:
            self.on_copy(self.context_prompt)

    def _on_context_rename(self):
        if self.context_prompt:
            self.on_rename(self.context_prompt)

    def set_selected_prompt(self, prompt: Optional[Prompt]):
        """Force selection state in the list."""
        self.selected_prompt = prompt
        for item in self.items:
            item.set_selected(prompt is not None and item.prompt.id == prompt.id)
