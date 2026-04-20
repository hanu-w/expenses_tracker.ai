"""
Expense Tracker — Add Expense View
Modern fintech-style form to add a new expense.
Supports session-based bill grouping and custom user-defined categories.
"""

import customtkinter as ctk
from datetime import datetime
from config import CURRENCY_SYMBOL, DATE_FORMAT
from modules.theme import FONTS
from modules.models import Expense
from modules.ui.components import ModernInput, AddCategoryDialog
from modules import category_manager as cm


class AddExpenseView(ctk.CTkFrame):
    """Modern add expense form with validation, bill support, and custom categories."""

    def __init__(self, master, db, theme, on_expense_added=None,
                 active_project_id=None, active_project_name=None,
                 on_start_session=None, on_finish_session=None, **kwargs):
        self.db = db
        self.theme = theme
        self.on_expense_added = on_expense_added

        # Session State
        self.active_project_id = active_project_id
        self.active_project_name = active_project_name
        self.on_start_session = on_start_session
        self.on_finish_session = on_finish_session

        # Track last valid category selection (plain name)
        self._last_category = ""
        
        # Prevent double-click spam
        self.is_processing = False

        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    # ─── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        """Build the modernized form layout."""

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

        # ─── Main Form ───────────────────────────────────────
        form = ctk.CTkFrame(content, fg_color="transparent")
        form.pack(fill="x", padx=28, pady=16)

        # Amount
        self.amount_var = ctk.StringVar()
        self.amount_input = ModernInput(
            form,
            label_text="How much did you spend?",
            icon=CURRENCY_SYMBOL,
            placeholder="0.00",
            variable=self.amount_var,
            font=("Segoe UI", 32, "bold"),
            height=80,
            theme=self.theme,
        )
        self.amount_input.pack(fill="x", pady=(0, 24))

        # Section label
        ctk.CTkLabel(
            form, text="Transaction Details",
            font=FONTS["subheading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        # Category + Date row
        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 20))
        grid.columnconfigure((0, 1), weight=1, uniform="grp")

        self._build_category_selector(grid)

        self.date_var = ctk.StringVar(value=datetime.now().strftime(DATE_FORMAT))
        self.date_input = ModernInput(
            grid,
            label_text="Date",
            icon="📅",
            placeholder="YYYY-MM-DD",
            variable=self.date_var,
            theme=self.theme,
        )
        self.date_input.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Project session section
        self._build_project_section(form)

        # Note
        self.note_var = ctk.StringVar()
        self.note_input = ModernInput(
            form,
            label_text="Add a note",
            icon="🖋️",
            placeholder="e.g., Dinner with family",
            variable=self.note_var,
            theme=self.theme,
        )
        self.note_input.pack(fill="x", pady=(10, 20))

        # Message label (error / success)
        self.message_label = ctk.CTkLabel(
            form, text="", font=FONTS["body"],
            text_color=self.theme.get("danger", "#ff7675"),
            anchor="w",
        )
        self.message_label.pack(fill="x", pady=(0, 10))

        # Submit
        self.add_btn = ctk.CTkButton(
            form,
            text="Add Expense",
            font=FONTS["button"],
            fg_color=self.theme.get("accent", "#6c5ce7"),
            hover_color=self.theme.get("accent_hover", "#7d6ff0"),
            text_color="#ffffff",
            height=56,
            corner_radius=14,
            command=self.add_expense,
        )
        self.add_btn.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            content,
            text="Tip: Use Projects to group related expenses into folder-like buckets",
            font=FONTS["small"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
        ).pack(pady=(14, 0))

        self._build_budget_status(content)

        # Enter-key shortcuts
        self.amount_input.input.bind("<Return>", lambda e: self.add_expense())
        self.note_input.input.bind("<Return>", lambda e: self.add_expense())
        self.date_input.input.bind("<Return>", lambda e: self.add_expense())

    # ─── Category Selector ────────────────────────────────────────────────────

    def _build_category_selector(self, parent):
        """
        Category field with a live-updating colored circle indicator on the left.
        The dropdown includes a plain-name list plus the '+ Add Category' action.
        """
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            frame, text="Category",
            font=FONTS["small_bold"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            anchor="w",
        ).pack(fill="x", pady=(0, 6), padx=4)

        container = ctk.CTkFrame(
            frame, height=55, corner_radius=12,
            border_width=1,
            border_color=self.theme.get("input_border", "#2a2a40"),
            fg_color=self.theme.get("input_bg", "#16162a"),
        )
        container.pack(fill="x")
        container.pack_propagate(False)

        # ── Live colored-circle indicator (category initial) ──
        all_cats = cm.get_all_categories(self.db)
        first_cat = all_cats[0] if all_cats else "Food"
        first_color = cm.get_category_color(self.db, first_cat)
        CIRCLE = 26

        self.cat_indicator = ctk.CTkFrame(
            container, width=CIRCLE, height=CIRCLE,
            corner_radius=CIRCLE // 2,
            fg_color=first_color,
        )
        self.cat_indicator.pack(side="left", padx=(14, 0))
        self.cat_indicator.pack_propagate(False)

        self.cat_indicator_lbl = ctk.CTkLabel(
            self.cat_indicator,
            text=first_cat[0].upper(),
            font=("Segoe UI", 10, "bold"),
            text_color="#ffffff",
        )
        self.cat_indicator_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Separator
        ctk.CTkFrame(
            container, width=1,
            fg_color=self.theme.get("input_border", "#2a2a40"),
        ).pack(side="left", fill="y", pady=12, padx=(10, 0))

        # ── Dropdown ──────────────────────────────────────────
        options = cm.build_option_labels(self.db, include_add_option=True)
        self.category_var = ctk.StringVar(value=first_cat)
        self._last_category = first_cat

        input_bg = self.theme.get("input_bg", "#16162a")
        self.category_menu = ctk.CTkOptionMenu(
            container,
            values=options,
            variable=self.category_var,
            font=FONTS["body"],
            fg_color=input_bg,
            button_color=input_bg,
            button_hover_color=self.theme.get("card_hover", "#1f1f35"),
            dropdown_fg_color=self.theme.get("surface", "#12121a"),
            dropdown_hover_color=self.theme.get("card_hover", "#1f1f35"),
            dropdown_text_color=self.theme.get("text", "#f0f0f5"),
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w",
            dynamic_resizing=False,
            command=self._on_category_selected,
        )
        self.category_menu.pack(side="left", fill="both", expand=True, padx=(6, 10))

    def _on_category_selected(self, selected: str):
        """Called whenever the user picks an item from the category dropdown."""
        if selected == "\uff0b Add Category":
            # Immediately revert to previous then open dialog
            self.category_var.set(self._last_category)
            self._open_add_category_dialog()
        else:
            self._last_category = selected
            # Animate the indicator to the new category's color
            color = cm.get_category_color(self.db, selected)
            self.cat_indicator.configure(fg_color=color)
            self.cat_indicator_lbl.configure(
                text=selected[0].upper() if selected else "?"
            )

    def _open_add_category_dialog(self):
        """Open the AddCategoryDialog modal."""
        AddCategoryDialog(
            self,
            theme=self.theme,
            on_created=self._on_category_created,
        )

    def _on_category_created(self, name: str, icon: str, color: str):
        """Called when the user creates a new category via the dialog."""
        result = self.db.add_custom_category(name, icon, color)
        if result is None:
            self._show_error(f'Category "{name}" already exists')
            return

        # Rebuild options list and auto-select the new category
        new_options = cm.build_option_labels(self.db, include_add_option=True)
        self.category_menu.configure(values=new_options)
        self.category_var.set(name)
        self._last_category = name

        # Update the indicator circle
        self.cat_indicator.configure(fg_color=color)
        self.cat_indicator_lbl.configure(text=name[0].upper() if name else "?")

        self._show_success(f'Category "{name}" created!')

    # ─── Project / Session Section ───────────────────────────────────────────

    def _build_project_section(self, parent):
        """Build the session-based project grouping UI. Hidden if active because global header handles it."""
        if self.active_project_id:
            return  # The global app banner handles the active state visualization
            
        self.project_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.project_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            self.project_frame, text="Project / Grouping",
            font=FONTS["subheading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        self._build_normal_mode_ui()

    def _build_normal_mode_ui(self):
        container = ctk.CTkFrame(
            self.project_frame,
            fg_color=self.theme.get("surface", "#12121a"),
            corner_radius=12, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        container.pack(fill="x")
        inner = ctk.CTkFrame(container, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(
            inner, text="No active project session.",
            font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
        ).pack(side="left")
        ctk.CTkButton(
            inner, text="Start New Project",
            font=FONTS["small_bold"], width=140, height=36,
            fg_color=self.theme.get("accent", "#6c5ce7"),
            hover_color=self.theme.get("accent_hover", "#7d6ff0"),
            command=self._on_click_start_session,
        ).pack(side="right")

    def _on_click_start_session(self):
        dialog = ctk.CTkInputDialog(
            text="Enter Project Name (e.g., 'Trip to Bali'):", title="Start New Project"
        )
        name = dialog.get_input()
        if name and name.strip():
            if self.on_start_session:
                self.on_start_session(name.strip())

    # ─── Add Expense Logic ────────────────────────────────────────────────────

    def add_expense(self):
        """Validate and persist the expense with robust error handling."""
        if self.is_processing:
            return
            
        print("[DEBUG] 'Add Expense' button clicked")
        
        self.is_processing = True
        self.add_btn.configure(state="disabled")
        
        try:
            raw_amount = self.amount_var.get()
            category = self.category_var.get()
            raw_date = self.date_var.get()
            note = self.note_var.get().strip()
            
            print(f"[DEBUG] values of amount: {raw_amount}, category: {category}, date: {raw_date}, note: {note}")
            
            # Validation
            if not raw_amount:
                self._show_error("Amount cannot be empty.")
                return
                
            try:
                amount = float(raw_amount)
            except ValueError:
                self._show_error("Amount must be a numeric value.")
                return
                
            if amount <= 0:
                self._show_error("Amount must be greater than 0.")
                return

            date = Expense.validate_date(raw_date)
            if date is None:
                self._show_error("Invalid date. Please use YYYY-MM-DD.")
                return
                
            if not category or category == "\uff0b Add Category":
                self._show_error("Please select a valid category.")
                return

            project_id = self.active_project_id
            
            self.db.add_expense(float(amount), category, date, note, project_id)
            
            if project_id:
                self._show_success(f"Added to Project: {self.active_project_name}")
            else:
                self._show_success("Expense added successfully")

            # Reset form
            self.amount_var.set("")
            self.note_var.set("")
            self.date_var.set(datetime.now().strftime(DATE_FORMAT))
            self.amount_input.input.focus()

            if self.on_expense_added:
                self.on_expense_added()
                
        except Exception as e:
            print(f"[ERROR] Failed to add expense: {str(e)}")
            self._show_error(f"Internal error: {str(e)}")
        finally:
            self.is_processing = False
            self.add_btn.configure(state="normal")

    # ─── Budget Status ────────────────────────────────────────────────────────

    def _build_budget_status(self, parent):
        """Compact monthly budget progress bar below the form."""
        budget_str = self.db.get_setting("monthly_budget", "0")
        budget = float(budget_str) if budget_str else 0
        if budget <= 0:
            return

        monthly_spent = self.db.get_monthly_total()
        pct = (monthly_spent / budget * 100) if budget > 0 else 0
        remaining = max(budget - monthly_spent, 0)
        bar_color = "#e17055" if pct >= 90 else "#fdcb6e" if pct >= 70 else "#00b894"

        budget_card = ctk.CTkFrame(
            parent, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=12, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        budget_card.pack(fill="x", padx=28, pady=(14, 16))
        inner = ctk.CTkFrame(budget_card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=14)

        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(
            title_row, text="Monthly Budget", font=FONTS["body_bold"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            title_row,
            text=f"{CURRENCY_SYMBOL}{monthly_spent:,.0f} / {CURRENCY_SYMBOL}{budget:,.0f} ({pct:.0f}%)",
            font=FONTS["small_bold"], text_color=bar_color, anchor="e",
        ).pack(side="right")

        bar_bg = ctk.CTkFrame(
            inner, fg_color=self.theme.get("input_bg", "#16162a"),
            corner_radius=6, height=10,
        )
        bar_bg.pack(fill="x", pady=(8, 0))
        bar_bg.pack_propagate(False)
        fill_pct = min(pct, 100) / 100.0
        if fill_pct > 0:
            ctk.CTkFrame(bar_bg, fg_color=bar_color, corner_radius=6).place(
                relx=0, rely=0, relheight=1.0, relwidth=fill_pct
            )

        status_text = (
            f"Over budget by {CURRENCY_SYMBOL}{monthly_spent - budget:,.2f}" if pct >= 100
            else f"{CURRENCY_SYMBOL}{remaining:,.2f} remaining"
        )
        status_color = (
            self.theme.get("danger", "#ff7675") if pct >= 100
            else self.theme.get("success", "#00cec9") if pct < 70
            else bar_color
        )
        ctk.CTkLabel(
            inner, text=status_text, font=FONTS["small"],
            text_color=status_color, anchor="w",
        ).pack(fill="x", pady=(6, 0))

    # ─── Feedback helpers ─────────────────────────────────────────────────────

    def _show_error(self, msg):
        self.message_label.configure(
            text=f"❌ {msg}", text_color=self.theme.get("danger", "#ff7675")
        )
        self.after(4000, lambda: self.message_label.configure(text=""))

    def _show_success(self, msg):
        self.message_label.configure(
            text=f"✅ {msg}", text_color=self.theme.get("success", "#00cec9")
        )
        self.after(4000, lambda: self.message_label.configure(text=""))

    def refresh(self, theme=None, **kwargs):
        if theme:
            self.theme = theme
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
