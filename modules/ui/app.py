"""
Expense Tracker — Main Application Window
Orchestrates sidebar, content views, theme switching, and database.
"""

import customtkinter as ctk

from config import WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT, SIDEBAR_WIDTH, APP_TITLE
from modules.database import ExpenseDB
from modules.theme import get_theme, FONTS
from modules.ui.sidebar import Sidebar
from modules.ui.dashboard import DashboardView
from modules.ui.add_expense import AddExpenseView
from modules.ui.expense_list import ExpenseListView
from modules.ui.charts import ChartsView
from modules.ui.settings import SettingsView


class ExpenseTrackerApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # ─── Database ────────────────────────────────────────
        self.db = ExpenseDB()

        # ─── Theme ───────────────────────────────────────────
        saved_mode = self.db.get_setting("theme_mode", "dark")
        self.app_mode = saved_mode
        self.theme = get_theme(self.app_mode)

        # ─── Window Setup ────────────────────────────────────
        self.title(APP_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.configure(fg_color=self.theme["bg"])

        # Set appearance mode to match saved preference
        ctk.set_appearance_mode(self.app_mode)
        ctk.set_default_color_theme("blue")

        # ─── Project Session State ───────────────────────────
        self.active_project_id = None
        self.active_project_name = None

        # ─── Layout ──────────────────────────────────────────
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = Sidebar(
            self, theme=self.theme,
            on_navigate=self.switch_view,
            on_theme_toggle=self._on_theme_change,
            app_mode=self.app_mode,
            width=SIDEBAR_WIDTH,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Content area
        self.content_frame = ctk.CTkFrame(self, fg_color=self.theme["bg"], corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        self.project_banner = ctk.CTkFrame(self.content_frame, fg_color=self.theme.get("success_bg", "#0a2e2d"), corner_radius=0)
        self.project_banner.grid_columnconfigure(0, weight=1)
        
        self.project_banner_label = ctk.CTkLabel(self.project_banner, text="", font=FONTS["body_bold"], text_color=self.theme.get("success", "#00cec9"))
        self.project_banner_label.grid(row=0, column=0, sticky="w", padx=20, pady=10)
        
        ctk.CTkButton(self.project_banner, text="End Project", font=FONTS["small_bold"], width=120, height=30,
                      fg_color=self.theme.get("accent", "#6c5ce7"), hover_color=self.theme.get("accent_hover", "#7d6ff0"),
                      command=self.finish_project_session).grid(row=0, column=1, padx=20, pady=10)

        # ─── Views ───────────────────────────────────────────
        self.current_view_name = "dashboard"
        self.current_view = None
        self._show_view("dashboard")

        # ─── Cleanup on close ────────────────────────────────
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def switch_view(self, view_name):
        """Switch to a different view."""
        if view_name == self.current_view_name and self.current_view:
            return
        self._show_view(view_name)

    def _show_view(self, view_name):
        """Create and show the requested view."""
        # Destroy current view
        if self.current_view:
            self.current_view.destroy()

        self.current_view_name = view_name

        # Create new view
        if view_name == "dashboard":
            self.current_view = DashboardView(
                self.content_frame, db=self.db,
                theme=self.theme, app_mode=self.app_mode,
                on_navigate=self.switch_view,
            )
        elif view_name == "add_expense":
            self.current_view = AddExpenseView(
                self.content_frame, db=self.db,
                theme=self.theme,
                on_expense_added=self._on_data_changed,
                # Session-based grouping
                active_project_id=self.active_project_id,
                active_project_name=self.active_project_name,
                on_start_session=self.start_project_session,
                on_finish_session=self.finish_project_session,
            )
        elif view_name == "expense_list":
            self.current_view = ExpenseListView(
                self.content_frame, db=self.db,
                theme=self.theme,
                on_data_changed=self._on_data_changed,
                on_navigate=self.switch_view,
            )
        elif view_name == "charts":
            self.current_view = ChartsView(
                self.content_frame, db=self.db,
                theme=self.theme, app_mode=self.app_mode,
                on_navigate=self.switch_view,
            )
        elif view_name == "settings":
            self.current_view = SettingsView(
                self.content_frame, db=self.db,
                theme=self.theme, app_mode=self.app_mode,
                on_theme_change=self._on_theme_change,
                on_data_changed=self._on_data_changed,
            )

        if self.current_view:
            self.current_view.grid(row=1, column=0, sticky="nsew")
            
        if self.active_project_id:
            self.project_banner_label.configure(text=f"📂 Active Project: {self.active_project_name}")
            self.project_banner.grid(row=0, column=0, sticky="new")
        else:
            self.project_banner.grid_forget()

    def _on_data_changed(self):
        """Called when expense data changes — refresh current view."""
        self._show_view(self.current_view_name)

    def _on_theme_change(self, mode=None):
        """Handle theme mode change — instantly refreshes ALL widgets."""
        if mode is None:
            mode = "light" if self.app_mode == "dark" else "dark"

        self.app_mode = mode
        self.theme = get_theme(mode)
        self.db.set_setting("theme_mode", mode)

        # Sync CustomTkinter global appearance
        ctk.set_appearance_mode(mode)

        # Update root + content frame backgrounds
        self.configure(fg_color=self.theme["bg"])
        self.content_frame.configure(fg_color=self.theme["bg"])

        # ── Rebuild Sidebar with new theme ───────────────────
        self.sidebar.destroy()
        self.sidebar = Sidebar(
            self, theme=self.theme,
            on_navigate=self.switch_view,
            on_theme_toggle=self._on_theme_change,
            app_mode=self.app_mode,
            width=SIDEBAR_WIDTH,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar._set_active(self.current_view_name)

        # ── Rebuild Project Banner with new theme ─────────────
        self.project_banner.configure(
            fg_color=self.theme.get("success_bg", "#0a2e2d")
        )
        self.project_banner_label.configure(
            text_color=self.theme.get("success", "#00cec9")
        )

        # ── Rebuild Current View with new theme ───────────────
        # Destroy and recreate view so every inner widget uses new colors.
        # This is the correct approach for CTk — avoids fighting internal theming.
        self._show_view(self.current_view_name)

        # Force full layout recalculation
        self.update_idletasks()

    # ─── Project Session Management ───────────────────────────

    def start_project_session(self, name):
        """Start a new project grouping session."""
        project_id = self.db.add_bill(name)
        self.active_project_id = project_id
        self.active_project_name = name
        self._on_data_changed() # Refresh UI to show session banner

    def finish_project_session(self):
        """End current project session."""
        self.active_project_id = None
        self.active_project_name = None
        self._on_data_changed()

    def _on_close(self):
        """Clean up on window close."""
        self.db.close()
        self.destroy()
