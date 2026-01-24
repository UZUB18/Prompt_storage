"""Toast notification component."""
import customtkinter as ctk
from typing import Dict


class Toast(ctk.CTkToplevel):
    """Subtle toast notification that auto-dismisses."""

    def __init__(
        self,
        master,
        message: str,
        colors: Dict[str, str],
        duration: int = 2000,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.colors = colors

        # Remove window decorations
        self.overrideredirect(True)
        self.configure(fg_color=colors["card"])
        self.attributes("-topmost", True)

        # Toast content
        frame = ctk.CTkFrame(
            self,
            fg_color=colors["card"],
            corner_radius=10,
        )
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Success indicator
        indicator = ctk.CTkFrame(
            frame,
            width=4,
            fg_color=colors["success"],
            corner_radius=2,
        )
        indicator.pack(side="left", fill="y", padx=(12, 8), pady=12)

        label = ctk.CTkLabel(
            frame,
            text=message,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=colors["text_primary"],
        )
        label.pack(side="left", padx=(0, 16), pady=12)

        # Position at bottom-right of parent
        self.update_idletasks()
        parent_x = master.winfo_rootx()
        parent_y = master.winfo_rooty()
        parent_w = master.winfo_width()
        parent_h = master.winfo_height()
        
        toast_w = self.winfo_reqwidth()
        toast_h = self.winfo_reqheight()

        x = parent_x + parent_w - toast_w - 24
        y = parent_y + parent_h - toast_h - 24

        self.geometry(f"+{x}+{y}")

        # Fade in effect (simple)
        self.attributes("-alpha", 0.0)
        self._fade_in(0.0)

        # Auto dismiss
        self.after(duration, self._fade_out)

    def _fade_in(self, alpha: float):
        """Fade in animation."""
        if alpha < 1.0:
            alpha += 0.1
            self.attributes("-alpha", alpha)
            self.after(20, lambda: self._fade_in(alpha))

    def _fade_out(self, alpha: float = 1.0):
        """Fade out animation."""
        if alpha > 0:
            alpha -= 0.1
            self.attributes("-alpha", alpha)
            self.after(20, lambda: self._fade_out(alpha))
        else:
            self.destroy()
