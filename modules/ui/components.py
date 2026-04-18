"""
Expense Tracker — Reusable UI Components
Stat cards, expense cards, category badges, search bar, and more.
"""

import customtkinter as ctk
from config import CURRENCY_SYMBOL, CATEGORY_COLORS, CATEGORY_ICONS
from modules.theme import FONTS
from modules import category_manager as cm


class StatCard(ctk.CTkFrame):
    """A metric card showing a title, value, and optional icon/subtitle."""

    def __init__(self, master, title, value, icon="", accent_color="#6c5ce7",
                 subtitle="", theme=None, **kwargs):
        self.theme = theme or {}
        bg = self.theme.get("card", "#1a1a2e")

        super().__init__(master, fg_color=bg, corner_radius=16, **kwargs)

        self.configure(border_width=1, border_color=self.theme.get("border", "#2a2a3e"))

        # Inner padding frame — increased padding for breathing room
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        # Icon + Title row
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")

        if icon:
            icon_label = ctk.CTkLabel(
                top_row, text=icon, font=("Segoe UI", 24),
                text_color=accent_color
            )
            icon_label.pack(side="left", padx=(0, 10))

        title_label = ctk.CTkLabel(
            top_row, text=title, font=FONTS["small_bold"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            anchor="w"
        )
        title_label.pack(side="left")

        # Value
        self.value_label = ctk.CTkLabel(
            inner, text=str(value), font=FONTS["heading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w"
        )
        self.value_label.pack(fill="x", anchor="w", pady=(10, 0))

        # Subtitle
        if subtitle:
            sub_label = ctk.CTkLabel(
                inner, text=subtitle, font=FONTS["small"],
                text_color=self.theme.get("text_muted", "#808098"),
                anchor="w"
            )
            sub_label.pack(fill="x", anchor="w", pady=(4, 0))

        # Accent bar at top
        accent_bar = ctk.CTkFrame(self, fg_color=accent_color, height=3, corner_radius=2)
        accent_bar.place(relx=0.05, rely=0.0, relwidth=0.9)

    def update_value(self, value):
        """Update the displayed value."""
        self.value_label.configure(text=str(value))


class ExpenseCard(ctk.CTkFrame):
    """A single expense item card with category badge, amount, date, delete."""

    def __init__(self, master, expense_data, theme=None, on_delete=None, **kwargs):
        self.theme = theme or {}
        self.expense_data = expense_data
        self.on_delete = on_delete

        bg = self.theme.get("card", "#1a1a2e")
        hover_bg = self.theme.get("card_hover", "#1f1f35")

        super().__init__(master, fg_color=bg, corner_radius=12, **kwargs)
        self.configure(border_width=1, border_color=self.theme.get("border", "#2a2a3e"))

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=12)

        # Left side: category badge + note
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        category = expense_data.get("category", "Other")
        cat_color = CATEGORY_COLORS.get(category, "#778ca3")
        cat_icon = CATEGORY_ICONS.get(category, "📌")

        # Category row
        cat_row = ctk.CTkFrame(left, fg_color="transparent")
        cat_row.pack(fill="x", anchor="w")

        badge = CategoryBadge(cat_row, category=category, theme=self.theme)
        badge.pack(side="left")

        # Date
        date_str = expense_data.get("date", "")
        try:
            from datetime import datetime
            parsed = datetime.strptime(date_str, "%Y-%m-%d")
            display_date = parsed.strftime("%d %b %Y")
        except (ValueError, TypeError):
            display_date = date_str

        date_label = ctk.CTkLabel(
            cat_row, text=f"  •  {display_date}", font=FONTS["small"],
            text_color=self.theme.get("text_secondary", "#b0b0c0")
        )
        date_label.pack(side="left", padx=(8, 0))

        # Note
        note = expense_data.get("note", "")
        if note:
            note_label = ctk.CTkLabel(
                left, text=note,
                font=FONTS["body"],
                text_color=self.theme.get("text", "#f0f0f5"),
                anchor="w",
                justify="left",
                wraplength=500  # Allows wrapping for long notes
            )
            note_label.pack(fill="x", anchor="w", pady=(6, 0))

        # Right side: amount + delete
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        amount = expense_data.get("amount", 0)
        amount_label = ctk.CTkLabel(
            right, text=f"{CURRENCY_SYMBOL}{amount:,.2f}",
            font=FONTS["title"],
            text_color=self.theme.get("text", "#f0f0f5")
        )
        amount_label.pack(side="left", padx=(0, 14))

        if on_delete:
            del_btn = ctk.CTkButton(
                right, text="✕", width=34, height=34,
                font=("Segoe UI", 14, "bold"),
                fg_color=self.theme.get("danger_bg", "#2e0a0a"),
                text_color=self.theme.get("danger", "#ff7675"),
                hover_color=self.theme.get("danger", "#ff7675"),
                corner_radius=8,
                command=lambda: on_delete(expense_data.get("id")),
            )
            del_btn.pack(side="left")

        # Hover effect
        def on_enter(e):
            self.configure(fg_color=hover_bg)
        def on_leave(e):
            self.configure(fg_color=bg)

        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)


class CategoryBadge(ctk.CTkFrame):
    """
    Modern category badge: colored circle with initial letter + category name.
    Replaces the old emoji-based design with a clean, consistent visual indicator.
    """

    _CIRCLE = 24  # diameter in px

    def __init__(self, master, category, theme=None, db=None, **kwargs):
        self.theme = theme or {}

        # Resolve color (custom or built-in)
        if db is not None:
            cat_color = cm.get_category_color(db, category)
        else:
            cat_color = CATEGORY_COLORS.get(category, "#778ca3")

        # Pill background: very subtle tint of the category color
        pill_bg   = _blend_color(cat_color, self.theme.get("card", "#1a1a2e"), 0.11)
        pill_border = _blend_color(cat_color, "#000000", 0.35)

        super().__init__(
            master,
            fg_color=pill_bg,
            corner_radius=8,
            border_width=1,
            border_color=pill_border,
            **kwargs,
        )

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=(6, 12), pady=5)

        # ── Colored circle with initial letter ─────────────────
        circle = ctk.CTkFrame(
            inner,
            width=self._CIRCLE, height=self._CIRCLE,
            corner_radius=self._CIRCLE // 2,
            fg_color=cat_color,
        )
        circle.pack(side="left", padx=(0, 8))
        circle.pack_propagate(False)

        initial = category[0].upper() if category else "?"
        lbl = ctk.CTkLabel(
            circle, text=initial,
            font=("Segoe UI", 10, "bold"),
            text_color="#ffffff",
        )
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        # ── Category name ────────────────────────────────────
        ctk.CTkLabel(
            inner, text=category,
            font=FONTS["small_bold"],
            text_color=cat_color,
        ).pack(side="left")


def _blend_color(fg_hex, bg_hex, alpha):
    """Blend foreground color with background at given alpha (0-1). Returns 6-char hex."""
    fg = _hex_to_rgb(fg_hex)
    bg = _hex_to_rgb(bg_hex)
    r = int(fg[0] * alpha + bg[0] * (1 - alpha))
    g = int(fg[1] * alpha + bg[1] * (1 - alpha))
    b = int(fg[2] * alpha + bg[2] * (1 - alpha))
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(hex_color):
    """Convert hex color to (r, g, b) tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 8:
        hex_color = hex_color[:6]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class SearchBar(ctk.CTkFrame):
    """Search input with icon."""

    def __init__(self, master, placeholder="Search expenses...", on_search=None,
                 theme=None, **kwargs):
        self.theme = theme or {}

        super().__init__(master, fg_color="transparent", **kwargs)

        self.search_var = ctk.StringVar()
        self.on_search = on_search

        # Container
        container = ctk.CTkFrame(
            self, fg_color=self.theme.get("input_bg", "#16162a"),
            corner_radius=10,
            border_width=1,
            border_color=self.theme.get("input_border", "#2a2a40"),
        )
        container.pack(fill="x")

        icon = ctk.CTkLabel(container, text="🔍", font=("Segoe UI", 16))
        icon.pack(side="left", padx=(14, 6))

        self.entry = ctk.CTkEntry(
            container, textvariable=self.search_var,
            placeholder_text=placeholder,
            font=FONTS["body"],
            fg_color="transparent",
            border_width=0,
            text_color=self.theme.get("text", "#f0f0f5"),
            placeholder_text_color=self.theme.get("text_muted", "#808098"),
            height=40,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 14), pady=8)

        if on_search:
            self.search_var.trace_add("write", lambda *_: on_search(self.search_var.get()))

    def get_value(self):
        return self.search_var.get()

    def clear(self):
        self.search_var.set("")


class BudgetTrackerCard(ctk.CTkFrame):
    """Monthly budget tracker with progress bar, spent/remaining, and warning."""

    # Progress bar color thresholds
    COLOR_GREEN = "#00b894"
    COLOR_YELLOW = "#fdcb6e"
    COLOR_RED = "#e17055"

    def __init__(self, master, budget, spent, theme=None, **kwargs):
        self.theme = theme or {}
        self.budget = budget
        self.spent = spent
        self.remaining = max(budget - spent, 0)
        self.pct = (spent / budget * 100) if budget > 0 else 0

        bg = self.theme.get("card", "#1a1a2e")
        super().__init__(master, fg_color=bg, corner_radius=16, **kwargs)
        self.configure(border_width=1, border_color=self.theme.get("border", "#2a2a3e"))

        self._build_ui()

    def _get_bar_color(self):
        """Return progress bar color based on percentage."""
        if self.pct >= 90:
            return self.COLOR_RED
        elif self.pct >= 70:
            return self.COLOR_YELLOW
        return self.COLOR_GREEN

    def _get_status_info(self):
        """Return (icon, label, color) for the current budget status."""
        if self.pct >= 100:
            return ("🚨", "Over Budget!", self.theme.get("danger", "#ff7675"))
        elif self.pct >= 90:
            return ("⚠️", "Critical — Nearly Exhausted", self.theme.get("danger", "#ff7675"))
        elif self.pct >= 70:
            return ("⚡", "Caution — Approaching Limit", self.theme.get("warning", "#ffeaa7"))
        elif self.pct >= 50:
            return ("📊", "On Track", self.theme.get("success", "#00cec9"))
        return ("✅", "Well Under Budget", self.theme.get("success", "#00cec9"))

    def _build_ui(self):
        """Build the budget tracker card layout."""
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        # ─── Title Row ────────────────────────────────────────
        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row, text="📋  Monthly Budget",
            font=FONTS["title"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            title_row, text=f"{self.pct:.0f}%",
            font=FONTS["title"],
            text_color=self._get_bar_color(),
            anchor="e",
        ).pack(side="right")

        # ─── Progress Bar ────────────────────────────────────
        bar_frame = ctk.CTkFrame(inner, fg_color="transparent")
        bar_frame.pack(fill="x", pady=(14, 0))

        bar_bg = ctk.CTkFrame(
            bar_frame,
            fg_color=self.theme.get("input_bg", "#16162a"),
            corner_radius=8,
            height=18,
        )
        bar_bg.pack(fill="x")
        bar_bg.pack_propagate(False)

        # Filled portion
        fill_pct = min(self.pct, 100) / 100.0
        if fill_pct > 0:
            bar_fill = ctk.CTkFrame(
                bar_bg,
                fg_color=self._get_bar_color(),
                corner_radius=8,
            )
            bar_fill.place(relx=0, rely=0, relheight=1.0, relwidth=fill_pct)

        # ─── Stats Row ───────────────────────────────────────
        stats_row = ctk.CTkFrame(inner, fg_color="transparent")
        stats_row.pack(fill="x", pady=(16, 0))
        stats_row.columnconfigure((0, 1, 2), weight=1, uniform="budget_stat")

        # Spent
        spent_col = ctk.CTkFrame(stats_row, fg_color="transparent")
        spent_col.grid(row=0, column=0, sticky="nsw")

        ctk.CTkLabel(
            spent_col, text="Spent",
            font=FONTS["small"],
            text_color=self.theme.get("text_muted", "#808098"),
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            spent_col, text=f"{CURRENCY_SYMBOL}{self.spent:,.2f}",
            font=FONTS["body_bold"],
            text_color=self._get_bar_color(),
            anchor="w",
        ).pack(anchor="w")

        # Remaining
        remain_col = ctk.CTkFrame(stats_row, fg_color="transparent")
        remain_col.grid(row=0, column=1, sticky="ns")

        ctk.CTkLabel(
            remain_col, text="Remaining",
            font=FONTS["small"],
            text_color=self.theme.get("text_muted", "#808098"),
        ).pack()

        remain_color = self.theme.get("success", "#00cec9") if self.remaining > 0 else self.theme.get("danger", "#ff7675")
        ctk.CTkLabel(
            remain_col, text=f"{CURRENCY_SYMBOL}{self.remaining:,.2f}",
            font=FONTS["body_bold"],
            text_color=remain_color,
        ).pack()

        # Budget total
        budget_col = ctk.CTkFrame(stats_row, fg_color="transparent")
        budget_col.grid(row=0, column=2, sticky="nse")

        ctk.CTkLabel(
            budget_col, text="Budget",
            font=FONTS["small"],
            text_color=self.theme.get("text_muted", "#808098"),
            anchor="e",
        ).pack(anchor="e")

        ctk.CTkLabel(
            budget_col, text=f"{CURRENCY_SYMBOL}{self.budget:,.2f}",
            font=FONTS["body_bold"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="e",
        ).pack(anchor="e")

        # ─── Status Message ──────────────────────────────────
        icon, label, color = self._get_status_info()

        status_frame = ctk.CTkFrame(
            inner,
            fg_color=_blend_color(color, self.theme.get("card", "#1a1a2e"), 0.12),
            corner_radius=10,
        )
        status_frame.pack(fill="x", pady=(14, 0))

        ctk.CTkLabel(
            status_frame, text=f"{icon}  {label}",
            font=FONTS["body_bold"],
            text_color=color,
        ).pack(padx=16, pady=10)

        # ─── Over-budget warning ─────────────────────────────
        if self.pct >= 100:
            overspend = self.spent - self.budget
            warn_frame = ctk.CTkFrame(
                inner,
                fg_color=self.theme.get("danger_bg", "#2e0a0a"),
                corner_radius=10,
            )
            warn_frame.pack(fill="x", pady=(10, 0))

            ctk.CTkLabel(
                warn_frame,
                text=f"🚨  You've overspent by {CURRENCY_SYMBOL}{overspend:,.2f} this month!",
                font=FONTS["body_bold"],
                text_color=self.theme.get("danger", "#ff7675"),
            ).pack(padx=16, pady=10)

    def update_data(self, budget, spent):
        """Update budget data and rebuild the card."""
        self.budget = budget
        self.spent = spent
        self.remaining = max(budget - spent, 0)
        self.pct = (spent / budget * 100) if budget > 0 else 0

        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()


class ModernInput(ctk.CTkFrame):
    """
    A premium card-styled input field with a label above it, 
    an icon on the left, and a focus-state highlight.
    """

    def __init__(self, master, label_text, icon="📝", placeholder="", 
                 is_option_menu=False, options=None, variable=None, 
                 height=55, font=None, theme=None, **kwargs):
        self.theme = theme or {}
        super().__init__(master, fg_color="transparent", **kwargs)

        self.border_normal = self.theme.get("input_border", "#2a2a40")
        self.border_focus = self.theme.get("accent", "#6c5ce7")
        self.is_option_menu = is_option_menu

        # Label above
        ctk.CTkLabel(
            self, text=label_text, font=FONTS["small_bold"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            anchor="w"
        ).pack(fill="x", pady=(0, 6), padx=4)

        # Field Card Container
        self.container = ctk.CTkFrame(
            self, height=height, corner_radius=12,
            border_width=1, border_color=self.border_normal,
            fg_color=self.theme.get("input_bg", "#16162a"),
        )
        self.container.pack(fill="x")
        self.container.pack_propagate(False)

        # Icon
        self.icon_label = ctk.CTkLabel(
            self.container, text=icon, font=("Segoe UI", 18),
            width=50
        )
        self.icon_label.pack(side="left", padx=(5, 0))

        # Divider
        divider = ctk.CTkFrame(self.container, width=1, fg_color=self.border_normal)
        divider.pack(side="left", fill="y", pady=12)

        # Input Field
        if is_option_menu:
            input_bg = self.theme.get("input_bg", "#16162a")
            self.input = ctk.CTkOptionMenu(
                self.container,
                values=options or [],
                variable=variable,
                font=font or FONTS["body"],
                fg_color=input_bg,
                button_color=input_bg,
                button_hover_color=self.theme.get("card_hover", "#1f1f35"),
                dropdown_fg_color=self.theme.get("surface", "#12121a"),
                dropdown_hover_color=self.theme.get("card_hover", "#1f1f35"),
                dropdown_text_color=self.theme.get("text", "#f0f0f5"),
                text_color=self.theme.get("text", "#f0f0f5"),
                anchor="w",
                dynamic_resizing=False,
            )
            self.input.pack(side="left", fill="both", expand=True, padx=(5, 10))
        else:
            self.input = ctk.CTkEntry(
                self.container,
                textvariable=variable,
                placeholder_text=placeholder,
                font=font or FONTS["body"],
                fg_color="transparent",
                border_width=0,
                text_color=self.theme.get("text", "#f0f0f5"),
                placeholder_text_color=self.theme.get("text_muted", "#808098"),
            )
            self.input.pack(side="left", fill="both", expand=True, padx=(12, 12))

            # Bind focus events
            self.input.bind("<FocusIn>", lambda e: self._on_focus(True))
            self.input.bind("<FocusOut>", lambda e: self._on_focus(False))

    def _on_focus(self, focused):
        color = self.border_focus if focused else self.border_normal
        self.container.configure(border_color=color)

    def get(self):
        return self.input.get()

    def set(self, value):
        if self.is_option_menu:
            self.input.set(value)
        else:
            self.input.delete(0, "end")
            self.input.insert(0, value)


class BillGroupCard(ctk.CTkFrame):
    """
    Shows a grouping of expenses (a Bill) as a compact, interactive card.
    Clicking the card opens a detailed popup view.
    """

    def __init__(self, master, bill_data, theme=None, on_click=None, **kwargs):
        self.theme = theme or {}
        self.bill_data = bill_data
        self.on_click = on_click

        bg = self.theme.get("card", "#1a1a2e")
        self.hover_bg = self.theme.get("card_hover", "#1f1f35")
        
        super().__init__(master, fg_color=bg, corner_radius=16, cursor="hand2", **kwargs)
        self.configure(border_width=1, border_color=self.theme.get("border", "#2a2a3e"))

        self._build_ui()
        
        # Bind click events
        if on_click:
            self.bind("<Button-1>", lambda e: on_click(self.bill_data.get("id")))
            for child in self.winfo_children():
                self._bind_click_recursive(child)
        
        # Hover effects
        self.bind("<Enter>", lambda e: self.configure(fg_color=self.hover_bg))
        self.bind("<Leave>", lambda e: self.configure(fg_color=bg))

    def _bind_click_recursive(self, widget):
        widget.bind("<Button-1>", lambda e: self.on_click(self.bill_data.get("id")))
        for child in widget.winfo_children():
            self._bind_click_recursive(child)

    def _build_ui(self):
        # ─── Bill Content ────────────────────────────────────
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)

        # Left: Bill Icon + Name + Count
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(
            left, text="📂", font=("Segoe UI", 32),
        ).pack(side="left", padx=(0, 18))

        name_stack = ctk.CTkFrame(left, fg_color="transparent")
        name_stack.pack(side="left")

        ctk.CTkLabel(
            name_stack, text=self.bill_data.get("name", "Untitled Bill"),
            font=FONTS["title"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w"
        ).pack(anchor="w")

        # Get count (passed in bill_data now or calculated externally)
        # Assuming the summary query provides a count or we can add it
        count = self.bill_data.get("count", 0)
        ctk.CTkLabel(
            name_stack, text=f"{count} expenses grouped",
            font=FONTS["small"],
            text_color=self.theme.get("text_muted", "#808098"),
            anchor="w"
        ).pack(anchor="w")

        # Right: Total Amount
        total = self.bill_data.get("total", 0)
        ctk.CTkLabel(
            inner, text=f"{CURRENCY_SYMBOL}{total:,.2f}",
            font=FONTS["heading"],
            text_color=self.theme.get("accent", "#6c5ce7"),
            anchor="e"
        ).pack(side="right")


class BillDetailPopup(ctk.CTkToplevel):
    """
    A modal popup showing all individual expenses linked to a bill.
    """

    def __init__(self, master, bill_id, db, theme, on_delete_expense=None):
        super().__init__(master)
        self.db = db
        self.theme = theme
        self.bill_id = bill_id
        self.on_delete_expense = on_delete_expense
        
        # Window setup
        self.title("Bill Details")
        self.geometry("650x700")
        self.transient(master)  # Keep on top of parent
        self.grab_set()         # Modal
        self.configure(fg_color=self.theme.get("bg", "#0b0b10"))

        self._load_data()
        self._build_ui()

    def _load_data(self):
        """Fetch bill name and expenses."""
        # Find bill name in current bills
        bills = self.db.get_all_bills()
        self.bill_name = "Bill Details"
        for b in bills:
            if b["id"] == self.bill_id:
                self.bill_name = b["name"]
                break
        
        self.expenses = self.db.get_expenses_by_bill(self.bill_id)
        self.total = sum(e["amount"] for e in self.expenses)

    def _build_ui(self):
        # ─── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))

        icon_label = ctk.CTkLabel(header, text="📂", font=("Segoe UI", 48))
        icon_label.pack(side="left", padx=(0, 20))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="both")

        ctk.CTkLabel(
            title_frame, text=self.bill_name,
            font=FONTS["heading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, text=f"Total: {CURRENCY_SYMBOL}{self.total:,.2f}  •  {len(self.expenses)} items",
            font=FONTS["body_bold"],
            text_color=self.theme.get("accent", "#6c5ce7"),
            anchor="w"
        ).pack(anchor="w")

        # ─── Expense List ────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.theme.get("scrollbar", "#2a2a3e"),
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        if not self.expenses:
            ctk.CTkLabel(
                scroll, text="No expenses in this bill.",
                font=FONTS["body"], text_color=self.theme.get("text_muted", "#808098")
            ).pack(pady=40)
        else:
            for exp in self.expenses:
                card = ExpenseCard(
                    scroll, exp, theme=self.theme, 
                    on_delete=self._handle_delete
                )
                card.pack(fill="x", pady=6, padx=10)

        # ─── Footer ──────────────────────────────────────────
        close_btn = ctk.CTkButton(
            self, text="Close", 
            fg_color=self.theme.get("surface", "#12121a"),
            border_width=1, border_color=self.theme.get("border", "#2a2a3e"),
            text_color=self.theme.get("text", "#f0f0f5"),
            font=FONTS["button"],
            height=45,
            command=self.destroy
        )
        close_btn.pack(pady=(0, 30), padx=30, fill="x")

    def _handle_delete(self, expense_id):
        """Handle internal deletion and refresh."""
        if self.on_delete_expense:
            self.on_delete_expense(expense_id)
            # Refresh popup content
            self._load_data()
            for widget in self.winfo_children():
                widget.destroy()
            self._build_ui()


class EmptyState(ctk.CTkFrame):
    """A clean UI placeholder for empty data states."""

    def __init__(self, master, title="No data available", message="Start by adding your first expense!",
                 icon="📊", theme=None, action_text=None, action_command=None, **kwargs):
        self.theme = theme or {}
        super().__init__(master, fg_color="transparent", **kwargs)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(expand=True, pady=60)

        # Icon
        ctk.CTkLabel(
            inner, text=icon, font=("Segoe UI", 64),
        ).pack(pady=(0, 20))

        # Title
        ctk.CTkLabel(
            inner, text=title, font=FONTS["subheading"],
            text_color=self.theme.get("text", "#f0f0f5"),
        ).pack(pady=(0, 8))

        # Message
        ctk.CTkLabel(
            inner, text=message, font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            wraplength=400,
        ).pack(pady=(0, 24))

        # Optional action button
        if action_text and action_command:
            ctk.CTkButton(
                inner, text=action_text, command=action_command,
                font=FONTS["body_bold"], height=40, corner_radius=10,
                fg_color=self.theme.get("accent", "#6c5ce7"),
                hover_color=self.theme.get("accent_hover", "#7d6ff0"),
                text_color="#ffffff",
            ).pack()


# ─── Color palette & emoji set for the dialog ─────────────────────────────────

_DIALOG_COLORS = [
    "#e84393", "#00b4d8", "#f4a261", "#2dc653", "#e63946",
    "#7b2fff", "#ff9f1c", "#06d6a0", "#118ab2", "#ef476f",
    "#8338ec", "#fb5607", "#3a86ff", "#ffbe0b", "#ff006e",
    "#778ca3",
]

_EMOJI_OPTIONS = [
    "📌", "🏷️", "💡", "⭐", "🔥", "🎯", "🎁", "🛒", "🏠", "✈️",
    "🐾", "🎵", "📷", "🌙", "❤️", "💼", "🧾", "🍕", "☕", "🎓",
    "🏋️", "🌱", "🐶", "🚀", "💈", "🎉", "🧴", "🪴", "🔧", "🎭",
    "💰", "🎮", "🚌", "📱", "🏥", "🎨", "🍺", "🌍", "🧳", "🎤",
]


class AddCategoryDialog(ctk.CTkToplevel):
    """
    A premium modal dialog for creating a new custom category.
    Lets the user enter a name, pick an emoji icon, and pick a colour.
    Calls `on_created(name, icon, color)` on success.
    """

    def __init__(self, master, theme, on_created=None):
        super().__init__(master)
        self.theme = theme
        self.on_created = on_created

        # State
        self.selected_icon = ctk.StringVar(value="📌")
        self.selected_color = ctk.StringVar(value=_DIALOG_COLORS[0])
        self._icon_buttons: dict[str, ctk.CTkButton] = {}
        self._color_buttons: dict[str, ctk.CTkFrame] = {}

        # Window
        self.title("Add Custom Category")
        self.geometry("520x640")
        self.resizable(False, False)
        self.configure(fg_color=self.theme.get("bg", "#0b0b10"))
        self.transient(master)
        self.grab_set()
        self.after(50, self.lift)

        self._build_ui()

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.theme.get("scrollbar", "#2a2a3e"),
        )
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Header ─────────────────────────────────────────────
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(28, 4))

        ctk.CTkLabel(
            hdr, text="Create Category",
            font=FONTS["subheading"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w",
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="✕", width=36, height=36, corner_radius=8,
            fg_color=self.theme.get("surface", "#12121a"),
            hover_color=self.theme.get("danger", "#ff7675"),
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            font=FONTS["body_bold"],
            command=self.destroy,
        ).pack(side="right")

        # ── Preview banner ─────────────────────────────────────
        self.preview_frame = ctk.CTkFrame(
            scroll,
            fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=14,
            border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
            height=70,
        )
        self.preview_frame.pack(fill="x", padx=28, pady=(12, 0))
        self.preview_frame.pack_propagate(False)

        preview_inner = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        preview_inner.pack(fill="both", expand=True, padx=20)

        self.preview_icon_lbl = ctk.CTkLabel(
            preview_inner, text="📌",
            font=("Segoe UI", 26),
        )
        self.preview_icon_lbl.pack(side="left", padx=(0, 12))

        self.preview_name_lbl = ctk.CTkLabel(
            preview_inner, text="Category Name",
            font=FONTS["title"],
            text_color=self.theme.get("text_muted", "#808098"),
        )
        self.preview_name_lbl.pack(side="left")

        # ── Category name ──────────────────────────────────────
        ctk.CTkLabel(
            scroll, text="Category Name",
            font=FONTS["small_bold"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            anchor="w",
        ).pack(fill="x", padx=28, pady=(20, 6))

        name_container = ctk.CTkFrame(
            scroll,
            fg_color=self.theme.get("input_bg", "#16162a"),
            corner_radius=12,
            border_width=1,
            border_color=self.theme.get("input_border", "#2a2a40"),
            height=52,
        )
        name_container.pack(fill="x", padx=28)
        name_container.pack_propagate(False)

        self.name_var = ctk.StringVar()
        self.name_var.trace_add("write", self._on_name_change)

        name_entry = ctk.CTkEntry(
            name_container,
            textvariable=self.name_var,
            placeholder_text='e.g. "Gym", "Travel", "Pets"',
            font=FONTS["body"],
            fg_color="transparent",
            border_width=0,
            text_color=self.theme.get("text", "#f0f0f5"),
            placeholder_text_color=self.theme.get("text_muted", "#808098"),
        )
        name_entry.pack(fill="both", expand=True, padx=16, pady=8)
        name_entry.bind("<Return>", lambda e: self._on_confirm())
        name_entry.focus_after(self)

        self.name_error = ctk.CTkLabel(
            scroll, text="",
            font=FONTS["small"],
            text_color=self.theme.get("danger", "#ff7675"),
            anchor="w",
        )
        self.name_error.pack(fill="x", padx=28, pady=(4, 0))

        # ── Icon picker ────────────────────────────────────────
        ctk.CTkLabel(
            scroll, text="Choose Icon",
            font=FONTS["small_bold"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            anchor="w",
        ).pack(fill="x", padx=28, pady=(18, 8))

        icon_grid_container = ctk.CTkFrame(
            scroll,
            fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=12,
            border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        icon_grid_container.pack(fill="x", padx=28)

        icon_grid = ctk.CTkFrame(icon_grid_container, fg_color="transparent")
        icon_grid.pack(padx=10, pady=10)

        cols = 10
        for idx, emoji in enumerate(_EMOJI_OPTIONS):
            btn = ctk.CTkButton(
                icon_grid,
                text=emoji,
                width=38, height=38,
                font=("Segoe UI", 17),
                fg_color="transparent",
                hover_color=self.theme.get("card_hover", "#1f1f35"),
                corner_radius=8,
                command=lambda e=emoji: self._select_icon(e),
            )
            btn.grid(row=idx // cols, column=idx % cols, padx=2, pady=2)
            self._icon_buttons[emoji] = btn

        self._select_icon("📌")

        # ── Color picker ───────────────────────────────────────
        ctk.CTkLabel(
            scroll, text="Choose Color",
            font=FONTS["small_bold"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            anchor="w",
        ).pack(fill="x", padx=28, pady=(18, 8))

        color_outer = ctk.CTkFrame(
            scroll,
            fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=12,
            border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        color_outer.pack(fill="x", padx=28)

        color_grid = ctk.CTkFrame(color_outer, fg_color="transparent")
        color_grid.pack(padx=12, pady=12)

        for idx, color in enumerate(_DIALOG_COLORS):
            swatch = ctk.CTkFrame(
                color_grid,
                fg_color=color,
                width=30, height=30,
                corner_radius=15,
                cursor="hand2",
            )
            swatch.grid(row=idx // 8, column=idx % 8, padx=4, pady=4)
            swatch.bind("<Button-1>", lambda e, c=color: self._select_color(c))
            self._color_buttons[color] = swatch

        self._select_color(_DIALOG_COLORS[0])

        # ── Action buttons ─────────────────────────────────────
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=28, pady=(22, 28))

        ctk.CTkButton(
            btn_row, text="Cancel",
            font=FONTS["button"],
            fg_color=self.theme.get("surface", "#12121a"),
            border_width=1, border_color=self.theme.get("border", "#2a2a3e"),
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            hover_color=self.theme.get("card_hover", "#1f1f35"),
            height=48, corner_radius=12,
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="✓  Create Category",
            font=FONTS["button"],
            fg_color=self.theme.get("accent", "#6c5ce7"),
            hover_color=self.theme.get("accent_hover", "#7d6ff0"),
            text_color="#ffffff",
            height=48, corner_radius=12,
            command=self._on_confirm,
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

    # ── Interaction helpers ────────────────────────────────────────────────────

    def _select_icon(self, emoji: str):
        # Deselect previous
        old = self.selected_icon.get()
        if old in self._icon_buttons:
            self._icon_buttons[old].configure(
                fg_color="transparent",
                text_color=self.theme.get("text", "#f0f0f5"),
            )
        # Select new
        self.selected_icon.set(emoji)
        if emoji in self._icon_buttons:
            self._icon_buttons[emoji].configure(
                fg_color=self.theme.get("accent", "#6c5ce7"),
                text_color="#ffffff",
            )
        self.preview_icon_lbl.configure(text=emoji)

    def _select_color(self, color: str):
        old = self.selected_color.get()
        if old in self._color_buttons:
            self._color_buttons[old].configure(
                border_width=0,
            )
        self.selected_color.set(color)
        if color in self._color_buttons:
            self._color_buttons[color].configure(
                border_width=3,
                border_color="#ffffff",
            )

    def _on_name_change(self, *_):
        name = self.name_var.get().strip()
        if name:
            self.preview_name_lbl.configure(
                text=name,
                text_color=self.theme.get("text", "#f0f0f5"),
            )
        else:
            self.preview_name_lbl.configure(
                text="Category Name",
                text_color=self.theme.get("text_muted", "#808098"),
            )
        self.name_error.configure(text="")

    def _on_confirm(self):
        name = self.name_var.get().strip()
        if not name:
            self.name_error.configure(text="❌  Please enter a category name")
            return
        if len(name) > 30:
            self.name_error.configure(text="❌  Name must be 30 characters or less")
            return

        icon = self.selected_icon.get()
        color = self.selected_color.get()

        if self.on_created:
            self.on_created(name, icon, color)
        self.destroy()

