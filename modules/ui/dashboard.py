"""
Expense Tracker — Dashboard View
Main overview screen with stat cards, mini charts, and recent expenses.
"""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("TkAgg")

from config import CURRENCY_SYMBOL, CATEGORY_COLORS
from modules.theme import FONTS, get_chart_style
from modules.ui.components import StatCard, ExpenseCard


class DashboardView(ctk.CTkFrame):
    """Dashboard view with financial overview."""

    def __init__(self, master, db, theme, app_mode="dark", **kwargs):
        self.db = db
        self.theme = theme
        self.app_mode = app_mode

        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        """Build the dashboard layout."""

        # ─── Scrollable container ────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.theme.get("scrollbar", "#2a2a3e"),
        )
        self.scroll.pack(fill="both", expand=True, padx=0, pady=0)

        content = self.scroll

        # ─── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))

        title = ctk.CTkLabel(
            header, text="Dashboard",
            font=FONTS["heading"],
            text_color=self.theme.get("text", "#eaeaea"),
            anchor="w"
        )
        title.pack(side="left")

        subtitle = ctk.CTkLabel(
            header, text="Your financial overview",
            font=FONTS["small"],
            text_color=self.theme.get("text_muted", "#5a5a6a"),
            anchor="w"
        )
        subtitle.pack(side="left", padx=(12, 0), pady=(8, 0))

        # ─── Stat Cards Row ─────────────────────────────────
        stats_frame = ctk.CTkFrame(content, fg_color="transparent")
        stats_frame.pack(fill="x", padx=24, pady=(16, 0))
        stats_frame.columnconfigure((0, 1, 2), weight=1, uniform="stat")

        total = self.db.get_total()
        weekly = self.db.get_weekly_total()
        monthly = self.db.get_monthly_total()

        self.card_total = StatCard(
            stats_frame,
            title="Total Expenses",
            value=f"{CURRENCY_SYMBOL}{total:,.2f}",
            icon="💰",
            accent_color="#a29bfe",
            subtitle="All time",
            theme=self.theme,
        )
        self.card_total.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_weekly = StatCard(
            stats_frame,
            title="This Week",
            value=f"{CURRENCY_SYMBOL}{weekly:,.2f}",
            icon="📅",
            accent_color="#00cec9",
            subtitle="Mon – Sun",
            theme=self.theme,
        )
        self.card_weekly.grid(row=0, column=1, sticky="nsew", padx=8)

        self.card_monthly = StatCard(
            stats_frame,
            title="This Month",
            value=f"{CURRENCY_SYMBOL}{monthly:,.2f}",
            icon="📆",
            accent_color="#6c5ce7",
            subtitle="Current month",
            theme=self.theme,
        )
        self.card_monthly.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        # ─── Budget Warning (if set) ─────────────────────────
        budget_str = self.db.get_setting("monthly_budget", "0")
        budget = float(budget_str) if budget_str else 0
        if budget > 0:
            pct = (monthly / budget) * 100 if budget > 0 else 0
            if pct >= 80:
                warn_color = self.theme["danger"] if pct >= 100 else self.theme["warning"]
                warn_bg = self.theme["danger_bg"] if pct >= 100 else self.theme["warning_bg"]
                warn_text = f"⚠️  Budget Alert: You've used {pct:.0f}% of your {CURRENCY_SYMBOL}{budget:,.0f} monthly budget!"

                warn_frame = ctk.CTkFrame(content, fg_color=warn_bg, corner_radius=12)
                warn_frame.pack(fill="x", padx=24, pady=(12, 0))
                ctk.CTkLabel(
                    warn_frame, text=warn_text, font=FONTS["body_bold"],
                    text_color=warn_color
                ).pack(padx=16, pady=10)

        # ─── Charts Row ─────────────────────────────────────
        charts_frame = ctk.CTkFrame(content, fg_color="transparent")
        charts_frame.pack(fill="x", padx=24, pady=(16, 0))
        charts_frame.columnconfigure((0, 1), weight=1, uniform="chart")

        # Pie Chart (Category breakdown)
        pie_card = ctk.CTkFrame(
            charts_frame, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            pie_card, text="Spending by Category", font=FONTS["title"],
            text_color=self.theme.get("text", "#eaeaea"), anchor="w"
        ).pack(fill="x", padx=16, pady=(12, 0))

        self._draw_pie_chart(pie_card)

        # Bar Chart (Monthly)
        bar_card = ctk.CTkFrame(
            charts_frame, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        bar_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            bar_card, text="Monthly Spending", font=FONTS["title"],
            text_color=self.theme.get("text", "#eaeaea"), anchor="w"
        ).pack(fill="x", padx=16, pady=(12, 0))

        self._draw_bar_chart(bar_card)

        # ─── Recent Expenses ─────────────────────────────────
        recent_header = ctk.CTkFrame(content, fg_color="transparent")
        recent_header.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            recent_header, text="Recent Expenses", font=FONTS["subheading"],
            text_color=self.theme.get("text", "#eaeaea"), anchor="w"
        ).pack(side="left")

        count = self.db.get_expense_count()
        ctk.CTkLabel(
            recent_header, text=f"{count} total",
            font=FONTS["small"],
            text_color=self.theme.get("text_muted", "#5a5a6a"),
        ).pack(side="right")

        recent = self.db.get_recent_expenses(5)
        if recent:
            for exp in recent:
                card = ExpenseCard(content, exp, theme=self.theme)
                card.pack(fill="x", padx=24, pady=3)
        else:
            empty = ctk.CTkLabel(
                content, text="No expenses yet. Click '➕ Add Expense' to get started!",
                font=FONTS["body"],
                text_color=self.theme.get("text_muted", "#5a5a6a"),
            )
            empty.pack(pady=30)

        # Bottom padding
        ctk.CTkFrame(content, fg_color="transparent", height=20).pack()

    def _draw_pie_chart(self, parent):
        """Draw a pie chart of category breakdown."""
        chart_style = get_chart_style(self.app_mode)
        matplotlib.rcParams.update(chart_style)

        breakdown = self.db.get_category_breakdown()

        fig = Figure(figsize=(4, 2.8), dpi=100)
        fig.patch.set_facecolor(self.theme.get("card", "#1a1a2e"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme.get("card", "#1a1a2e"))

        if breakdown:
            labels = [b["category"] for b in breakdown]
            sizes = [b["total"] for b in breakdown]
            colors = [CATEGORY_COLORS.get(cat, "#778ca3") for cat in labels]

            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors,
                autopct="%1.0f%%", startangle=90,
                textprops={"fontsize": 8, "color": self.theme.get("text", "#eaeaea")},
                pctdistance=0.78,
                wedgeprops={"linewidth": 2, "edgecolor": self.theme.get("card", "#1a1a2e")},
            )
            for t in autotexts:
                t.set_fontsize(7)
                t.set_color("#ffffff")
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    fontsize=12, color=self.theme.get("text_muted", "#5a5a6a"),
                    transform=ax.transAxes)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")

        fig.tight_layout(pad=0.5)
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 12))

    def _draw_bar_chart(self, parent):
        """Draw a bar chart of monthly spending."""
        chart_style = get_chart_style(self.app_mode)
        matplotlib.rcParams.update(chart_style)

        monthly = self.db.get_monthly_breakdown(6)

        fig = Figure(figsize=(4, 2.8), dpi=100)
        fig.patch.set_facecolor(self.theme.get("card", "#1a1a2e"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme.get("card", "#1a1a2e"))

        if monthly and any(m["total"] > 0 for m in monthly):
            months = [m["month"] for m in monthly]
            totals = [m["total"] for m in monthly]

            bars = ax.bar(months, totals, color="#6c5ce7", width=0.5, 
                         border_radius=4, edgecolor="none")

            # Add value labels on bars
            for bar, val in zip(bars, totals):
                if val > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2, bar.get_height() + max(totals) * 0.02,
                        f"{CURRENCY_SYMBOL}{val:,.0f}", ha="center", va="bottom",
                        fontsize=7, color=self.theme.get("text_secondary", "#8a8a9a"),
                    )

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(self.theme.get("chart_grid", "#1a1a2e"))
            ax.spines["bottom"].set_color(self.theme.get("chart_grid", "#1a1a2e"))
            ax.tick_params(axis="x", labelsize=7, rotation=15)
            ax.tick_params(axis="y", labelsize=7)
            ax.set_ylabel("")
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    fontsize=12, color=self.theme.get("text_muted", "#5a5a6a"),
                    transform=ax.transAxes)
            ax.axis("off")

        fig.tight_layout(pad=0.5)
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 12))

    def refresh(self, theme=None, app_mode=None):
        """Rebuild the dashboard with fresh data."""
        if theme:
            self.theme = theme
        if app_mode:
            self.app_mode = app_mode

        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
