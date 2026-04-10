"""
Expense Tracker — Reusable UI Components
Stat cards, expense cards, category badges, search bar, and more.
"""

import customtkinter as ctk
from config import CURRENCY_SYMBOL, CATEGORY_COLORS, CATEGORY_ICONS
from modules.theme import FONTS


class StatCard(ctk.CTkFrame):
    """A metric card showing a title, value, and optional icon/subtitle."""

    def __init__(self, master, title, value, icon="", accent_color="#6c5ce7",
                 subtitle="", theme=None, **kwargs):
        self.theme = theme or {}
        bg = self.theme.get("card", "#1a1a2e")

        super().__init__(master, fg_color=bg, corner_radius=16, **kwargs)

        self.configure(border_width=1, border_color=self.theme.get("border", "#2a2a3e"))

        # Inner padding frame
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # Icon + Title row
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")

        if icon:
            icon_label = ctk.CTkLabel(
                top_row, text=icon, font=("Segoe UI", 22),
                text_color=accent_color
            )
            icon_label.pack(side="left", padx=(0, 8))

        title_label = ctk.CTkLabel(
            top_row, text=title, font=FONTS["small"],
            text_color=self.theme.get("text_secondary", "#8a8a9a"),
            anchor="w"
        )
        title_label.pack(side="left")

        # Value
        self.value_label = ctk.CTkLabel(
            inner, text=str(value), font=FONTS["heading"],
            text_color=self.theme.get("text", "#eaeaea"),
            anchor="w"
        )
        self.value_label.pack(fill="x", anchor="w", pady=(8, 0))

        # Subtitle
        if subtitle:
            sub_label = ctk.CTkLabel(
                inner, text=subtitle, font=FONTS["tiny"],
                text_color=self.theme.get("text_muted", "#5a5a6a"),
                anchor="w"
            )
            sub_label.pack(fill="x", anchor="w", pady=(2, 0))

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

        super().__init__(master, fg_color=bg, corner_radius=12, height=60, **kwargs)
        self.configure(border_width=1, border_color=self.theme.get("border", "#2a2a3e"))

        # Prevent shrinking
        self.pack_propagate(False)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=10)

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
            text_color=self.theme.get("text_muted", "#5a5a6a")
        )
        date_label.pack(side="left", padx=(6, 0))

        # Note
        note = expense_data.get("note", "")
        if note:
            note_label = ctk.CTkLabel(
                left, text=note[:50] + ("..." if len(note) > 50 else ""),
                font=FONTS["tiny"],
                text_color=self.theme.get("text_secondary", "#8a8a9a"),
                anchor="w"
            )
            note_label.pack(fill="x", anchor="w", pady=(2, 0))

        # Right side: amount + delete
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        amount = expense_data.get("amount", 0)
        amount_label = ctk.CTkLabel(
            right, text=f"{CURRENCY_SYMBOL}{amount:,.2f}",
            font=FONTS["title"],
            text_color=self.theme.get("text", "#eaeaea")
        )
        amount_label.pack(side="left", padx=(0, 12))

        if on_delete:
            del_btn = ctk.CTkButton(
                right, text="✕", width=32, height=32,
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
    """Colored pill badge showing category icon and name."""

    def __init__(self, master, category, theme=None, **kwargs):
        self.theme = theme or {}
        cat_color = CATEGORY_COLORS.get(category, "#778ca3")
        cat_icon = CATEGORY_ICONS.get(category, "📌")

        # Blend category color with dark background for a subtle badge bg
        badge_bg = _blend_color(cat_color, self.theme.get("card", "#1a1a2e"), 0.15)

        super().__init__(master, fg_color=badge_bg, corner_radius=8, **kwargs)

        label = ctk.CTkLabel(
            self, text=f"{cat_icon} {category}",
            font=FONTS["small_bold"],
            text_color=cat_color,
        )
        label.pack(padx=10, pady=3)


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

        icon = ctk.CTkLabel(container, text="🔍", font=("Segoe UI", 14))
        icon.pack(side="left", padx=(12, 4))

        self.entry = ctk.CTkEntry(
            container, textvariable=self.search_var,
            placeholder_text=placeholder,
            font=FONTS["body"],
            fg_color="transparent",
            border_width=0,
            text_color=self.theme.get("text", "#eaeaea"),
            placeholder_text_color=self.theme.get("text_muted", "#5a5a6a"),
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=6)

        if on_search:
            self.search_var.trace_add("write", lambda *_: on_search(self.search_var.get()))

    def get_value(self):
        return self.search_var.get()

    def clear(self):
        self.search_var.set("")
