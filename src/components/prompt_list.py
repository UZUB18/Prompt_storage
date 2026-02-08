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
        on_toggle_pin: Callable[[Prompt], None],
        on_toggle_select: Callable[[Prompt, object | None, Optional[bool]], None],
        show_checkbox: bool,
        selected: bool,
        dirty: bool,
        colors: Dict[str, str],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.prompt = prompt
        self.on_select = on_select
        self.on_context = on_context
        self.on_toggle_pin = on_toggle_pin
        self.on_toggle_select = on_toggle_select
        self.multi_select_mode = show_checkbox
        self.colors = colors
        self.selected = selected
        self.dirty = bool(dirty)
        self.active = False

        self.configure(
            fg_color="transparent",
            corner_radius=12,
            cursor="hand2",
        )

        # Container with padding (8/12/16 rhythm)
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

        header_row = ctk.CTkFrame(container, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 8))

        self.select_var = ctk.BooleanVar(value=selected)
        self.select_checkbox = ctk.CTkCheckBox(
            header_row,
            text="",
            width=20,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=6,
            fg_color=colors["accent"],
            border_color=colors["border"],
            hover_color=colors["accent_hover"],
            command=self._on_checkbox,
        )
        if show_checkbox:
            self.select_checkbox.pack(side="left", padx=(0, 8))

        # Name (heading style)
        self.name_label = ctk.CTkLabel(
            header_row,
            text=prompt.name,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=colors["text_primary"],
            anchor="w",
        )
        self.name_label.pack(side="left", fill="x", expand=True)

        self.dirty_dot = ctk.CTkLabel(
            header_row,
            text="●",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=colors["warning"],
            width=12,
        )
        self.dirty_dot.pack(side="right", padx=(0, 6))
        self.set_dirty(self.dirty)

        self.pin_btn = ctk.CTkButton(
            header_row,
            text="★" if prompt.pinned else "☆",
            width=26,
            height=26,
            corner_radius=13,
            fg_color="transparent",
            hover_color=colors["card"],
            text_color=colors["accent"] if prompt.pinned else colors["text_muted"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            border_width=0,
            command=self._on_pin,
        )
        self.pin_btn.pack(side="right")
        self.pin_btn.bind("<Enter>", self._on_enter)
        self.pin_btn.bind("<Leave>", self._on_leave)

        # Metadata + preview line (faint)
        meta_text = self._build_metadata(prompt)
        preview = "" if prompt.sensitive else self._build_snippet(prompt.content)
        line_text = meta_text
        if preview:
            line_text = f"{meta_text} · {preview}" if meta_text else preview
        line_text = self._clamp_text(line_text, max_chars=160)

        self.meta_label = ctk.CTkLabel(
            container,
            text=line_text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=colors["text_muted"],
            anchor="w",
            justify="left",
            wraplength=240,
        )
        self.meta_label.pack(fill="x")

        # Bind events to all child widgets so the entire item is clickable
        widgets = [
            self,
            container,
            header_row,
            self.name_label,
            self.meta_label,
        ]
        for widget in widgets:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Button-3>", self._on_right_click)
            try:
                widget.configure(cursor="hand2")
            except Exception:
                pass

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

        max_first = 60
        max_second = 60

        if len(first) > max_first:
            first = first[: max_first - 1].rstrip() + "…"

        if second:
            second = second if len(second) <= max_second else second[: max_second - 1].rstrip() + "…"
            return f"{first} · {second}"

        return first

    def _build_blurred_snippet(self, content: str) -> str:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return "••••••••••"
        preview = lines[0][:40]
        return "•" * max(10, len(preview))

    def _build_metadata(self, prompt: Prompt) -> str:
        parts = []
        version_number = max(1, int(getattr(prompt, "version_number", 1) or 1))
        parts.append(f"🧬 v{version_number}")
        if prompt.pinned:
            parts.append("📌 Pinned")
        if prompt.sensitive:
            parts.append("🔒 Sensitive")
        category_label = prompt.category.value
        custom_category = (getattr(prompt, "custom_category", "") or "").strip()
        if prompt.category == Category.OTHER and custom_category:
            category_label = f"Other · {custom_category}"
        parts.append(f"📁 {category_label}")
        tags = [t for t in prompt.tags if t]
        if tags:
            tags_text = ", ".join(tags)
            if len(tags_text) > 36:
                tags_text = tags_text[:33] + "..."
            parts.append(f"🏷 {tags_text}")
        parts.append(f"🕒 {self._format_time(prompt.updated_at)}")
        return " · ".join(parts)

    def _clamp_text(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 1].rstrip() + "…"

    def _on_enter(self, event=None):
        if not self.selected and not self.multi_select_mode:
            self.configure(fg_color=self.colors["card"])

    def _on_leave(self, event=None):
        if not self.selected and not self.multi_select_mode:
            self.configure(fg_color="transparent")

    def _on_click(self, event=None):
        if event is not None and (
            self._is_descendant_of(event.widget, self.select_checkbox)
            or self._is_descendant_of(event.widget, self.pin_btn)
        ):
            return
        if self.multi_select_mode:
            self.on_toggle_select(self.prompt, event)
            return
        self.on_select(self.prompt)

    def _on_right_click(self, event=None):
        self.on_context(self.prompt, event)

    def _on_pin(self):
        self.on_toggle_pin(self.prompt)

    def _on_checkbox(self):
        self.on_toggle_select(self.prompt, None, self.select_var.get())
        self.set_selected(self.select_var.get())

    def set_multiselect(self, enabled: bool, selected: bool):
        self.multi_select_mode = enabled
        if enabled:
            self.select_var.set(selected)
            self.select_checkbox.pack(side="left", padx=(0, 8))
            self.pin_btn.pack_forget()
            if not selected:
                self.configure(fg_color="transparent", border_width=0)
        else:
            self.select_checkbox.pack_forget()
            self.pin_btn.pack(side="right")

    def set_selected(self, selected: bool):
        self.selected = selected
        self.select_var.set(selected)
        if selected:
            self.configure(
                fg_color=self.colors["accent_glow"],
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
            if self.active:
                self.set_active(True)

    def set_dirty(self, dirty: bool):
        self.dirty = bool(dirty)
        if self.dirty:
            self.dirty_dot.pack(side="right", padx=(0, 6))
        else:
            self.dirty_dot.pack_forget()

    def set_active(self, active: bool):
        self.active = bool(active)
        # Keep keyboard-active cursor internal only; avoid extra row coloring that can
        # look like selection. In multi-select, selected rows are the only colored rows.
        if not self.selected and not self.multi_select_mode:
            if self.active:
                self.configure(
                    fg_color=self.colors["card"],
                    border_width=1,
                    border_color=self.colors["border"],
                )
            else:
                self.configure(
                    fg_color="transparent",
                    border_width=0,
                )

    def _is_descendant_of(self, widget, ancestor) -> bool:
        current = widget
        while current is not None:
            if current == ancestor:
                return True
            current = getattr(current, "master", None)
        return False


class PromptList(ctk.CTkScrollableFrame):
    """Scrollable prompt list with Apple-style items."""

    def __init__(
        self,
        master,
        on_select: Callable[[Prompt], None],
        on_copy: Callable[[Prompt], None],
        on_rename: Callable[[Prompt], None],
        on_new_version: Callable[[Prompt], None],
        on_toggle_pin: Callable[[Prompt], None],
        on_selection_change: Callable[[List[Prompt]], None],
        on_clear_search: Callable[[], None],
        on_new_prompt: Callable[[], None],
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
        self.on_new_version = on_new_version
        self.on_toggle_pin = on_toggle_pin
        self.on_selection_change = on_selection_change
        self.on_clear_search = on_clear_search
        self.on_new_prompt = on_new_prompt
        self.colors = colors
        self.items: List[PromptListItem] = []
        self.prompts: List[Prompt] = []
        self.filtered_prompts: List[Prompt] = []
        self.selected_prompt: Optional[Prompt] = None
        self.search_term = ""
        self.category_filter: Optional[Category] = None
        self.pinned_only = False
        self.multi_select_mode = False
        self.selected_ids: set[str] = set()
        self._last_selected_index: Optional[int] = None
        self.sort_option = "Recently updated"
        self.context_prompt: Optional[Prompt] = None
        self.dirty_ids: set[str] = set()
        self._active_prompt_id: Optional[str] = None

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Pin", command=self._on_context_toggle_pin)
        self._pin_menu_index = 0
        self.context_menu.add_command(label="Copy", command=self._on_context_copy)
        self.context_menu.add_command(label="Rename", command=self._on_context_rename)
        self.context_menu.add_command(label="Create new version", command=self._on_context_new_version)

        self.empty_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.empty_label = ctk.CTkLabel(
            self.empty_frame,
            text="No prompts match your search or filter.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["text_muted"],
        )
        self.empty_label.pack(pady=(0, 12))

        empty_btns = ctk.CTkFrame(self.empty_frame, fg_color="transparent")
        empty_btns.pack()

        self.empty_clear_btn = ctk.CTkButton(
            empty_btns,
            text="Clear search",
            height=32,
            **self._btn_secondary_style(size=12, radius=8),
            command=self.on_clear_search,
        )
        self.empty_clear_btn.pack(side="left", padx=(0, 8))

        self.empty_new_btn = ctk.CTkButton(
            empty_btns,
            text="New prompt",
            height=32,
            **self._btn_primary_style(size=12, radius=8),
            command=self.on_new_prompt,
        )
        self.empty_new_btn.pack(side="left")

    def _btn_secondary_style(
        self,
        *,
        size: int = 11,
        weight: str = "normal",
        radius: int = 8,
    ) -> dict:
        return {
            "corner_radius": radius,
            "font": ctk.CTkFont(family="Segoe UI", size=size, weight=weight),
            "fg_color": self.colors["surface"],
            "hover_color": self.colors["border"],
            "text_color": self.colors["text_secondary"],
            "border_width": 1,
            "border_color": self.colors["border"],
        }

    def _btn_primary_style(self, *, size: int = 11, weight: str = "bold", radius: int = 8) -> dict:
        return {
            "corner_radius": radius,
            "font": ctk.CTkFont(family="Segoe UI", size=size, weight=weight),
            "fg_color": self.colors["accent"],
            "hover_color": self.colors["accent_hover"],
        }

    def set_prompts(self, prompts: List[Prompt]):
        """Set prompts and rebuild list."""
        self.prompts = prompts
        if self.selected_ids:
            available = {p.id for p in prompts}
            self.selected_ids = {pid for pid in self.selected_ids if pid in available}
            self.on_selection_change(self.get_selected_prompts())
        self._apply_filters()

    def set_search(self, term: str):
        """Set search term."""
        self.search_term = term.lower()
        self._apply_filters()

    def set_category_filter(self, category: Optional[Category]):
        """Set category filter."""
        self.category_filter = category
        self._apply_filters()

    def set_pinned_only(self, value: bool):
        """Set pinned-only filter."""
        self.pinned_only = bool(value)
        self._apply_filters()

    def set_sort(self, option: str):
        """Set sorting option."""
        self.sort_option = option
        self._apply_filters()

    def set_dirty_ids(self, dirty_ids: set[str]):
        """Set ids that should show unsaved/dirty indicator."""
        self.dirty_ids = set(dirty_ids)
        self._sync_dirty_ui()

    def set_multi_select_mode(self, enabled: bool):
        self.multi_select_mode = bool(enabled)
        if not self.multi_select_mode:
            self.selected_ids.clear()
            self.on_selection_change(self.get_selected_prompts())
            self._last_selected_index = None
        else:
            # Carry current single-selection into multi-select so visual selection
            # and checkbox state always match.
            if self.selected_prompt and any(p.id == self.selected_prompt.id for p in self.prompts):
                self.selected_ids.add(self.selected_prompt.id)
            if self.filtered_prompts:
                if self._active_prompt_id is None:
                    # Prime keyboard navigation cursor in multi-select mode.
                    self._active_prompt_id = self.filtered_prompts[0].id
                if self.selected_ids:
                    idx = next(
                        (i for i, p in enumerate(self.filtered_prompts) if p.id in self.selected_ids),
                        None,
                    )
                    if idx is not None:
                        self._last_selected_index = idx
            self.on_selection_change(self.get_selected_prompts())
        self._rebuild_list()

    def keyboard_move_selection(self, step: int, extend: bool = False) -> bool:
        if not self.filtered_prompts:
            return False

        current_index = self._active_index()
        if current_index is None:
            current_index = 0

        next_index = max(0, min(len(self.filtered_prompts) - 1, current_index + step))
        target = self.filtered_prompts[next_index]
        self._active_prompt_id = target.id

        if self.multi_select_mode:
            if extend:
                anchor = self._last_selected_index
                if anchor is None:
                    anchor = current_index
                start = min(anchor, next_index)
                end = max(anchor, next_index)
                self.selected_ids = {p.id for p in self.filtered_prompts[start : end + 1]}
                self._last_selected_index = anchor
            else:
                self.selected_ids = {target.id}
                self._last_selected_index = next_index
            self.on_selection_change(self.get_selected_prompts())
            self._sync_selection_ui()
        else:
            self._on_item_select(target)

        self._sync_active_ui()
        return True

    def keyboard_toggle_active(self) -> bool:
        if not self.multi_select_mode or not self.filtered_prompts:
            return False
        index = self._active_index()
        if index is None:
            index = 0
        prompt = self.filtered_prompts[index]
        self._active_prompt_id = prompt.id
        if prompt.id in self.selected_ids:
            self.selected_ids.remove(prompt.id)
        else:
            self.selected_ids.add(prompt.id)
        self._last_selected_index = index
        self.on_selection_change(self.get_selected_prompts())
        self._sync_selection_ui()
        self._sync_active_ui()
        return True

    def _active_index(self) -> Optional[int]:
        if self._active_prompt_id:
            for idx, prompt in enumerate(self.filtered_prompts):
                if prompt.id == self._active_prompt_id:
                    return idx
        if self.selected_ids:
            for idx, prompt in enumerate(self.filtered_prompts):
                if prompt.id in self.selected_ids:
                    return idx
        if self.selected_prompt:
            for idx, prompt in enumerate(self.filtered_prompts):
                if prompt.id == self.selected_prompt.id:
                    return idx
        return None

    def toggle_selected(self, prompt: Prompt):
        if prompt.id in self.selected_ids:
            self.selected_ids.remove(prompt.id)
        else:
            self.selected_ids.add(prompt.id)
        self._active_prompt_id = prompt.id
        self.on_selection_change(self.get_selected_prompts())
        self._sync_selection_ui()

    def clear_selection(self):
        if not self.selected_ids:
            return
        self.selected_ids.clear()
        self.on_selection_change(self.get_selected_prompts())
        self._last_selected_index = None
        self._sync_selection_ui()

    def select_all(self):
        # Select currently visible prompts (respects active search/filter/sort).
        visible = self.filtered_prompts if self.filtered_prompts else self.prompts
        self.selected_ids = {p.id for p in visible}
        if self.filtered_prompts:
            self._active_prompt_id = self.filtered_prompts[0].id
            self._last_selected_index = 0
        self.on_selection_change(self.get_selected_prompts())
        self._sync_selection_ui()

    def get_selected_prompts(self) -> List[Prompt]:
        if not self.selected_ids:
            return []
        lookup = {p.id: p for p in self.prompts}
        return [lookup[p_id] for p_id in self.selected_ids if p_id in lookup]

    def _apply_filters(self):
        """Apply search and category filters."""
        filtered = self.prompts

        if self.search_term:
            filtered = [
                p for p in filtered
                if self.search_term in p.name.lower()
                or self.search_term in p.content.lower()
                or self.search_term in (getattr(p, "custom_category", "") or "").lower()
                or any(self.search_term in t.lower() for t in p.tags)
            ]

        if self.category_filter:
            filtered = [p for p in filtered if p.category == self.category_filter]

        if self.pinned_only:
            filtered = [p for p in filtered if getattr(p, "pinned", False)]

        filtered = self._apply_sort(filtered)
        self.filtered_prompts = filtered
        self._rebuild_list()

    def _apply_sort(self, prompts: List[Prompt]) -> List[Prompt]:
        """Sort prompts based on selected option."""
        if not prompts:
            return prompts

        if self.sort_option == "Name A->Z":
            sorted_prompts = sorted(prompts, key=lambda p: p.name.lower())
            return self._pin_sort(sorted_prompts)

        def parse_time(value: str) -> datetime:
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return datetime.min

        if self.sort_option == "Created":
            sorted_prompts = sorted(prompts, key=lambda p: parse_time(p.created_at), reverse=True)
            return self._pin_sort(sorted_prompts)

        # Default: Recently updated
        sorted_prompts = sorted(prompts, key=lambda p: parse_time(p.updated_at), reverse=True)
        return self._pin_sort(sorted_prompts)

    def _pin_sort(self, prompts: List[Prompt]) -> List[Prompt]:
        if self.pinned_only:
            return prompts
        pinned = [p for p in prompts if getattr(p, "pinned", False)]
        others = [p for p in prompts if not getattr(p, "pinned", False)]
        return pinned + others

    def _rebuild_list(self):
        """Rebuild the list UI."""
        # Clear existing items
        for item in self.items:
            item.destroy()
        self.items.clear()
        self.empty_frame.pack_forget()

        # Create new items
        if not self.filtered_prompts:
            self.empty_frame.pack(pady=24)
            self._active_prompt_id = None
            return

        visible_ids = {p.id for p in self.filtered_prompts}
        if self._active_prompt_id not in visible_ids:
            self._active_prompt_id = None

        for prompt in self.filtered_prompts:
            item = PromptListItem(
                self,
                prompt=prompt,
                on_select=self._on_item_select,
                on_context=self._show_context_menu,
                on_toggle_pin=self._on_item_toggle_pin,
                on_toggle_select=self._on_item_toggle_select,
                show_checkbox=self.multi_select_mode,
                selected=prompt.id in self.selected_ids,
                dirty=prompt.id in self.dirty_ids,
                colors=self.colors,
            )
            item.pack(fill="x", pady=2)
            self.items.append(item)
            item.set_multiselect(self.multi_select_mode, prompt.id in self.selected_ids)

            if self.multi_select_mode:
                item.set_selected(prompt.id in self.selected_ids)
            elif self.selected_prompt and prompt.id == self.selected_prompt.id:
                item.set_selected(True)

        if self._active_prompt_id is None:
            if self.multi_select_mode:
                if self.selected_ids:
                    self._active_prompt_id = next(
                        (p.id for p in self.filtered_prompts if p.id in self.selected_ids),
                        self.filtered_prompts[0].id,
                    )
                else:
                    self._active_prompt_id = self.filtered_prompts[0].id
            elif self.selected_prompt and self.selected_prompt.id in visible_ids:
                self._active_prompt_id = self.selected_prompt.id

        self._sync_active_ui()

    def _on_item_select(self, prompt: Prompt):
        """Handle item selection."""
        if self.multi_select_mode:
            self._on_item_toggle_select(prompt, None)
            return
        self.selected_prompt = prompt
        self._active_prompt_id = prompt.id

        for item in self.items:
            item.set_selected(item.prompt.id == prompt.id)

        self.on_select(prompt)

    def _show_context_menu(self, prompt: Prompt, event):
        """Show context menu for a prompt."""
        self.context_prompt = prompt
        label = "Unpin" if prompt.pinned else "Pin"
        try:
            self.context_menu.entryconfigure(self._pin_menu_index, label=label)
        except Exception:
            pass
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

    def _on_context_toggle_pin(self):
        if self.context_prompt:
            self.on_toggle_pin(self.context_prompt)

    def _on_context_new_version(self):
        if self.context_prompt:
            self.on_new_version(self.context_prompt)

    def _on_item_toggle_pin(self, prompt: Prompt):
        self.on_toggle_pin(prompt)

    def _on_item_toggle_select(
        self,
        prompt: Prompt,
        event: object | None,
        desired_state: Optional[bool] = None,
    ):
        if not self.multi_select_mode:
            return
        shift = False
        if event is not None:
            try:
                shift = bool(event.state & 0x0001)
            except Exception:
                shift = False

        try:
            current_index = next(
                idx for idx, p in enumerate(self.filtered_prompts) if p.id == prompt.id
            )
        except StopIteration:
            current_index = None

        if shift and self._last_selected_index is not None and current_index is not None:
            start = min(self._last_selected_index, current_index)
            end = max(self._last_selected_index, current_index)
            for p in self.filtered_prompts[start : end + 1]:
                self.selected_ids.add(p.id)
            self._last_selected_index = current_index
        else:
            if desired_state is True:
                self.selected_ids.add(prompt.id)
            elif desired_state is False:
                self.selected_ids.discard(prompt.id)
            else:
                if prompt.id in self.selected_ids:
                    self.selected_ids.remove(prompt.id)
                else:
                    self.selected_ids.add(prompt.id)
            if current_index is not None:
                self._last_selected_index = current_index

        self.on_selection_change(self.get_selected_prompts())
        self._sync_selection_ui()
        if current_index is not None:
            self._active_prompt_id = self.filtered_prompts[current_index].id
        self._sync_active_ui()

    def set_selected_prompt(self, prompt: Optional[Prompt]):
        """Force selection state in the list."""
        self.selected_prompt = prompt
        self._active_prompt_id = prompt.id if prompt else self._active_prompt_id
        for item in self.items:
            item.set_selected(prompt is not None and item.prompt.id == prompt.id)
        self._sync_active_ui()

    def _sync_selection_ui(self):
        for item in self.items:
            item.set_selected(item.prompt.id in self.selected_ids)
        self._sync_active_ui()

    def _sync_dirty_ui(self):
        for item in self.items:
            item.set_dirty(item.prompt.id in self.dirty_ids)

    def _sync_active_ui(self):
        for item in self.items:
            item.set_active(bool(self._active_prompt_id and item.prompt.id == self._active_prompt_id))

