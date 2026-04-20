"""
Expense Tracker — Dashboard View
Main overview screen with stat cards, weekly insights, warnings, suggestions,
mini charts, and recent expenses.
"""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("TkAgg")

from config import CURRENCY_SYMBOL, CATEGORY_COLORS
from modules.theme import FONTS, get_chart_style
from modules.ui.components import StatCard, ExpenseCard, BudgetTrackerCard, EmptyState
from modules import analytics


# ─── Colour helpers used inline ───────────────────────────────────────────────
def _blend(fg: str, bg: str, alpha: float) -> str:
    """Simple hex colour blending (alpha-compositing)."""
    def _h(c):
        c = c.lstrip("#")
        return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
    fr, fg_, fb = _h(fg)
    br, bg_, bb = _h(bg)
    r = int(fr * alpha + br * (1 - alpha))
    g = int(fg_ * alpha + bg_ * (1 - alpha))
    b = int(fb * alpha + bb * (1 - alpha))
    return f"#{r:02x}{g:02x}{b:02x}"


class DashboardView(ctk.CTkFrame):
    """Dashboard view with financial overview."""

    def __init__(self, master, db, theme, app_mode="dark", on_navigate=None, **kwargs):
        self.db          = db
        self.theme       = theme
        self.app_mode    = app_mode
        self.on_navigate = on_navigate
        self._data_fingerprint = None

        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        """Build the dashboard layout."""

        # ─── Scrollable container ────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.theme.get("scrollbar", "#2a2a3e"),
        )
        self.scroll.pack(fill="both", expand=True, padx=0, pady=0)

        content = self.scroll

        # ─── Data Check ──────────────────────────────────────
        total_count = self.db.get_expense_count()

        if total_count == 0:
            EmptyState(
                content,
                title="Your Dashboard is Empty",
                message="Track your first expense to see stats, charts, and financial insights here!",
                icon="📊",
                theme=self.theme,
                action_text="➕  Add Your First Expense",
                action_command=lambda: self.on_navigate("add_expense") if self.on_navigate else None
            ).pack(expand=True, fill="both", pady=100)
            return

        # ─── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 8))

        ctk.CTkLabel(
            header, text="Dashboard",
            font=FONTS["heading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="Your financial overview",
            font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
            anchor="w"
        ).pack(side="left", padx=(14, 0), pady=(6, 0))

        # ─── Stat Cards Row ──────────────────────────────────
        stats_frame = ctk.CTkFrame(content, fg_color="transparent")
        stats_frame.pack(fill="x", padx=28, pady=(16, 0))
        stats_frame.columnconfigure((0, 1, 2), weight=1, uniform="stat")

        total   = self.db.get_total()
        weekly  = self.db.get_weekly_total()
        monthly = self.db.get_monthly_total()

        StatCard(
            stats_frame, title="Total Expenses",
            value=f"{CURRENCY_SYMBOL}{total:,.2f}",
            icon="💰", accent_color="#a29bfe", subtitle="All time", theme=self.theme,
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        StatCard(
            stats_frame, title="This Week",
            value=f"{CURRENCY_SYMBOL}{weekly:,.2f}",
            icon="📅", accent_color="#00cec9", subtitle="Mon – Sun", theme=self.theme,
        ).grid(row=0, column=1, sticky="nsew", padx=10)

        StatCard(
            stats_frame, title="This Month",
            value=f"{CURRENCY_SYMBOL}{monthly:,.2f}",
            icon="📆", accent_color="#6c5ce7", subtitle="Current month", theme=self.theme,
        ).grid(row=0, column=2, sticky="nsew", padx=(10, 0))

        # ─── Budget Tracker ───────────────────────────────────
        budget_str = self.db.get_setting("monthly_budget", "0")
        budget     = float(budget_str) if budget_str else 0

        if budget > 0:
            BudgetTrackerCard(
                content, budget=budget, spent=monthly, theme=self.theme,
            ).pack(fill="x", padx=28, pady=(16, 0))
        else:
            hint_frame = ctk.CTkFrame(
                content,
                fg_color=self.theme.get("card", "#1a1a2e"),
                corner_radius=12,
                border_width=1,
                border_color=self.theme.get("border", "#2a2a3e"),
            )
            hint_frame.pack(fill="x", padx=28, pady=(16, 0))
            ctk.CTkLabel(
                hint_frame,
                text="💡  Set a monthly budget in Settings to track your spending progress",
                font=FONTS["body"],
                text_color=self.theme.get("text_secondary", "#b0b0c0"),
                anchor="w",
            ).pack(fill="x", padx=20, pady=14)

        # ═══════════════════════════════════════════════════════════════════════
        #   INSIGHTS PANEL  (placed ABOVE charts so user sees insights first)
        # ═══════════════════════════════════════════════════════════════════════

        # ─── Weekly Summary ─────────────────────────────────
        self._build_section_header(content, "📊  Weekly Summary", pady_top=28)
        self._build_weekly_summary(content)

        # ─── Warnings & Alerts ──────────────────────────────
        self._build_section_header(content, "🔔  Warnings & Alerts", pady_top=20)
        self._build_warnings(content, budget)

        # ─── Suggestions ────────────────────────────────────
        self._build_section_header(content, "💡  Suggestions", pady_top=20)
        self._build_suggestions(content, budget)

        # ═══════════════════════════════════════════════════════════════════════
        #   CHARTS
        # ═══════════════════════════════════════════════════════════════════════

        self._build_section_header(content, "📈  Spending Charts", pady_top=20)

        charts_frame = ctk.CTkFrame(content, fg_color="transparent")
        charts_frame.pack(fill="x", padx=28, pady=(10, 0))
        charts_frame.columnconfigure((0, 1), weight=1, uniform="chart")

        pie_card = ctk.CTkFrame(
            charts_frame, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(
            pie_card, text="Spending by Category", font=FONTS["title"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", padx=20, pady=(16, 0))
        self._draw_pie_chart(pie_card)

        bar_card = ctk.CTkFrame(
            charts_frame, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        bar_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(
            bar_card, text="Monthly Spending", font=FONTS["title"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", padx=20, pady=(16, 0))
        self._draw_bar_chart(bar_card)

        # ─── Recent Expenses ─────────────────────────────────
        recent_header = ctk.CTkFrame(content, fg_color="transparent")
        recent_header.pack(fill="x", padx=28, pady=(24, 10))

        ctk.CTkLabel(
            recent_header, text="Recent Expenses", font=FONTS["subheading"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(side="left")

        count = self.db.get_expense_count()
        ctk.CTkLabel(
            recent_header, text=f"{count} total",
            font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
        ).pack(side="right")

        recent = self.db.get_recent_expenses(5)
        if recent:
            for exp in recent:
                ExpenseCard(content, exp, theme=self.theme).pack(fill="x", padx=28, pady=4)
        else:
            ctk.CTkLabel(
                content, text="No expenses yet. Click '➕ Add Expense' to get started!",
                font=FONTS["body"],
                text_color=self.theme.get("text_secondary", "#b0b0c0"),
            ).pack(pady=36)

        ctk.CTkFrame(content, fg_color="transparent", height=24).pack()

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _build_section_header(self, parent, title: str, pady_top: int = 20):
        """Render a slim section heading row."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=(pady_top, 6))

        ctk.CTkLabel(
            row, text=title, font=FONTS["subheading"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(side="left")

        # Thin divider line
        line = ctk.CTkFrame(
            row, height=2, fg_color=self.theme.get("border", "#2a2a3e"), corner_radius=1
        )
        line.pack(side="left", fill="x", expand=True, padx=(14, 0), pady=(4, 0))

    def _card_frame(self, parent, accent: str = None) -> ctk.CTkFrame:
        """Return a styled card frame."""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=14,
            border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        if accent:
            # top accent bar
            bar = ctk.CTkFrame(card, fg_color=accent, height=3, corner_radius=2)
            bar.place(relx=0.03, rely=0.0, relwidth=0.94)
        return card

    # ─── Weekly Summary ──────────────────────────────────────────────────────

    def _build_weekly_summary(self, parent):
        """Four-cell summary grid for this week's key numbers."""
        summary = analytics.get_weekly_summary(self.db)

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=28)
        container.columnconfigure((0, 1, 2, 3), weight=1, uniform="ws")

        # ── Cell definitions ──
        cells = [
            self._ws_cell_total_week(container, summary),
            self._ws_cell_highest(container, summary),
            self._ws_cell_top_category(container, summary),
            self._ws_cell_comparison(container, summary),
        ]
        for i, cell in enumerate(cells):
            padx = (0, 10) if i == 0 else (10, 0) if i == len(cells) - 1 else 10
            cell.grid(row=0, column=i, sticky="nsew", padx=padx)

    def _ws_cell_total_week(self, parent, s) -> ctk.CTkFrame:
        """Card: Total spent this week."""
        card = self._card_frame(parent, accent="#00cec9")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            inner, text="💸  This Week", font=FONTS["small_bold"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"), anchor="w"
        ).pack(anchor="w")

        amt = s["this_week"]
        ctk.CTkLabel(
            inner, text=f"{CURRENCY_SYMBOL}{amt:,.2f}",
            font=FONTS["heading"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(anchor="w", pady=(6, 0))

        ctk.CTkLabel(
            inner, text="Total spent Mon – today",
            font=FONTS["tiny"],
            text_color=self.theme.get("text_muted", "#808098"), anchor="w"
        ).pack(anchor="w", pady=(2, 0))
        return card

    def _ws_cell_highest(self, parent, s) -> ctk.CTkFrame:
        """Card: Highest single expense this week."""
        card = self._card_frame(parent, accent="#fd79a8")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            inner, text="🏆  Biggest Expense", font=FONTS["small_bold"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"), anchor="w"
        ).pack(anchor="w")

        exp = s.get("highest_exp")
        if exp:
            ctk.CTkLabel(
                inner, text=f"{CURRENCY_SYMBOL}{exp['amount']:,.2f}",
                font=FONTS["heading"],
                text_color="#fd79a8", anchor="w"
            ).pack(anchor="w", pady=(6, 0))

            note_text = exp.get("note", "").strip() or exp.get("category", "")
            ctk.CTkLabel(
                inner, text=f"{exp.get('category', '')}  •  {note_text}",
                font=FONTS["tiny"],
                text_color=self.theme.get("text_muted", "#808098"),
                anchor="w", wraplength=160
            ).pack(anchor="w", pady=(2, 0))
        else:
            ctk.CTkLabel(
                inner, text="—",
                font=FONTS["heading"],
                text_color=self.theme.get("text_muted", "#808098"), anchor="w"
            ).pack(anchor="w", pady=(6, 0))
            ctk.CTkLabel(
                inner, text="No expenses yet this week",
                font=FONTS["tiny"],
                text_color=self.theme.get("text_muted", "#808098"), anchor="w"
            ).pack(anchor="w")
        return card

    def _ws_cell_top_category(self, parent, s) -> ctk.CTkFrame:
        """Card: Top spending category with percentage."""
        card = self._card_frame(parent, accent="#a29bfe")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            inner, text="🥇  Top Category", font=FONTS["small_bold"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"), anchor="w"
        ).pack(anchor="w")

        top = s.get("top_cat")
        if top:
            cat_color = CATEGORY_COLORS.get(top["category"], "#a29bfe")
            ctk.CTkLabel(
                inner, text=top["category"],
                font=FONTS["heading"],
                text_color=cat_color, anchor="w"
            ).pack(anchor="w", pady=(6, 0))

            ctk.CTkLabel(
                inner,
                text=f"{top['pct']:.0f}% of this week  •  {CURRENCY_SYMBOL}{top['total']:,.0f}",
                font=FONTS["tiny"],
                text_color=self.theme.get("text_muted", "#808098"), anchor="w"
            ).pack(anchor="w", pady=(2, 0))
        else:
            ctk.CTkLabel(
                inner, text="—",
                font=FONTS["heading"],
                text_color=self.theme.get("text_muted", "#808098"), anchor="w"
            ).pack(anchor="w", pady=(6, 0))
        return card

    def _ws_cell_comparison(self, parent, s) -> ctk.CTkFrame:
        """Card: Week-over-week comparison."""
        change = s["change_pct"]

        if change > 0:
            direction = "up"
            accent    = "#e17055"   # red-ish for increase
            arrow     = "↑"
            label     = f"{change:.0f}% more vs last week"
        elif change < 0:
            direction = "down"
            accent    = "#00b894"   # green for decrease
            arrow     = "↓"
            label     = f"{abs(change):.0f}% less vs last week"
        else:
            direction = "same"
            accent    = "#b2bec3"
            arrow     = "→"
            label     = "Same as last week"

        card = self._card_frame(parent, accent=accent)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            inner, text="📆  vs Last Week", font=FONTS["small_bold"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"), anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner, text=f"{arrow} {abs(change):.0f}%",
            font=FONTS["heading"],
            text_color=accent, anchor="w"
        ).pack(anchor="w", pady=(6, 0))

        ctk.CTkLabel(
            inner, text=label,
            font=FONTS["tiny"],
            text_color=self.theme.get("text_muted", "#808098"), anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        # Sub-row: this vs last
        sub = ctk.CTkFrame(inner, fg_color="transparent")
        sub.pack(anchor="w", pady=(8, 0), fill="x")

        sub_text = (
            f"This: {CURRENCY_SYMBOL}{s['this_week']:,.0f}  "
            f"Last: {CURRENCY_SYMBOL}{s['last_week']:,.0f}"
        )
        ctk.CTkLabel(
            sub, text=sub_text, font=FONTS["tiny"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"), anchor="w"
        ).pack(anchor="w")

        return card

    # ─── Warnings & Alerts ───────────────────────────────────────────────────

    def _build_warnings(self, parent, budget: float):
        """Render warning/alert banner cards."""
        items = analytics.get_warnings_alerts(self.db, budget)

        if not items:
            # All-clear banner
            ok = ctk.CTkFrame(
                parent,
                fg_color=_blend("#00b894", self.theme.get("card", "#1a1a2e"), 0.14),
                corner_radius=12,
            )
            ok.pack(fill="x", padx=28)
            ctk.CTkLabel(
                ok,
                text="✅  Everything looks good — no alerts at this time.",
                font=FONTS["body_bold"],
                text_color="#00b894",
                anchor="w",
            ).pack(padx=20, pady=12)
            return

        col_map = {
            "warning": ("#fdcb6e", self.theme.get("warning_bg", "#2e2a0a")),
            "alert":   ("#ff7675", self.theme.get("danger_bg",  "#2e0a0a")),
        }

        for item in items:
            text_color, bg_color = col_map.get(item["level"], ("#f0f0f5", "#1a1a2e"))
            banner = ctk.CTkFrame(
                parent,
                fg_color=bg_color,
                corner_radius=12,
                border_width=1,
                border_color=text_color,
            )
            banner.pack(fill="x", padx=28, pady=(0, 8))

            row = ctk.CTkFrame(banner, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=12)

            ctk.CTkLabel(
                row, text=item["icon"],
                font=("Segoe UI", 22),
                text_color=text_color,
            ).pack(side="left", padx=(0, 12))

            ctk.CTkLabel(
                row, text=item["message"],
                font=FONTS["body"],
                text_color=text_color,
                anchor="w", wraplength=900, justify="left",
            ).pack(side="left", fill="x", expand=True)

    # ─── Suggestions ─────────────────────────────────────────────────────────

    def _build_suggestions(self, parent, budget: float):
        """Render suggestion list cards."""
        items = analytics.get_suggestions(self.db, budget)

        suggestion_color = "#74b9ff"  # light blue

        for idx, text in enumerate(items):
            card = ctk.CTkFrame(
                parent,
                fg_color=_blend(suggestion_color, self.theme.get("card", "#1a1a2e"), 0.08),
                corner_radius=12,
                border_width=1,
                border_color=_blend(suggestion_color, "#000000", 0.30),
            )
            card.pack(fill="x", padx=28, pady=(0, 8))

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=12)

            # Numbered pill
            num_pill = ctk.CTkFrame(
                row,
                fg_color=suggestion_color,
                corner_radius=14,
                width=28, height=28,
            )
            num_pill.pack(side="left", padx=(0, 14))
            num_pill.pack_propagate(False)
            ctk.CTkLabel(
                num_pill, text=str(idx + 1),
                font=("Segoe UI", 11, "bold"),
                text_color="#0d1117",
            ).place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(
                row, text=text,
                font=FONTS["body"],
                text_color=self.theme.get("text", "#f0f0f5"),
                anchor="w", wraplength=900, justify="left",
            ).pack(side="left", fill="x", expand=True)

    # ─── Charts ──────────────────────────────────────────────────────────────

    def _draw_pie_chart(self, parent):
        """Draw a pie chart of category breakdown."""
        chart_style = get_chart_style(self.app_mode)
        matplotlib.rcParams.update(chart_style)

        breakdown = self.db.get_category_breakdown()
        if not breakdown:
            return

        fig = Figure(figsize=(4, 2.8), dpi=100)
        fig.patch.set_facecolor(self.theme.get("card", "#1a1a2e"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme.get("card", "#1a1a2e"))

        labels = [b["category"] for b in breakdown]
        sizes  = [b["total"]    for b in breakdown]
        colors = [CATEGORY_COLORS.get(cat, "#778ca3") for cat in labels]

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors,
            autopct="%1.0f%%", startangle=90,
            textprops={"fontsize": 9, "color": self.theme.get("text", "#f0f0f5")},
            pctdistance=0.78,
            wedgeprops={"linewidth": 2, "edgecolor": self.theme.get("card", "#1a1a2e")},
        )
        for t in autotexts:
            t.set_fontsize(8)
            t.set_color("#ffffff")

        fig.tight_layout(pad=0.5)
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(6, 16))

    def _draw_bar_chart(self, parent):
        """Draw a bar chart of monthly spending."""
        chart_style = get_chart_style(self.app_mode)
        matplotlib.rcParams.update(chart_style)

        monthly = self.db.get_monthly_breakdown(6)
        if not monthly or not any(m["total"] > 0 for m in monthly):
            return

        fig = Figure(figsize=(4, 2.8), dpi=100)
        fig.patch.set_facecolor(self.theme.get("card", "#1a1a2e"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme.get("card", "#1a1a2e"))

        months = [m["month"] for m in monthly]
        totals = [m["total"] for m in monthly]

        bars = ax.bar(months, totals, color="#6c5ce7", width=0.5, edgecolor="none")

        for bar, val in zip(bars, totals):
            if val > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height() + max(totals) * 0.02,
                    f"{CURRENCY_SYMBOL}{val:,.0f}", ha="center", va="bottom",
                    fontsize=8, color=self.theme.get("text_secondary", "#b0b0c0"),
                )

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(self.theme.get("chart_grid", "#1a1a2e"))
        ax.spines["bottom"].set_color(self.theme.get("chart_grid", "#1a1a2e"))
        ax.tick_params(axis="x", labelsize=8, rotation=15)
        ax.tick_params(axis="y", labelsize=8)
        ax.set_ylabel("")

        fig.tight_layout(pad=0.5)
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(6, 16))

    # ─── Refresh ─────────────────────────────────────────────────────────────

    def refresh(self, theme=None, app_mode=None):
        """Rebuild the dashboard with fresh data if it has changed."""
        if theme:
            self.theme = theme
        if app_mode:
            self.app_mode = app_mode

        new_fingerprint = (
            f"{self.db.get_expense_count()}_{self.db.get_total()}"
            f"_{self.db.get_weekly_total()}_{self.app_mode}"
        )
        if self._data_fingerprint == new_fingerprint:
            return  # No change, skip expensive redraw

        self._data_fingerprint = new_fingerprint
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
