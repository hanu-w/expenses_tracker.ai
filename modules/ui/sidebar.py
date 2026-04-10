"""
Expense Tracker — Sidebar Navigation
Left sidebar with navigation buttons and app branding.
"""

import customtkinter as ctk
from modules.theme import FONTS


class Sidebar(ctk.CTkFrame):
    """Navigation sidebar with branding and menu items."""

    NAV_ITEMS = [
        {"name": "Dashboard",   "icon": "📊", "view": "dashboard"},
        {"name": "Add Expense", "icon": "➕", "view": "add_expense"},
        {"name": "Expenses",    "icon": "📋", "view": "expense_list"},
        {"name": "Charts",      "icon": "📈", "view": "charts"},
        {"name": "Settings",    "icon": "⚙️", "view": "settings"},
    ]

    def __init__(self, master, theme, on_navigate, **kwargs):
        self.theme = theme
        self.on_navigate = on_navigate
        self.active_view = "dashboard"
        self.nav_buttons = {}

        super().__init__(
            master,
            fg_color=self.theme["sidebar"],
            corner_radius=0,
            **kwargs,
        )

        self._build_ui()

    def _build_ui(self):
        """Build the sidebar layout."""

        # ─── Logo / Branding ──────────────────────────────────
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(28, 8))

        logo_label = ctk.CTkLabel(
            brand_frame, text="💰",
            font=("Segoe UI", 36),
        )
        logo_label.pack(anchor="w")

        title_label = ctk.CTkLabel(
            brand_frame, text="ExpenseAI",
            font=("Segoe UI", 22, "bold"),
            text_color="#a29bfe",
        )
        title_label.pack(anchor="w", pady=(4, 0))

        tagline = ctk.CTkLabel(
            brand_frame, text="Smart Expense Tracker",
            font=FONTS["tiny"],
            text_color=self.theme.get("text_muted", "#5a5a6a"),
        )
        tagline.pack(anchor="w", pady=(0, 0))

        # ─── Divider ─────────────────────────────────────────
        divider = ctk.CTkFrame(self, fg_color=self.theme.get("border", "#2a2a3e"), height=1)
        divider.pack(fill="x", padx=16, pady=(16, 16))

        # ─── Menu Label ──────────────────────────────────────
        menu_label = ctk.CTkLabel(
            self, text="MENU", font=FONTS["tiny"],
            text_color=self.theme.get("text_muted", "#5a5a6a"),
            anchor="w"
        )
        menu_label.pack(fill="x", padx=20, pady=(0, 8))

        # ─── Navigation Buttons ──────────────────────────────
        for item in self.NAV_ITEMS:
            btn = self._create_nav_button(item)
            self.nav_buttons[item["view"]] = btn

        # Set initial active state
        self._set_active("dashboard")

        # ─── Spacer ──────────────────────────────────────────
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # ─── Footer ──────────────────────────────────────────
        footer_divider = ctk.CTkFrame(self, fg_color=self.theme.get("border", "#2a2a3e"), height=1)
        footer_divider.pack(fill="x", padx=16, pady=(0, 8))

        version_label = ctk.CTkLabel(
            self, text="v1.0.0",
            font=FONTS["tiny"],
            text_color=self.theme.get("text_muted", "#5a5a6a"),
        )
        version_label.pack(pady=(0, 16))

    def _create_nav_button(self, item):
        """Create a single navigation button."""
        btn = ctk.CTkButton(
            self,
            text=f"  {item['icon']}  {item['name']}",
            font=FONTS["nav"],
            fg_color="transparent",
            text_color=self.theme.get("text_secondary", "#8a8a9a"),
            hover_color=self.theme.get("sidebar_active", "#1a1a2e"),
            anchor="w",
            height=42,
            corner_radius=10,
            command=lambda v=item["view"]: self._on_click(v),
        )
        btn.pack(fill="x", padx=12, pady=2)
        return btn

    def _on_click(self, view_name):
        """Handle nav button click."""
        self._set_active(view_name)
        self.on_navigate(view_name)

    def _set_active(self, view_name):
        """Highlight the active button."""
        self.active_view = view_name
        for name, btn in self.nav_buttons.items():
            if name == view_name:
                btn.configure(
                    fg_color=self.theme.get("accent", "#6c5ce7"),
                    text_color="#ffffff",
                    font=FONTS["nav_active"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.theme.get("text_secondary", "#8a8a9a"),
                    font=FONTS["nav"],
                )

    def update_theme(self, theme):
        """Update sidebar colors when theme changes."""
        self.theme = theme
        self.configure(fg_color=theme["sidebar"])
        # Re-apply active state with new colors
        self._set_active(self.active_view)
