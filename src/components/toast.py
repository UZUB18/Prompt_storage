"""Toast notification component - Minimalist Apple 2026 Edition."""
import customtkinter as ctk
from typing import Dict


class Toast(ctk.CTkToplevel):
    """Minimalist pill-shaped toast that floats at the bottom center."""

    def __init__(
        self,
        master,
        message: str,
        colors: Dict[str, str],
        duration: int = 2500,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.colors = colors

        # Remove window decorations
        self.overrideredirect(True)
        self.configure(fg_color=colors["surface"])
        self.attributes("-topmost", True)
        
        # Transparent background for the window itself (if OS allows)
        # Note: In Windows, we can't easily do transparent window background with CTk
        # without complex hacking, so we maintain matching fg_color.
        
        # Pill container
        pill_bg = colors.get("toast_bg", colors["text_primary"])
        pill_text = colors.get("toast_text", "#FFFFFF")
        self.pill = ctk.CTkFrame(
            self,
            fg_color=pill_bg,
            corner_radius=20,
            border_width=0,
        )
        self.pill.pack(fill="both", expand=True)

        # Content
        self.label = ctk.CTkLabel(
            self.pill,
            text=message,
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=12, weight="bold"),
            text_color=pill_text,
        )
        self.label.pack(side="left", padx=20, pady=8)

        # Position at bottom-center of parent
        self.update_idletasks()
        
        # Get parent geometry
        parent_x = master.winfo_rootx()
        parent_y = master.winfo_rooty()
        parent_w = master.winfo_width()
        parent_h = master.winfo_height()
        
        # Calculate size
        toast_w = self.winfo_reqwidth()
        toast_h = self.winfo_reqheight()

        # Center horizontally, 40px from bottom
        x = parent_x + (parent_w // 2) - (toast_w // 2)
        y = parent_y + parent_h - toast_h - 60

        self.geometry(f"{toast_w}x{toast_h}+{x}+{y}")

        # Animation states
        self.attributes("-alpha", 0.0)
        self._fade_in(0.0)

        # Auto dismiss
        self.after(duration, lambda: self._fade_out(1.0))

    def _fade_in(self, alpha: float):
        """Smooth fade in."""
        if alpha < 1.0:
            alpha += 0.08
            if alpha > 1.0: alpha = 1.0
            self.attributes("-alpha", alpha)
            self.after(16, lambda: self._fade_in(alpha))

    def _fade_out(self, alpha: float):
        """Smooth fade out."""
        if alpha > 0:
            alpha -= 0.08
            if alpha < 0: alpha = 0
            self.attributes("-alpha", alpha)
            self.after(16, lambda: self._fade_out(alpha))
        else:
            self.destroy()
