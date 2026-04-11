"""
Expense Tracker — Sidebar Navigation
Left sidebar with navigation buttons, app branding, and theme toggle.
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

    def __init__(self, master, theme, on_navigate,
                 on_theme_toggle=None, app_mode="dark", **kwargs):
        self.theme = theme
        self.on_navigate = on_navigate
        self.on_theme_toggle = on_theme_toggle
        self.app_mode = app_mode
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
        brand_frame.pack(fill="x", padx=18, pady=(28, 10))

        logo_label = ctk.CTkLabel(
            brand_frame, text="💰",
            font=("Segoe UI", 38),
        )
        logo_label.pack(anchor="w")

        title_label = ctk.CTkLabel(
            brand_frame, text="ExpenseAI",
            font=("Segoe UI", 22, "bold"),
            text_color="#a29bfe",
        )
        title_label.pack(anchor="w", pady=(6, 0))

        tagline = ctk.CTkLabel(
            brand_frame, text="Smart Expense Tracker",
            font=FONTS["small"],
            text_color=self.theme.get("text_muted", "#808098"),
        )
        tagline.pack(anchor="w", pady=(2, 0))

        # ─── Divider ─────────────────────────────────────────
        divider = ctk.CTkFrame(self, fg_color=self.theme.get("border", "#2a2a3e"), height=1)
        divider.pack(fill="x", padx=18, pady=(18, 18))

        # ─── Menu Label ──────────────────────────────────────
        menu_label = ctk.CTkLabel(
            self, text="MENU", font=FONTS["small_bold"],
            text_color=self.theme.get("text_muted", "#808098"),
            anchor="w"
        )
        menu_label.pack(fill="x", padx=22, pady=(0, 10))

        # ─── Navigation Buttons ──────────────────────────────
        for item in self.NAV_ITEMS:
            btn = self._create_nav_button(item)
            self.nav_buttons[item["view"]] = btn

        # Set initial active state
        self._set_active("dashboard")

        # ─── Spacer ──────────────────────────────────────────
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # ─── Theme Toggle ────────────────────────────────────
        if self.on_theme_toggle:
            toggle_divider = ctk.CTkFrame(
                self, fg_color=self.theme.get("border", "#2a2a3e"), height=1
            )
            toggle_divider.pack(fill="x", padx=18, pady=(0, 12))

            toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
            toggle_frame.pack(fill="x", padx=14, pady=(0, 6))

            is_dark = self.app_mode == "dark"
            toggle_icon = "🌙" if is_dark else "☀️"
            toggle_label = "Dark Mode" if is_dark else "Light Mode"

            self.theme_toggle_btn = ctk.CTkButton(
                toggle_frame,
                text=f"  {toggle_icon}  {toggle_label}",
                font=FONTS["nav"],
                fg_color=self.theme.get("sidebar_active", "#1a1a2e"),
                text_color="#ffffff" if is_dark else "#e0e0e0",
                hover_color=self.theme.get("accent", "#6c5ce7"),
                anchor="w",
                height=44,
                corner_radius=10,
                command=self._on_toggle_theme,
            )
            self.theme_toggle_btn.pack(fill="x")

        # ─── Footer ──────────────────────────────────────────
        footer_divider = ctk.CTkFrame(self, fg_color=self.theme.get("border", "#2a2a3e"), height=1)
        footer_divider.pack(fill="x", padx=18, pady=(10, 10))

        version_label = ctk.CTkLabel(
            self, text="v1.0.0",
            font=FONTS["small"],
            text_color=self.theme.get("text_muted", "#808098"),
        )
        version_label.pack(pady=(0, 18))

    def _create_nav_button(self, item):
        """Create a single navigation button."""
        btn = ctk.CTkButton(
            self,
            text=f"  {item['icon']}  {item['name']}",
            font=FONTS["nav"],
            fg_color="transparent",
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            hover_color=self.theme.get("sidebar_active", "#1a1a2e"),
            anchor="w",
            height=46,
            corner_radius=10,
            command=lambda v=item["view"]: self._on_click(v),
        )
        btn.pack(fill="x", padx=14, pady=3)
        return btn

    def _on_click(self, view_name):
        """Handle nav button click."""
        self._set_active(view_name)
        self.on_navigate(view_name)

    def _on_toggle_theme(self):
        """Handle theme toggle button click."""
        if self.on_theme_toggle:
            # Pass None to signal a toggle (app.py handles flipping)
            self.on_theme_toggle(None)

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
                    text_color=self.theme.get("text_secondary", "#b0b0c0"),
                    font=FONTS["nav"],
                )

    def update_theme(self, theme):
        """Update sidebar colors when theme changes."""
        self.theme = theme
        self.configure(fg_color=theme["sidebar"])
        # Re-apply active state with new colors
        self._set_active(self.active_view)
