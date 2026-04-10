"""
Expense Tracker — Charts View
Full-page charts: Pie (category), Bar (monthly), Line (weekly trend).
"""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("TkAgg")
import numpy as np

from config import CURRENCY_SYMBOL, CATEGORY_COLORS
from modules.theme import FONTS, get_chart_style


class ChartsView(ctk.CTkFrame):
    """Charts view with pie, bar, and line charts."""

    def __init__(self, master, db, theme, app_mode="dark", **kwargs):
        self.db = db
        self.theme = theme
        self.app_mode = app_mode

        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        """Build the charts layout."""
        chart_style = get_chart_style(self.app_mode)
        matplotlib.rcParams.update(chart_style)

        # ─── Scrollable container ────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.theme.get("scrollbar", "#2a2a3e"),
        )
        scroll.pack(fill="both", expand=True)
        content = scroll

        # ─── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            header, text="Charts & Analytics",
            font=FONTS["heading"],
            text_color=self.theme.get("text", "#eaeaea"),
            anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="Visual spending insights",
            font=FONTS["small"],
            text_color=self.theme.get("text_muted", "#5a5a6a"),
        ).pack(side="left", padx=(12, 0), pady=(8, 0))

        # ─── Top Row: Pie + Bar ──────────────────────────────
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x", padx=24, pady=(16, 0))
        top_row.columnconfigure((0, 1), weight=1, uniform="chart")

        # Pie Chart Card
        pie_card = ctk.CTkFrame(
            top_row, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            pie_card, text="📊  Spending by Category", font=FONTS["title"],
            text_color=self.theme.get("text", "#eaeaea"), anchor="w"
        ).pack(fill="x", padx=16, pady=(16, 0))

        self._draw_pie_chart(pie_card)

        # Bar Chart Card
        bar_card = ctk.CTkFrame(
            top_row, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        bar_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            bar_card, text="📊  Monthly Spending", font=FONTS["title"],
            text_color=self.theme.get("text", "#eaeaea"), anchor="w"
        ).pack(fill="x", padx=16, pady=(16, 0))

        self._draw_bar_chart(bar_card)

        # ─── Bottom: Line Chart (full width) ─────────────────
        line_card = ctk.CTkFrame(
            content, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        line_card.pack(fill="x", padx=24, pady=(16, 0))

        ctk.CTkLabel(
            line_card, text="📈  Weekly Spending Trend", font=FONTS["title"],
            text_color=self.theme.get("text", "#eaeaea"), anchor="w"
        ).pack(fill="x", padx=16, pady=(16, 0))

        self._draw_line_chart(line_card)

        # ─── Insights Section ────────────────────────────────
        insights_card = ctk.CTkFrame(
            content, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        insights_card.pack(fill="x", padx=24, pady=(16, 16))

        ctk.CTkLabel(
            insights_card, text="💡  Quick Insights", font=FONTS["title"],
            text_color=self.theme.get("text", "#eaeaea"), anchor="w"
        ).pack(fill="x", padx=16, pady=(16, 8))

        self._draw_insights(insights_card)

    def _draw_pie_chart(self, parent):
        """Draw category breakdown pie chart."""
        breakdown = self.db.get_category_breakdown()

        fig = Figure(figsize=(4.5, 3.5), dpi=100)
        fig.patch.set_facecolor(self.theme.get("card", "#1a1a2e"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme.get("card", "#1a1a2e"))

        if breakdown:
            labels = [b["category"] for b in breakdown]
            sizes = [b["total"] for b in breakdown]
            colors = [CATEGORY_COLORS.get(cat, "#778ca3") for cat in labels]

            wedges, texts, autotexts = ax.pie(
                sizes, labels=None, colors=colors,
                autopct="%1.1f%%", startangle=90,
                textprops={"fontsize": 9, "color": "#ffffff"},
                pctdistance=0.75,
                wedgeprops={"linewidth": 2.5, "edgecolor": self.theme.get("card", "#1a1a2e")},
            )

            # Legend
            legend_labels = [f"{cat} ({CURRENCY_SYMBOL}{val:,.0f})" for cat, val in zip(labels, sizes)]
            ax.legend(
                wedges, legend_labels,
                loc="center left", bbox_to_anchor=(1, 0.5),
                fontsize=8,
                frameon=False,
                labelcolor=self.theme.get("text_secondary", "#8a8a9a"),
            )
        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                    fontsize=14, color=self.theme.get("text_muted", "#5a5a6a"),
                    transform=ax.transAxes)
            ax.axis("off")

        fig.tight_layout(pad=1)
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 16))

    def _draw_bar_chart(self, parent):
        """Draw monthly spending bar chart."""
        monthly = self.db.get_monthly_breakdown(6)

        fig = Figure(figsize=(4.5, 3.5), dpi=100)
        fig.patch.set_facecolor(self.theme.get("card", "#1a1a2e"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme.get("card", "#1a1a2e"))

        if monthly and any(m["total"] > 0 for m in monthly):
            months = [m["month"] for m in monthly]
            totals = [m["total"] for m in monthly]

            # Gradient-like colors
            gradient = ["#6c5ce7", "#a29bfe", "#6c5ce7", "#a29bfe", "#6c5ce7", "#a29bfe"]
            bar_colors = gradient[:len(months)]

            bars = ax.bar(months, totals, color=bar_colors, width=0.55,
                         edgecolor="none", zorder=3)

            # Value labels
            for bar, val in zip(bars, totals):
                if val > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max(totals) * 0.03,
                        f"{CURRENCY_SYMBOL}{val:,.0f}",
                        ha="center", va="bottom",
                        fontsize=8, color=self.theme.get("text_secondary", "#8a8a9a"),
                        fontweight="bold",
                    )

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(self.theme.get("border", "#2a2a3e"))
            ax.spines["bottom"].set_color(self.theme.get("border", "#2a2a3e"))
            ax.tick_params(axis="x", labelsize=8, rotation=15)
            ax.tick_params(axis="y", labelsize=8)
            ax.grid(axis="y", alpha=0.15, color=self.theme.get("text_muted", "#5a5a6a"))
            ax.set_axisbelow(True)
        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                    fontsize=14, color=self.theme.get("text_muted", "#5a5a6a"),
                    transform=ax.transAxes)
            ax.axis("off")

        fig.tight_layout(pad=1)
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 16))

    def _draw_line_chart(self, parent):
        """Draw weekly trend line chart."""
        weekly = self.db.get_weekly_trend(8)

        fig = Figure(figsize=(10, 3.2), dpi=100)
        fig.patch.set_facecolor(self.theme.get("card", "#1a1a2e"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme.get("card", "#1a1a2e"))

        if weekly and any(w["total"] > 0 for w in weekly):
            weeks = [w["week"] for w in weekly]
            totals = [w["total"] for w in weekly]

            x = range(len(weeks))

            # Line
            ax.plot(x, totals, color="#6c5ce7", linewidth=2.5, marker="o",
                   markersize=7, markerfacecolor="#a29bfe", markeredgecolor="#6c5ce7",
                   markeredgewidth=2, zorder=5)

            # Area fill
            ax.fill_between(x, totals, alpha=0.15, color="#6c5ce7")

            # Value labels
            for xi, val in zip(x, totals):
                if val > 0:
                    ax.annotate(
                        f"{CURRENCY_SYMBOL}{val:,.0f}",
                        (xi, val), textcoords="offset points",
                        xytext=(0, 14), ha="center",
                        fontsize=8, color=self.theme.get("text_secondary", "#8a8a9a"),
                        fontweight="bold",
                    )

            ax.set_xticks(list(x))
            ax.set_xticklabels(weeks, fontsize=9)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(self.theme.get("border", "#2a2a3e"))
            ax.spines["bottom"].set_color(self.theme.get("border", "#2a2a3e"))
            ax.grid(axis="y", alpha=0.15, color=self.theme.get("text_muted", "#5a5a6a"))
            ax.set_axisbelow(True)
        else:
            ax.text(0.5, 0.5, "No data yet — add some expenses to see trends",
                    ha="center", va="center",
                    fontsize=14, color=self.theme.get("text_muted", "#5a5a6a"),
                    transform=ax.transAxes)
            ax.axis("off")

        fig.tight_layout(pad=1)
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 16))

    def _draw_insights(self, parent):
        """Generate and display quick insights."""
        from modules.analytics import get_insights

        insights = get_insights(self.db)

        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(0, 16))

        if insights:
            for insight in insights:
                row = ctk.CTkFrame(inner, fg_color="transparent")
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(
                    row, text=insight, font=FONTS["body"],
                    text_color=self.theme.get("text_secondary", "#8a8a9a"),
                    anchor="w"
                ).pack(fill="x")
        else:
            ctk.CTkLabel(
                inner, text="Add more expenses to see personalized insights!",
                font=FONTS["body"],
                text_color=self.theme.get("text_muted", "#5a5a6a"),
            ).pack(pady=8)

    def refresh(self, theme=None, app_mode=None):
        """Rebuild charts with fresh data."""
        if theme:
            self.theme = theme
        if app_mode:
            self.app_mode = app_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
