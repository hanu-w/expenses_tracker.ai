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
from modules.ui.components import EmptyState


class ChartsView(ctk.CTkFrame):
    """Charts view with pie, bar, and line charts."""

    def __init__(self, master, db, theme, app_mode="dark", on_navigate=None, **kwargs):
        self.db = db
        self.theme = theme
        self.app_mode = app_mode
        self.on_navigate = on_navigate
        self._data_fingerprint = None

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

        # ─── Data Check ──────────────────────────────────────
        total_count = self.db.get_expense_count()

        if total_count == 0:
            EmptyState(
                content,
                title="No Insights Yet",
                message="Visual analytics and spending trends will appear here once you've added some expenses.",
                icon="📈",
                theme=self.theme,
                action_text="➕  Add Expense",
                action_command=lambda: self.on_navigate("add_expense") if self.on_navigate else None
            ).pack(expand=True, fill="both", pady=100)
            return

        # ─── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 8))

        ctk.CTkLabel(
            header, text="Charts & Analytics",
            font=FONTS["heading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="Visual spending insights",
            font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"),
        ).pack(side="left", padx=(14, 0), pady=(6, 0))

        # ─── Top Row: Pie + Bar ──────────────────────────────
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x", padx=28, pady=(20, 0))
        top_row.columnconfigure((0, 1), weight=1, uniform="chart")

        # Pie Chart Card
        pie_card = ctk.CTkFrame(
            top_row, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            pie_card, text="📊  Spending by Category", font=FONTS["title"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", padx=20, pady=(20, 0))

        self._draw_pie_chart(pie_card)

        # Bar Chart Card
        bar_card = ctk.CTkFrame(
            top_row, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        bar_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(
            bar_card, text="📊  Monthly Spending", font=FONTS["title"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", padx=20, pady=(20, 0))

        self._draw_bar_chart(bar_card)

        # ─── Bottom: Line Chart (full width) ─────────────────
        line_card = ctk.CTkFrame(
            content, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        line_card.pack(fill="x", padx=28, pady=(20, 0))

        ctk.CTkLabel(
            line_card, text="📈  Weekly Spending Trend", font=FONTS["title"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", padx=20, pady=(20, 0))

        self._draw_line_chart(line_card)

        # ─── Insights Section ────────────────────────────────
        insights_card = ctk.CTkFrame(
            content, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        insights_card.pack(fill="x", padx=28, pady=(20, 20))

        ctk.CTkLabel(
            insights_card, text="💡  Quick Insights", font=FONTS["title"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", padx=20, pady=(20, 10))

        self._draw_insights(insights_card)

    def _draw_pie_chart(self, parent):
        """Draw category breakdown pie chart with insight and tooltips."""
        breakdown = self.db.get_category_breakdown()
        if not breakdown:
            return

        fig = Figure(figsize=(4.5, 3.5), dpi=100)
        fig.patch.set_facecolor(self.theme.get("card", "#1a1a2e"))
        # Adjust subplot to make room for top label and clean layout
        ax = fig.add_subplot(111, position=[0.05, 0.1, 0.5, 0.75])
        ax.set_facecolor(self.theme.get("card", "#1a1a2e"))

        if breakdown:
            labels = [b["category"] for b in breakdown]
            sizes = [b["total"] for b in breakdown]
            colors = [CATEGORY_COLORS.get(cat, "#778ca3") for cat in labels]
            total_sum = sum(sizes)

            # --- HIGHLIGHT TOP CATEGORY ---
            max_idx = np.argmax(sizes)
            # Soft explode
            explode_arr = [0.06 if i == max_idx else 0 for i in range(len(sizes))]
            
            top_cat = labels[max_idx]
            top_pct = (sizes[max_idx] / total_sum) * 100 if total_sum > 0 else 0
            
            # Premium Title
            ax.set_title(f"Highest: {top_cat} ({top_pct:.1f}%)", fontsize=12, 
                         color=self.theme.get("text", "#f0f0f5"), fontweight="bold", pad=20)

            wedges, texts, autotexts = ax.pie(
                sizes, labels=None, colors=colors,
                autopct="%1.0f%%", startangle=90, explode=explode_arr,
                textprops={"fontsize": 10, "color": "#ffffff", "fontweight": "bold"},
                pctdistance=0.75,
                wedgeprops={"linewidth": 3, "edgecolor": self.theme.get("card", "#1a1a2e")},
            )

            # Legend
            legend_labels = [f"{cat} ({CURRENCY_SYMBOL}{val:,.0f})" for cat, val in zip(labels, sizes)]
            ax.legend(
                wedges, legend_labels,
                loc="center left", bbox_to_anchor=(1.1, 0.5),
                fontsize=10,
                frameon=False,
                labelcolor=self.theme.get("text_secondary", "#b0b0c0"),
            )

            # --- TOOLTIPS ---
            annot = ax.annotate("", xy=(0,0), xytext=(15, 15), textcoords="offset points",
                                bbox=dict(boxstyle="round,pad=0.6", fc=self.theme.get("surface", "#12121a"), 
                                          ec=self.theme.get("border", "#2a2a3e"), lw=1.5, alpha=0.95),
                                color=self.theme.get("text", "#f0f0f5"), fontsize=10, fontweight="bold", zorder=20)
            annot.set_visible(False)

            def hover(event):
                if event.inaxes == ax:
                    for i, wedge in enumerate(wedges):
                        cont, _ = wedge.contains(event)
                        if cont:
                            annot.xy = (event.xdata, event.ydata)
                            pct = (sizes[i] / total_sum) * 100 if total_sum else 0
                            annot.set_text(f"{labels[i]}\n{CURRENCY_SYMBOL}{sizes[i]:,.2f} ({pct:.1f}%)")
                            if not annot.get_visible():
                                annot.set_visible(True)
                            fig.canvas.draw_idle()
                            return
                if annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

            fig.tight_layout(pad=1.5)
            fig.canvas.mpl_connect("motion_notify_event", hover)

        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                    fontsize=14, color=self.theme.get("text_secondary", "#b0b0c0"),
                    transform=ax.transAxes)
            ax.axis("off")
            fig.tight_layout(pad=1.5)

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(6, 20))

    def _draw_bar_chart(self, parent):
        """Draw monthly spending bar chart with premium context and stable tooltips."""
        monthly = self.db.get_monthly_breakdown(6)
        if not monthly or not any(m["total"] > 0 for m in monthly):
            return

        fig = Figure(figsize=(4.5, 3.5), dpi=100)
        fig.patch.set_facecolor(self.theme.get("card", "#1a1a2e"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme.get("card", "#1a1a2e"))

        if monthly and any(m["total"] > 0 for m in monthly):
            months = [m["month"] for m in monthly]
            totals = [m["total"] for m in monthly]

            # Highlight logic
            max_idx = np.argmax(totals)
            base_color = self.theme.get("surface", "#12121a")
            accent_color = self.theme.get("accent", "#6c5ce7")
            
            # Soften base bars
            bar_colors = [accent_color if i == max_idx else base_color for i in range(len(months))]
            bar_ec = [self.theme.get("border", "#2a2a3e") if i != max_idx else accent_color for i in range(len(months))]

            bars = ax.bar(months, totals, color=bar_colors, edgecolor=bar_ec, linewidth=1.5, width=0.6, zorder=3)

            # Value labels & peak annotation
            max_val = max(totals)
            for i, (bar, val) in enumerate(zip(bars, totals)):
                if val > 0:
                    text_color = self.theme.get("text", "#f0f0f5") if i == max_idx else self.theme.get("text_secondary", "#b0b0c0")
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max_val * 0.02,
                        f"{val:,.0f}",
                        ha="center", va="bottom",
                        fontsize=9, color=text_color,
                        fontweight="bold" if i == max_idx else "normal",
                    )
                    
                    if i == max_idx:
                        ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + max_val * 0.12,
                            "Peak",
                            ha="center", va="bottom",
                            fontsize=10, color=accent_color,
                            fontweight="bold",
                        )

            # Accommodate premium padding
            ax.set_ylim(0, max_val * 1.3)

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(self.theme.get("border", "#2a2a3e"))
            ax.spines["bottom"].set_color(self.theme.get("border", "#2a2a3e"))
            ax.tick_params(axis="x", labelsize=10, pad=8, rotation=0, colors=self.theme.get("text", "#f0f0f5"))
            ax.tick_params(axis="y", labelsize=9, colors=self.theme.get("text_secondary", "#b0b0c0"))
            ax.grid(axis="y", alpha=0.08, color=self.theme.get("text_muted", "#808098"))
            ax.set_axisbelow(True)
            
            # --- TOOLTIPS ---
            annot = ax.annotate("", xy=(0,0), xytext=(0, 15), textcoords="offset points",
                                bbox=dict(boxstyle="round,pad=0.6", fc=self.theme.get("surface", "#12121a"), 
                                          ec=self.theme.get("border", "#2a2a3e"), lw=1.5, alpha=0.95),
                                color=self.theme.get("text", "#f0f0f5"), fontsize=10, fontweight="bold", zorder=20, ha="center")
            annot.set_visible(False)

            def hover(event):
                if event.inaxes == ax:
                    for i, bar in enumerate(bars):
                        cont, _ = bar.contains(event)
                        if cont:
                            annot.xy = (bar.get_x() + bar.get_width() / 2, bar.get_height())
                            annot.set_text(f"{months[i]}\n{CURRENCY_SYMBOL}{totals[i]:,.2f}")
                            if not annot.get_visible():
                                annot.set_visible(True)
                            fig.canvas.draw_idle()
                            return
                if annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

            fig.tight_layout(pad=1.5)
            fig.canvas.mpl_connect("motion_notify_event", hover)

        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                    fontsize=14, color=self.theme.get("text_secondary", "#b0b0c0"),
                    transform=ax.transAxes)
            ax.axis("off")
            fig.tight_layout(pad=1.5)

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(6, 20))

    def _draw_line_chart(self, parent):
        """Draw weekly trend line chart with stable tooltips and premium path."""
        weekly = self.db.get_weekly_trend(8)
        if not weekly or not any(w["total"] > 0 for w in weekly):
            return

        fig = Figure(figsize=(10, 3.5), dpi=100)
        fig.patch.set_facecolor(self.theme.get("card", "#1a1a2e"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme.get("card", "#1a1a2e"))

        if weekly and any(w["total"] > 0 for w in weekly):
            weeks = [w["week"] for w in weekly]
            totals = [w["total"] for w in weekly]

            x = list(range(len(weeks)))

            # --- TREND DETECTION ---
            if len(totals) >= 2:
                z = np.polyfit(x, totals, 1)
                slope = z[0]
                if slope > max(totals) * 0.05:
                    trend_text = "Increasing 📈"
                    trend_color = self.theme.get("error", "#ff7675")
                elif slope < -max(totals) * 0.05:
                    trend_text = "Decreasing 📉"
                    trend_color = self.theme.get("success", "#00cec9")
                else:
                    trend_text = "Stable 📊"
                    trend_color = self.theme.get("text_secondary", "#b0b0c0")
                
                ax.set_title(f"Recent Trend: {trend_text}", fontsize=12, 
                             color=trend_color, fontweight="bold", pad=20)

            # Premium Line — clip_on=False prevents edge markers from being cut
            line, = ax.plot(x, totals, color="#6c5ce7", linewidth=3.5, marker="o",
                   markersize=10, markerfacecolor=self.theme.get("card", "#1a1a2e"), markeredgecolor="#6c5ce7",
                   markeredgewidth=2.5, solid_capstyle='round', solid_joinstyle='round',
                   zorder=5, clip_on=False)

            # Area fill
            ax.fill_between(x, totals, alpha=0.1, color="#6c5ce7")

            # Horizontal margins so first/last points aren't cut at edges
            ax.margins(x=0.08)

            ax.set_xticks(x)
            ax.set_xticklabels(weeks, fontsize=10, color=self.theme.get("text", "#f0f0f5"))
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(self.theme.get("border", "#2a2a3e"))
            ax.spines["bottom"].set_color(self.theme.get("border", "#2a2a3e"))
            ax.tick_params(axis="x", pad=8)
            ax.tick_params(axis="y", labelsize=10, colors=self.theme.get("text_secondary", "#b0b0c0"))
            ax.grid(axis="y", alpha=0.08, color=self.theme.get("text_muted", "#808098"))
            ax.set_axisbelow(True)
            
            # Dynamic y-axis with breathing room
            m_val = max(totals)
            ax.set_ylim(0, m_val * 1.2)
            
            # --- TOOLTIPS ---
            annot = ax.annotate("", xy=(0,0), xytext=(0, 20), textcoords="offset points",
                                bbox=dict(boxstyle="round,pad=0.6", fc=self.theme.get("surface", "#12121a"), 
                                          ec=self.theme.get("border", "#2a2a3e"), lw=1.5, alpha=0.95),
                                color=self.theme.get("text", "#f0f0f5"), fontsize=10, fontweight="bold", zorder=20, ha="center")
            annot.set_visible(False)

            def hover(event):
                if event.inaxes == ax:
                    distances = [((event.xdata - xi)**2 + ((event.ydata - yi) / (m_val * 1.2) * len(x))**2) for xi, yi in zip(x, totals)]
                    if distances:
                        min_idx = np.argmin(distances)
                        if distances[min_idx] < 0.2:
                            annot.xy = (x[min_idx], totals[min_idx])
                            annot.set_text(f"{weeks[min_idx]}\n{CURRENCY_SYMBOL}{totals[min_idx]:,.2f}")
                            if not annot.get_visible():
                                annot.set_visible(True)
                            fig.canvas.draw_idle()
                            return
                if annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

            # Explicit margins instead of tight_layout to prevent clipping
            fig.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.15)
            fig.canvas.mpl_connect("motion_notify_event", hover)

        else:
            ax.text(0.5, 0.5, "No data yet — add some expenses to see trends",
                    ha="center", va="center",
                    fontsize=14, color=self.theme.get("text_secondary", "#b0b0c0"),
                    transform=ax.transAxes)
            ax.axis("off")
            fig.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.15)

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(6, 20))

    def _draw_insights(self, parent):
        """Generate and display quick insights."""
        from modules.analytics import get_insights

        insights = get_insights(self.db)

        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=(0, 20))

        if not insights or (len(insights) == 1 and insights[0]["title"] == "No Data Yet"):
            msg = insights[0]["message"] if insights else "Add more expenses to see personalized insights!"
            ctk.CTkLabel(
                inner, text=msg,
                font=FONTS["body"],
                text_color=self.theme.get("text_secondary", "#b0b0c0"),
            ).pack(pady=10)
            return

        for insight in insights:
            card = ctk.CTkFrame(
                inner,
                fg_color=self.theme.get("card_hover", "#1f1f35"),
                corner_radius=12,
            )
            card.pack(fill="x", pady=6)

            card_inner = ctk.CTkFrame(card, fg_color="transparent")
            card_inner.pack(fill="x", padx=16, pady=12)

            # Icon
            icon_lbl = ctk.CTkLabel(
                card_inner, text=insight["icon"],
                font=("Segoe UI", 24)
            )
            icon_lbl.pack(side="left", padx=(0, 12))

            # Text Stack
            text_stack = ctk.CTkFrame(card_inner, fg_color="transparent")
            text_stack.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                text_stack, text=insight["title"],
                font=FONTS["body_bold"],
                text_color=self.theme.get("text", "#f0f0f5"),
                anchor="w"
            ).pack(anchor="w")

            ctk.CTkLabel(
                text_stack, text=insight["message"],
                font=FONTS["small"],
                text_color=self.theme.get("text_secondary", "#b0b0c0"),
                anchor="w", justify="left", wraplength=700
            ).pack(anchor="w", pady=(2, 0))

    def refresh(self, theme=None, app_mode=None):
        """Rebuild charts with fresh data if changed."""
        if theme:
            self.theme = theme
        if app_mode:
            self.app_mode = app_mode
            
        # Check if data or theme has actually changed
        new_fingerprint = f"{self.db.get_expense_count()}_{self.db.get_total()}_{self.app_mode}"
        if self._data_fingerprint == new_fingerprint:
            return  # No change, avoid expensive redraw
            
        self._data_fingerprint = new_fingerprint
        
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
