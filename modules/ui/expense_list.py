"""
Expense Tracker — Expense List View
Scrollable list of expenses with Bill grouping support and advanced filtering.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from config import CATEGORIES, CURRENCY_SYMBOL, DATE_FORMAT
from modules.theme import FONTS
from modules.ui.components import ExpenseCard, SearchBar, EmptyState, BillGroupCard


class ExpenseListView(ctk.CTkFrame):
    """Expense list with grouping, search, and filter functionality."""

    def __init__(self, master, db, theme, on_data_changed=None, on_navigate=None, **kwargs):
        self.db = db
        self.theme = theme
        self.on_data_changed = on_data_changed
        self.on_navigate = on_navigate
        
        # State
        self.current_category = "All"
        self.current_period = "All Time"
        self.current_search = ""
        self.view_mode = "List"  # "List" or "Grouped"
        
        self.page_size = 20
        self.loaded_count = 0

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

        # View Mode Toggle
        self.view_toggle = ctk.CTkSegmentedButton(
            header, values=["List", "Bills"],
            command=self._on_view_mode_change,
            selected_color=self.theme.get("accent", "#6c5ce7"),
            selected_hover_color=self.theme.get("accent_hover", "#7d6ff0"),
            fg_color=self.theme.get("surface", "#12121a"),
            unselected_color=self.theme.get("surface", "#12121a"),
            unselected_hover_color=self.theme.get("card_hover", "#1f1f35"),
            text_color=self.theme.get("text", "#f0f0f5"),
            font=FONTS["small_bold"],
        )
        self.view_toggle.set(self.view_mode)
        self.view_toggle.pack(side="right")

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

    def _load_expenses(self, append=False):
        """Load and display expenses based on current filters and view mode."""
        if not append:
            for widget in self.list_frame.winfo_children():
                widget.destroy()
            self.loaded_count = 0

        category = self.category_var.get()
        start_date, end_date = self._get_date_range()

        if self.view_mode == "Bills" and not append:
            self._load_grouped_by_bill()
            return

        # Standard List View logic
        stats = self.db.get_filtered_total_and_count(
            category=category if category != "All" else None,
            start_date=start_date,
            end_date=end_date,
            search=self.current_search if self.current_search else None,
        )
        
        filtered_total = stats["total"]
        filtered_count = stats["count"]
        
        expenses = self.db.get_expenses_filtered(
            category=category if category != "All" else None,
            start_date=start_date,
            end_date=end_date,
            search=self.current_search if self.current_search else None,
            limit=self.page_size,
            offset=self.loaded_count
        )

        self.count_label.configure(text=f"Showing {self.loaded_count + len(expenses)} of {filtered_count}")

        if not append and filtered_count > 0:
            total_frame = ctk.CTkFrame(self.list_frame, fg_color=self.theme.get("card", "#1a1a2e"), corner_radius=10)
            total_frame.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(total_frame, text=f"Total Expenditure: {CURRENCY_SYMBOL}{filtered_total:,.2f}", 
                        font=FONTS["body_bold"], text_color=self.theme.get("accent", "#6c5ce7")).pack(padx=20, pady=10)

        if expenses:
            for exp in expenses:
                card = ExpenseCard(self.list_frame, exp, theme=self.theme, on_delete=self._on_delete)
                card.pack(fill="x", pady=4)
            self.loaded_count += len(expenses)
            
            if self.loaded_count < filtered_count:
                self.load_more_btn = ctk.CTkButton(
                    self.list_frame, text="Load More", command=self._load_more,
                    fg_color="transparent", text_color=self.theme.get("accent", "#6c5ce7"),
                    font=FONTS["body_bold"], hover_color=self.theme.get("card_hover", "#1f1f35"),
                )
                self.load_more_btn.pack(pady=20)
        elif not append:
            self._show_empty_state()

    def _load_grouped_by_bill(self):
        """Load expenses grouped by bill."""
        bills_summary = self.db.get_bill_summary()
        
        if not bills_summary:
            self._show_empty_state("No Bills Found", "Create your first bill in the 'Add Expense' tab.")
            return

        for bill in bills_summary:
            expenses = self.db.get_expenses_by_bill(bill["id"])
            if expenses:
                card = BillGroupCard(
                    self.list_frame, bill, expenses, 
                    theme=self.theme,
                    on_delete_expense=self._on_delete
                )
                card.pack(fill="x", pady=10)

        # Show unbilled expenses if any
        unbilled = self.db.get_expenses_filtered(limit=100) # Simple fetch
        unbilled = [e for e in unbilled if e.get("bill_id") is None]
        
        if unbilled:
            spacer = ctk.CTkFrame(self.list_frame, height=40, fg_color="transparent")
            spacer.pack(fill="x")
            
            ctk.CTkLabel(
                self.list_frame, text="Individual Expenses",
                font=FONTS["subheading"], text_color=self.theme.get("text_secondary", "#b0b0c0"),
                anchor="w"
            ).pack(fill="x", padx=10, pady=(0, 10))
            
            for exp in unbilled:
                card = ExpenseCard(self.list_frame, exp, theme=self.theme, on_delete=self._on_delete)
                card.pack(fill="x", pady=4)

    def _show_empty_state(self, title="No expenses found", message="Try adjusting your filters or search query."):
        EmptyState(
            self.list_frame,
            title=title,
            message=message,
            icon="📭",
            theme=self.theme,
            action_text="➕  Add Expense",
            action_command=lambda: self.on_navigate("add_expense") if self.on_navigate else None
        ).pack(expand=True, fill="both", pady=40)

    def _on_view_mode_change(self, value):
        """Switch between List and Grouped view."""
        self.view_mode = "List" if value == "List" else "Bills"
        self._load_expenses()

    def _load_more(self):
        if hasattr(self, "load_more_btn"):
            self.load_more_btn.destroy()
        self._load_expenses(append=True)

    def _on_search(self, value):
        self.current_search = value
        self._load_expenses()

    def _on_category_change(self, value):
        self._load_expenses()

    def _on_period_change(self, value):
        self._load_expenses()

    def _on_delete(self, expense_id):
        dialog = ctk.CTkInputDialog(text=f"Type 'yes' to confirm deletion:", title="Delete Expense")
        result = dialog.get_input()
        if result and result.lower() == "yes":
            self.db.delete_expense(expense_id)
            self._load_expenses()
            if self.on_data_changed: self.on_data_changed()

    def refresh(self, theme=None, **kwargs):
        if theme: self.theme = theme
        for widget in self.winfo_children(): widget.destroy()
        self._build_ui()
