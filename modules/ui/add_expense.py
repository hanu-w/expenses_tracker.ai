"""
Expense Tracker — Add Expense View
Modern fintech-style form to add a new expense with bill grouping support.
"""

import customtkinter as ctk
from datetime import datetime
from config import CATEGORIES, CURRENCY_SYMBOL, CATEGORY_ICONS, DATE_FORMAT
from modules.theme import FONTS
from modules.models import Expense
from modules.ui.components import ModernInput


class AddExpenseView(ctk.CTkFrame):
    """Modern add expense form with validation and bill support."""

    def __init__(self, master, db, theme, on_expense_added=None, **kwargs):
        self.db = db
        self.theme = theme
        self.on_expense_added = on_expense_added
        
        # State for bills
        self.bills = []
        self.show_new_bill_input = False

        super().__init__(master, fg_color="transparent", **kwargs)
        self._load_data()
        self._build_ui()

    def _load_data(self):
        """Fetch bills from DB."""
        self.bills = self.db.get_all_bills()

    def _build_ui(self):
        """Build the modernized form layout."""

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

        # ─── Main Form Layout ────────────────────────────────
        form_container = ctk.CTkFrame(content, fg_color="transparent")
        form_container.pack(fill="x", padx=28, pady=16)

        # ─── SECTION 1: Amount (Prominent) ───────────────────
        self.amount_var = ctk.StringVar()
        self.amount_input = ModernInput(
            form_container, 
            label_text="How much did you spend?",
            icon=CURRENCY_SYMBOL,
            placeholder="0.00",
            variable=self.amount_var,
            font=("Segoe UI", 32, "bold"),
            height=80,
            theme=self.theme
        )
        self.amount_input.pack(fill="x", pady=(0, 24))

        # ─── SECTION 2: Transaction Details ──────────────────
        details_label = ctk.CTkLabel(
            form_container, text="Transaction Details",
            font=FONTS["subheading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w"
        )
        details_label.pack(fill="x", pady=(0, 12))

        # Grid for Category and Date
        grid_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        grid_frame.pack(fill="x", pady=(0, 20))
        grid_frame.columnconfigure((0, 1), weight=1, uniform="group1")

        # Category
        cat_options = [f"{CATEGORY_ICONS.get(c, '')} {c}" for c in CATEGORIES]
        self.category_var = ctk.StringVar(value=cat_options[0])
        self.category_input = ModernInput(
            grid_frame,
            label_text="Category",
            icon="🏷️",
            is_option_menu=True,
            options=cat_options,
            variable=self.category_var,
            theme=self.theme
        )
        self.category_input.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Date
        self.date_var = ctk.StringVar(value=datetime.now().strftime(DATE_FORMAT))
        self.date_input = ModernInput(
            grid_frame,
            label_text="Date",
            icon="📅",
            placeholder="YYYY-MM-DD",
            variable=self.date_var,
            theme=self.theme
        )
        self.date_input.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # ─── SECTION 3: Bill / Grouping ──────────────────────
        self._build_bill_section(form_container)

        # ─── SECTION 4: Notes ────────────────────────────────
        self.note_var = ctk.StringVar()
        self.note_input = ModernInput(
            form_container,
            label_text="Add a note",
            icon="🖋️",
            placeholder="e.g., Dinner with family",
            variable=self.note_var,
            theme=self.theme
        )
        self.note_input.pack(fill="x", pady=(10, 20))

        # ─── Error / Success Message ─────────────────────────
        self.message_label = ctk.CTkLabel(
            form_container, text="", font=FONTS["body"],
            text_color=self.theme.get("danger", "#ff7675"),
            anchor="w"
        )
        self.message_label.pack(fill="x", pady=(0, 10))

        # ─── Submit Button ──────────────────────────────────
        self.add_btn = ctk.CTkButton(
            form_container,
            text="Add Expense",
            font=FONTS["button"],
            fg_color=self.theme.get("accent", "#6c5ce7"),
            hover_color=self.theme.get("accent_hover", "#7d6ff0"),
            text_color="#ffffff",
            height=56,
            corner_radius=14,
            command=self._on_add,
        )
        self.add_btn.pack(fill="x", pady=(0, 6))

        # ─── Quick Add Hint ─────────────────────────────────
        hint = ctk.CTkLabel(
            content, text="💡 Tip: Create Bills to group related expenses like trips or projects",
            font=FONTS["small"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
        )
        hint.pack(pady=(14, 0))

        # ─── Budget Status ───────────────────────────────────
        self._build_budget_status(content)

        # Bind Enter key
        self.amount_input.input.bind("<Return>", lambda e: self._on_add())
        self.note_input.input.bind("<Return>", lambda e: self._on_add())
        self.date_input.input.bind("<Return>", lambda e: self._on_add())

    def _build_bill_section(self, parent):
        """Build the bill selection/creation logic."""
        self.bill_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.bill_frame.pack(fill="x", pady=(0, 20))
        
        bill_label = ctk.CTkLabel(
            self.bill_frame, text="Bill / Grouping (Optional)",
            font=FONTS["subheading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w"
        )
        bill_label.pack(fill="x", pady=(0, 8))

        # Bill Dropdown + "New" Button
        row = ctk.CTkFrame(self.bill_frame, fg_color="transparent")
        row.pack(fill="x")
        
        # Options: "None" + Bill Names + "Create New..."
        bill_names = ["None"] + [b["name"] for b in self.bills]
        self.bill_var = ctk.StringVar(value="None")
        
        self.bill_dropdown = ModernInput(
            row,
            label_text="Select existing bill",
            icon="📂",
            is_option_menu=True,
            options=bill_names,
            variable=self.bill_var,
            theme=self.theme
        )
        self.bill_dropdown.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # New Bill Toggle
        self.new_bill_btn = ctk.CTkButton(
            row, text="+ New", width=80, height=55,
            corner_radius=12,
            fg_color=self.theme.get("surface", "#12121a"),
            border_width=1, border_color=self.theme.get("border", "#2a2a3e"),
            text_color=self.theme.get("accent", "#6c5ce7"),
            hover_color=self.theme.get("card_hover", "#1f1f35"),
            font=FONTS["body_bold"],
            command=self._toggle_new_bill
        )
        self.new_bill_btn.pack(side="right", pady=(24, 0))

        # Inline New Bill Entry (hidden by default)
        self.new_bill_container = ctk.CTkFrame(self.bill_frame, fg_color="transparent")
        # will pack/unpack in toggle
        
        self.new_bill_var = ctk.StringVar()
        self.new_bill_input = ModernInput(
            self.new_bill_container,
            label_text="Enter new bill name",
            icon="📁",
            placeholder="e.g., Vacation 2026",
            variable=self.new_bill_var,
            theme=self.theme
        )
        self.new_bill_input.pack(fill="x", pady=(10, 0))

    def _toggle_new_bill(self):
        """Toggle the new bill entry field."""
        self.show_new_bill_input = not self.show_new_bill_input
        if self.show_new_bill_input:
            self.new_bill_container.pack(fill="x")
            self.new_bill_btn.configure(text="Cancel", text_color=self.theme.get("danger", "#ff7675"))
            self.bill_dropdown.input.configure(state="disabled")
        else:
            self.new_bill_container.pack_forget()
            self.new_bill_btn.configure(text="+ New", text_color=self.theme.get("accent", "#6c5ce7"))
            self.bill_dropdown.input.configure(state="normal")
            self.new_bill_var.set("")

    def _on_add(self):
        """Handle adding the expense."""
        # 1. Validate Basic Fields
        amount = Expense.validate_amount(self.amount_var.get())
        if amount is None:
            self._show_error("❌ Please enter a valid amount")
            return

        date = Expense.validate_date(self.date_var.get())
        if date is None:
            self._show_error("❌ Invalid date. Use YYYY-MM-DD")
            return

        cat_str = self.category_var.get()
        category = cat_str.split(" ", 1)[-1] if " " in cat_str else cat_str
        note = self.note_var.get().strip()

        # 2. Handle Bill Logic
        bill_id = None
        if self.show_new_bill_input:
            new_bill_name = self.new_bill_var.get().strip()
            if not new_bill_name:
                self._show_error("❌ Please enter a bill name or cancel")
                return
            # Create new bill
            bill_id = self.db.add_bill(new_bill_name)
        else:
            bill_sel = self.bill_var.get()
            if bill_sel != "None":
                # Find bill ID
                for b in self.bills:
                    if b["name"] == bill_sel:
                        bill_id = b["id"]
                        break

        # 3. Add to DB
        self.db.add_expense(amount, category, date, note, bill_id)

        # 4. Success UI
        self._show_success(f"✅ Added {CURRENCY_SYMBOL}{amount:,.2f} for {category}")
        
        # 5. Reset Form
        self.amount_var.set("")
        self.note_var.set("")
        self.date_var.set(datetime.now().strftime(DATE_FORMAT))
        self.amount_input.input.focus()

        if self.show_new_bill_input:
            self._toggle_new_bill() # Close new bill input
            
        # Reload bills for next entry
        self._load_data()
        
        # Update dropdown options
        bill_names = ["None"] + [b["name"] for b in self.bills]
        self.bill_dropdown.input.configure(values=bill_names)
        self.bill_var.set("None")

        if self.on_expense_added:
            self.on_expense_added()

    def _show_error(self, msg):
        self.message_label.configure(text=msg, text_color=self.theme.get("danger", "#ff7675"))
        self.after(4000, lambda: self.message_label.configure(text=""))

    def _show_success(self, msg):
        self.message_label.configure(text=msg, text_color=self.theme.get("success", "#00cec9"))
        self.after(4000, lambda: self.message_label.configure(text=""))

    def _build_budget_status(self, parent):
        """Build a compact budget usage indicator below the form."""
        budget_str = self.db.get_setting("monthly_budget", "0")
        budget = float(budget_str) if budget_str else 0
        if budget <= 0: return

        monthly_spent = self.db.get_monthly_total()
        pct = (monthly_spent / budget * 100) if budget > 0 else 0
        remaining = max(budget - monthly_spent, 0)

        bar_color = "#e17055" if pct >= 90 else "#fdcb6e" if pct >= 70 else "#00b894"

        budget_card = ctk.CTkFrame(
            parent, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=12, border_width=1, border_color=self.theme.get("border", "#2a2a3e"),
        )
        budget_card.pack(fill="x", padx=28, pady=(14, 16))

        inner = ctk.CTkFrame(budget_card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=14)

        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row, text="📋  Monthly Budget", font=FONTS["body_bold"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            title_row, text=f"{CURRENCY_SYMBOL}{monthly_spent:,.0f} / {CURRENCY_SYMBOL}{budget:,.0f} ({pct:.0f}%)",
            font=FONTS["small_bold"], text_color=bar_color, anchor="e",
        ).pack(side="right")

        bar_bg = ctk.CTkFrame(inner, fg_color=self.theme.get("input_bg", "#16162a"), corner_radius=6, height=10)
        bar_bg.pack(fill="x", pady=(8, 0))
        bar_bg.pack_propagate(False)

        fill_pct = min(pct, 100) / 100.0
        if fill_pct > 0:
            ctk.CTkFrame(bar_bg, fg_color=bar_color, corner_radius=6).place(relx=0, rely=0, relheight=1.0, relwidth=fill_pct)

        status_text = f"🚨 Over budget by {CURRENCY_SYMBOL}{monthly_spent - budget:,.2f}" if pct >= 100 else f"✅ {CURRENCY_SYMBOL}{remaining:,.2f} remaining"
        status_color = self.theme.get("danger", "#ff7675") if pct >= 100 else self.theme.get("success", "#00cec9") if pct < 70 else bar_color

        ctk.CTkLabel(inner, text=status_text, font=FONTS["small"], text_color=status_color, anchor="w").pack(fill="x", pady=(6, 0))

    def refresh(self, theme=None, **kwargs):
        if theme: self.theme = theme
        for widget in self.winfo_children(): widget.destroy()
        self._load_data()
        self._build_ui()
