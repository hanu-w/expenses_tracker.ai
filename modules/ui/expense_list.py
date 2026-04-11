"""
Expense Tracker — Expense List View
Scrollable list of all expenses with search, filter, and delete.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from config import CATEGORIES, CURRENCY_SYMBOL, DATE_FORMAT
from modules.theme import FONTS
from modules.ui.components import ExpenseCard, SearchBar


class ExpenseListView(ctk.CTkFrame):
    """Expense list with search, filter, and delete functionality."""

    def __init__(self, master, db, theme, on_data_changed=None, **kwargs):
        self.db = db
        self.theme = theme
        self.on_data_changed = on_data_changed
        self.current_category = "All"
        self.current_period = "All Time"
        self.current_search = ""

        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        """Build the expense list layout."""

        # ─── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 8))

        ctk.CTkLabel(
            header, text="Expenses",
            font=FONTS["heading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w"
        ).pack(side="left")

        # ─── Search & Filters ────────────────────────────────
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=28, pady=(12, 0))

        # Search bar
        self.search_bar = SearchBar(
            filter_frame,
            placeholder="Search by category or note...",
            on_search=self._on_search,
            theme=self.theme,
        )
        self.search_bar.pack(fill="x", pady=(0, 12))

        # Filter row
        filter_row = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_row.pack(fill="x")

        # Category filter
        ctk.CTkLabel(
            filter_row, text="Category:", font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
        ).pack(side="left", padx=(0, 8))

        cat_options = ["All"] + CATEGORIES
        self.category_var = ctk.StringVar(value="All")
        cat_menu = ctk.CTkOptionMenu(
            filter_row, values=cat_options, variable=self.category_var,
            font=FONTS["body"], width=150, height=36, corner_radius=8,
            fg_color=self.theme.get("input_bg", "#16162a"),
            button_color=self.theme.get("accent", "#6c5ce7"),
            button_hover_color=self.theme.get("accent_hover", "#7d6ff0"),
            dropdown_fg_color=self.theme.get("surface", "#12121a"),
            dropdown_hover_color=self.theme.get("card_hover", "#1f1f35"),
            dropdown_text_color=self.theme.get("text", "#f0f0f5"),
            text_color=self.theme.get("text", "#f0f0f5"),
            command=self._on_category_change,
        )
        cat_menu.pack(side="left", padx=(0, 20))

        # Period filter
        ctk.CTkLabel(
            filter_row, text="Period:", font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
        ).pack(side="left", padx=(0, 8))

        periods = ["All Time", "This Week", "This Month", "Last 3 Months"]
        self.period_var = ctk.StringVar(value="All Time")
        period_menu = ctk.CTkOptionMenu(
            filter_row, values=periods, variable=self.period_var,
            font=FONTS["body"], width=150, height=36, corner_radius=8,
            fg_color=self.theme.get("input_bg", "#16162a"),
            button_color=self.theme.get("accent", "#6c5ce7"),
            button_hover_color=self.theme.get("accent_hover", "#7d6ff0"),
            dropdown_fg_color=self.theme.get("surface", "#12121a"),
            dropdown_hover_color=self.theme.get("card_hover", "#1f1f35"),
            dropdown_text_color=self.theme.get("text", "#f0f0f5"),
            text_color=self.theme.get("text", "#f0f0f5"),
            command=self._on_period_change,
        )
        period_menu.pack(side="left")

        # Count label (right side)
        self.count_label = ctk.CTkLabel(
            filter_row, text="", font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
        )
        self.count_label.pack(side="right")

        # ─── Expense List ────────────────────────────────────
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.theme.get("scrollbar", "#2a2a3e"),
        )
        self.list_frame.pack(fill="both", expand=True, padx=28, pady=(14, 20))

        self._load_expenses()

    def _get_date_range(self):
        """Get start/end date based on selected period."""
        period = self.period_var.get()
        today = datetime.now()

        if period == "This Week":
            start = today - timedelta(days=today.weekday())
            return start.strftime(DATE_FORMAT), today.strftime(DATE_FORMAT)
        elif period == "This Month":
            start = today.replace(day=1)
            return start.strftime(DATE_FORMAT), today.strftime(DATE_FORMAT)
        elif period == "Last 3 Months":
            start = today - timedelta(days=90)
            return start.strftime(DATE_FORMAT), today.strftime(DATE_FORMAT)
        else:
            return None, None

    def _load_expenses(self):
        """Load and display expenses based on current filters."""
        # Clear existing cards
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        # Get filtered data
        category = self.category_var.get()
        start_date, end_date = self._get_date_range()

        expenses = self.db.get_expenses_filtered(
            category=category if category != "All" else None,
            start_date=start_date,
            end_date=end_date,
            search=self.current_search if self.current_search else None,
        )

        total_count = self.db.get_expense_count()
        self.count_label.configure(text=f"Showing {len(expenses)} of {total_count}")

        if expenses:
            # Show total for filtered results
            filtered_total = sum(e["amount"] for e in expenses)
            total_frame = ctk.CTkFrame(
                self.list_frame,
                fg_color=self.theme.get("card", "#1a1a2e"),
                corner_radius=10,
            )
            total_frame.pack(fill="x", pady=(0, 10))

            ctk.CTkLabel(
                total_frame,
                text=f"Total: {CURRENCY_SYMBOL}{filtered_total:,.2f}",
                font=FONTS["body_bold"],
                text_color=self.theme.get("accent", "#6c5ce7"),
            ).pack(padx=20, pady=10)

            for exp in expenses:
                card = ExpenseCard(
                    self.list_frame, exp,
                    theme=self.theme,
                    on_delete=self._on_delete,
                )
                card.pack(fill="x", pady=4)
        else:
            empty_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=60)

            ctk.CTkLabel(
                empty_frame, text="📭", font=("Segoe UI", 52),
            ).pack()

            ctk.CTkLabel(
                empty_frame, text="No expenses found",
                font=FONTS["subheading"],
                text_color=self.theme.get("text_secondary", "#b0b0c0"),
            ).pack(pady=(10, 6))

            ctk.CTkLabel(
                empty_frame, text="Try adjusting your filters or add a new expense",
                font=FONTS["body"],
                text_color=self.theme.get("text_secondary", "#b0b0c0"),
            ).pack()

    def _on_search(self, value):
        """Handle search input change."""
        self.current_search = value
        self._load_expenses()

    def _on_category_change(self, value):
        """Handle category filter change."""
        self._load_expenses()

    def _on_period_change(self, value):
        """Handle period filter change."""
        self._load_expenses()

    def _on_delete(self, expense_id):
        """Handle delete expense."""
        # Confirmation dialog
        dialog = ctk.CTkInputDialog(
            text=f"Type 'yes' to confirm deletion:",
            title="Delete Expense",
        )
        result = dialog.get_input()
        if result and result.lower() == "yes":
            self.db.delete_expense(expense_id)
            self._load_expenses()
            if self.on_data_changed:
                self.on_data_changed()

    def refresh(self, theme=None, **kwargs):
        """Rebuild with updated theme or fresh data."""
        if theme:
            self.theme = theme
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
