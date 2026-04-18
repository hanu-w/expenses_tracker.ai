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

        # ─── Bill Session State ──────────────────────────────
        self.active_bill_id = None
        self.active_bill_name = None

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
        self.content_frame.grid_rowconfigure(0, weight=1)

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
                active_bill_id=self.active_bill_id,
                active_bill_name=self.active_bill_name,
                on_start_session=self.start_bill_session,
                on_finish_session=self.finish_bill_session,
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
            self.current_view.grid(row=0, column=0, sticky="nsew")

    def _on_data_changed(self):
        """Called when expense data changes — refresh current view."""
        self._show_view(self.current_view_name)

    def _on_theme_change(self, mode=None):
        """Handle theme mode change. If mode is None, toggle current mode."""
        if mode is None:
            mode = "light" if self.app_mode == "dark" else "dark"

        self.app_mode = mode
        self.theme = get_theme(mode)
        self.db.set_setting("theme_mode", mode)

        # Sync CustomTkinter appearance mode
        ctk.set_appearance_mode(mode)

        # Update app background
        self.configure(fg_color=self.theme["bg"])
        self.content_frame.configure(fg_color=self.theme["bg"])

    # ─── Bill Session Management ──────────────────────────────

    def start_bill_session(self, name):
        """Start a new bill grouping session."""
        bill_id = self.db.add_bill(name)
        self.active_bill_id = bill_id
        self.active_bill_name = name
        self._on_data_changed() # Refresh UI to show session banner

    def finish_bill_session(self):
        """End current bill session."""
        self.active_bill_id = None
        self.active_bill_name = None
        self._on_data_changed()

        # Rebuild sidebar with new theme
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

        # Rebuild current view with new theme
        self._show_view(self.current_view_name)

    def _on_close(self):
        """Clean up on window close."""
        self.db.close()
        self.destroy()
