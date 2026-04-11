"""
Expense Tracker — Add Expense View
Form to add a new expense with validation and instant feedback.
"""

import customtkinter as ctk
from datetime import datetime
from config import CATEGORIES, CURRENCY_SYMBOL, CATEGORY_ICONS, DATE_FORMAT
from modules.theme import FONTS
from modules.models import Expense


class AddExpenseView(ctk.CTkFrame):
    """Add expense form with validation."""

    def __init__(self, master, db, theme, on_expense_added=None, **kwargs):
        self.db = db
        self.theme = theme
        self.on_expense_added = on_expense_added

        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        """Build the form layout."""

        # ─── Scrollable container ────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.theme.get("scrollbar", "#2a2a3e"),
        )
        scroll.pack(fill="both", expand=True)
        content = scroll

        # ─── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 8))

        ctk.CTkLabel(
            header, text="Add New Expense",
            font=FONTS["heading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w"
        ).pack(side="left")

        # ─── Form Card ──────────────────────────────────────
        form_card = ctk.CTkFrame(
            content,
            fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16,
            border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        form_card.pack(fill="x", padx=28, pady=(16, 0))

        form_inner = ctk.CTkFrame(form_card, fg_color="transparent")
        form_inner.pack(fill="x", padx=36, pady=32)

        # ─── Amount Field ────────────────────────────────────
        ctk.CTkLabel(
            form_inner, text="Amount", font=FONTS["body_bold"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", pady=(0, 8))

        amount_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        amount_frame.pack(fill="x", pady=(0, 20))

        currency_label = ctk.CTkLabel(
            amount_frame, text=CURRENCY_SYMBOL,
            font=("Segoe UI", 28, "bold"),
            text_color=self.theme.get("accent", "#6c5ce7"),
        )
        currency_label.pack(side="left", padx=(0, 10))

        self.amount_var = ctk.StringVar()
        self.amount_entry = ctk.CTkEntry(
            amount_frame,
            textvariable=self.amount_var,
            placeholder_text="0.00",
            font=("Segoe UI", 28),
            fg_color=self.theme.get("input_bg", "#16162a"),
            border_color=self.theme.get("input_border", "#2a2a40"),
            text_color=self.theme.get("text", "#f0f0f5"),
            placeholder_text_color=self.theme.get("text_muted", "#808098"),
            height=55,
            corner_radius=12,
        )
        self.amount_entry.pack(side="left", fill="x", expand=True)

        # ─── Category Field ──────────────────────────────────
        ctk.CTkLabel(
            form_inner, text="Category", font=FONTS["body_bold"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", pady=(0, 8))

        # Category options with icons
        cat_options = [f"{CATEGORY_ICONS.get(c, '')} {c}" for c in CATEGORIES]
        self.category_var = ctk.StringVar(value=cat_options[0])

        self.category_menu = ctk.CTkOptionMenu(
            form_inner,
            values=cat_options,
            variable=self.category_var,
            font=FONTS["body"],
            fg_color=self.theme.get("input_bg", "#16162a"),
            button_color=self.theme.get("accent", "#6c5ce7"),
            button_hover_color=self.theme.get("accent_hover", "#7d6ff0"),
            dropdown_fg_color=self.theme.get("surface", "#12121a"),
            dropdown_hover_color=self.theme.get("card_hover", "#1f1f35"),
            dropdown_text_color=self.theme.get("text", "#f0f0f5"),
            text_color=self.theme.get("text", "#f0f0f5"),
            height=44,
            corner_radius=10,
        )
        self.category_menu.pack(fill="x", pady=(0, 20))

        # ─── Date + Note Row ─────────────────────────────────
        row_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 20))
        row_frame.columnconfigure((0, 1), weight=1, uniform="field")

        # Date
        date_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        date_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            date_col, text="Date", font=FONTS["body_bold"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", pady=(0, 8))

        self.date_var = ctk.StringVar(value=datetime.now().strftime(DATE_FORMAT))
        self.date_entry = ctk.CTkEntry(
            date_col,
            textvariable=self.date_var,
            placeholder_text="YYYY-MM-DD",
            font=FONTS["body"],
            fg_color=self.theme.get("input_bg", "#16162a"),
            border_color=self.theme.get("input_border", "#2a2a40"),
            text_color=self.theme.get("text", "#f0f0f5"),
            placeholder_text_color=self.theme.get("text_muted", "#808098"),
            height=44,
            corner_radius=10,
        )
        self.date_entry.pack(fill="x")

        # Note
        note_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        note_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(
            note_col, text="Note (optional)", font=FONTS["body_bold"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", pady=(0, 8))

        self.note_var = ctk.StringVar()
        self.note_entry = ctk.CTkEntry(
            note_col,
            textvariable=self.note_var,
            placeholder_text="e.g., Lunch with friends",
            font=FONTS["body"],
            fg_color=self.theme.get("input_bg", "#16162a"),
            border_color=self.theme.get("input_border", "#2a2a40"),
            text_color=self.theme.get("text", "#f0f0f5"),
            placeholder_text_color=self.theme.get("text_muted", "#808098"),
            height=44,
            corner_radius=10,
        )
        self.note_entry.pack(fill="x")

        # ─── Error / Success Message ─────────────────────────
        self.message_label = ctk.CTkLabel(
            form_inner, text="", font=FONTS["body"],
            text_color=self.theme.get("danger", "#ff7675"),
            anchor="w"
        )
        self.message_label.pack(fill="x", pady=(6, 10))

        # ─── Add Button ─────────────────────────────────────
        self.add_btn = ctk.CTkButton(
            form_inner,
            text="➕  Add Expense",
            font=FONTS["button"],
            fg_color=self.theme.get("accent", "#6c5ce7"),
            hover_color=self.theme.get("accent_hover", "#7d6ff0"),
            text_color="#ffffff",
            height=52,
            corner_radius=12,
            command=self._on_add,
        )
        self.add_btn.pack(fill="x", pady=(0, 6))

        # ─── Quick Add Hint ─────────────────────────────────
        hint = ctk.CTkLabel(
            content, text="💡 Tip: Press Enter to add quickly",
            font=FONTS["small"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
        )
        hint.pack(pady=(14, 0))

        # ─── Budget Status (compact) ─────────────────────────
        self._build_budget_status(content)

        # Bind Enter key
        self.amount_entry.bind("<Return>", lambda e: self._on_add())
        self.note_entry.bind("<Return>", lambda e: self._on_add())
        self.date_entry.bind("<Return>", lambda e: self._on_add())

    def _on_add(self):
        """Handle add expense button click."""
        # Validate amount
        amount = Expense.validate_amount(self.amount_var.get())
        if amount is None:
            self._show_error("❌ Please enter a valid amount greater than 0")
            return

        # Validate date
        date = Expense.validate_date(self.date_var.get())
        if date is None:
            self._show_error("❌ Invalid date format. Use YYYY-MM-DD")
            return

        # Extract category (remove icon prefix)
        cat_str = self.category_var.get()
        category = cat_str.split(" ", 1)[-1] if " " in cat_str else cat_str

        note = self.note_var.get().strip()

        # Add to database
        self.db.add_expense(amount, category, date, note)

        # Show success
        self._show_success(f"✅ Added {CURRENCY_SYMBOL}{amount:,.2f} for {category}")

        # Clear form
        self.amount_var.set("")
        self.note_var.set("")
        self.date_var.set(datetime.now().strftime(DATE_FORMAT))
        self.amount_entry.focus()

        # Notify app
        if self.on_expense_added:
            self.on_expense_added()

    def _show_error(self, msg):
        """Show error message."""
        self.message_label.configure(
            text=msg,
            text_color=self.theme.get("danger", "#ff7675"),
        )
        self.after(4000, lambda: self.message_label.configure(text=""))

    def _show_success(self, msg):
        """Show success message."""
        self.message_label.configure(
            text=msg,
            text_color=self.theme.get("success", "#00cec9"),
        )
        self.after(4000, lambda: self.message_label.configure(text=""))

    def _build_budget_status(self, parent):
        """Build a compact budget usage indicator below the form."""
        budget_str = self.db.get_setting("monthly_budget", "0")
        budget = float(budget_str) if budget_str else 0
        if budget <= 0:
            return

        monthly_spent = self.db.get_monthly_total()
        pct = (monthly_spent / budget * 100) if budget > 0 else 0
        remaining = max(budget - monthly_spent, 0)

        # Color based on threshold
        if pct >= 90:
            bar_color = "#e17055"
        elif pct >= 70:
            bar_color = "#fdcb6e"
        else:
            bar_color = "#00b894"

        # Compact budget card
        budget_card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=12,
            border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        budget_card.pack(fill="x", padx=28, pady=(14, 16))

        inner = ctk.CTkFrame(budget_card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=14)

        # Title row with percentage
        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row, text="📋  Budget This Month",
            font=FONTS["body_bold"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            title_row,
            text=f"{CURRENCY_SYMBOL}{monthly_spent:,.0f} / {CURRENCY_SYMBOL}{budget:,.0f}  ({pct:.0f}%)",
            font=FONTS["small_bold"],
            text_color=bar_color,
            anchor="e",
        ).pack(side="right")

        # Mini progress bar
        bar_bg = ctk.CTkFrame(
            inner,
            fg_color=self.theme.get("input_bg", "#16162a"),
            corner_radius=6,
            height=10,
        )
        bar_bg.pack(fill="x", pady=(8, 0))
        bar_bg.pack_propagate(False)

        fill_pct = min(pct, 100) / 100.0
        if fill_pct > 0:
            bar_fill = ctk.CTkFrame(
                bar_bg, fg_color=bar_color, corner_radius=6,
            )
            bar_fill.place(relx=0, rely=0, relheight=1.0, relwidth=fill_pct)

        # Remaining text
        if pct >= 100:
            overspend = monthly_spent - budget
            status_text = f"🚨 Over budget by {CURRENCY_SYMBOL}{overspend:,.2f}"
            status_color = self.theme.get("danger", "#ff7675")
        else:
            status_text = f"✅ {CURRENCY_SYMBOL}{remaining:,.2f} remaining"
            status_color = self.theme.get("success", "#00cec9") if pct < 70 else bar_color

        ctk.CTkLabel(
            inner, text=status_text,
            font=FONTS["small"],
            text_color=status_color,
            anchor="w",
        ).pack(fill="x", pady=(6, 0))

    def refresh(self, theme=None, **kwargs):
        """Rebuild with updated theme."""
        if theme:
            self.theme = theme
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
