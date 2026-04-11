"""
Expense Tracker — Settings View
Theme toggle, budget setting, CSV export/import, data management.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from config import CURRENCY_SYMBOL, APP_VERSION
from modules.theme import FONTS


class SettingsView(ctk.CTkFrame):
    """Settings panel with theme, budget, export, and data management."""

    def __init__(self, master, db, theme, app_mode="dark",
                 on_theme_change=None, on_data_changed=None, **kwargs):
        self.db = db
        self.theme = theme
        self.app_mode = app_mode
        self.on_theme_change = on_theme_change
        self.on_data_changed = on_data_changed

        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        """Build the settings layout."""
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.theme.get("scrollbar", "#2a2a3e"),
        )
        scroll.pack(fill="both", expand=True)
        content = scroll

        # ─── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 20))

        ctk.CTkLabel(
            header, text="Settings",
            font=FONTS["heading"],
            text_color=self.theme.get("text", "#f0f0f5"),
            anchor="w"
        ).pack(side="left")

        # ─── Appearance Section ──────────────────────────────
        self._section_header(content, "🎨  Appearance")

        appearance_card = self._card(content)

        row = ctk.CTkFrame(appearance_card, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=20)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            left, text="Dark Mode", font=FONTS["body_bold"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            left, text="Toggle between dark and light themes",
            font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"), anchor="w"
        ).pack(fill="x", pady=(4, 0))

        self.theme_switch = ctk.CTkSwitch(
            row, text="",
            onvalue="dark", offvalue="light",
            command=self._on_theme_toggle,
            progress_color=self.theme.get("accent", "#6c5ce7"),
            button_color="#ffffff",
            fg_color=self.theme.get("input_bg", "#16162a"),
        )
        self.theme_switch.pack(side="right", padx=(20, 0))

        if self.app_mode == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

        # ─── Budget Section ──────────────────────────────────
        self._section_header(content, "💰  Monthly Budget")

        budget_card = self._card(content)
        budget_inner = ctk.CTkFrame(budget_card, fg_color="transparent")
        budget_inner.pack(fill="x", padx=24, pady=20)

        ctk.CTkLabel(
            budget_inner, text="Set a monthly spending limit to get alerts when you're close",
            font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"), anchor="w"
        ).pack(fill="x", pady=(0, 12))

        budget_row = ctk.CTkFrame(budget_inner, fg_color="transparent")
        budget_row.pack(fill="x")

        ctk.CTkLabel(
            budget_row, text=CURRENCY_SYMBOL,
            font=("Segoe UI", 22, "bold"),
            text_color=self.theme.get("accent", "#6c5ce7"),
        ).pack(side="left", padx=(0, 10))

        current_budget = self.db.get_setting("monthly_budget", "0")
        self.budget_var = ctk.StringVar(value=current_budget if current_budget != "0" else "")

        self.budget_entry = ctk.CTkEntry(
            budget_row, textvariable=self.budget_var,
            placeholder_text="e.g., 10000",
            font=FONTS["body"], width=220, height=42, corner_radius=10,
            fg_color=self.theme.get("input_bg", "#16162a"),
            border_color=self.theme.get("input_border", "#2a2a40"),
            text_color=self.theme.get("text", "#f0f0f5"),
            placeholder_text_color=self.theme.get("text_muted", "#808098"),
        )
        self.budget_entry.pack(side="left", padx=(0, 14))

        save_btn = ctk.CTkButton(
            budget_row, text="Save", font=FONTS["button"],
            fg_color=self.theme.get("accent", "#6c5ce7"),
            hover_color=self.theme.get("accent_hover", "#7d6ff0"),
            text_color="#ffffff", width=90, height=42, corner_radius=10,
            command=self._on_save_budget,
        )
        save_btn.pack(side="left")

        self.budget_msg = ctk.CTkLabel(
            budget_inner, text="", font=FONTS["body"],
            text_color=self.theme.get("success", "#00cec9"),
        )
        self.budget_msg.pack(fill="x", pady=(10, 0))

        # ─── Data Management Section ─────────────────────────
        self._section_header(content, "📁  Data Management")

        data_card = self._card(content)
        data_inner = ctk.CTkFrame(data_card, fg_color="transparent")
        data_inner.pack(fill="x", padx=24, pady=20)

        # Export
        export_row = ctk.CTkFrame(data_inner, fg_color="transparent")
        export_row.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            export_row, text="Export all expenses to CSV file",
            font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"), anchor="w"
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            export_row, text="📥 Export CSV", font=FONTS["button"],
            fg_color=self.theme.get("success", "#00cec9"),
            hover_color="#00b8b3", text_color="#ffffff",
            width=150, height=40, corner_radius=10,
            command=self._on_export,
        ).pack(side="right")

        # Import
        import_row = ctk.CTkFrame(data_inner, fg_color="transparent")
        import_row.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            import_row, text="Import expenses from a CSV file",
            font=FONTS["body"],
            text_color=self.theme.get("text_secondary", "#b0b0c0"), anchor="w"
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            import_row, text="📤 Import CSV", font=FONTS["button"],
            fg_color=self.theme.get("primary", "#a29bfe"),
            hover_color="#9084f0", text_color="#ffffff",
            width=150, height=40, corner_radius=10,
            command=self._on_import,
        ).pack(side="right")

        # Divider
        ctk.CTkFrame(
            data_inner, fg_color=self.theme.get("border", "#2a2a3e"), height=1
        ).pack(fill="x", pady=10)

        # Clear All
        clear_row = ctk.CTkFrame(data_inner, fg_color="transparent")
        clear_row.pack(fill="x", pady=(0, 0))

        ctk.CTkLabel(
            clear_row, text="⚠️ Clear all expense data (cannot be undone)",
            font=FONTS["body"],
            text_color=self.theme.get("danger", "#ff7675"), anchor="w"
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            clear_row, text="🗑️ Clear All", font=FONTS["button"],
            fg_color=self.theme.get("danger_bg", "#2e0a0a"),
            hover_color=self.theme.get("danger", "#ff7675"),
            text_color=self.theme.get("danger", "#ff7675"),
            width=150, height=40, corner_radius=10,
            command=self._on_clear_all,
        ).pack(side="right")

        # ─── About Section ───────────────────────────────────
        self._section_header(content, "ℹ️  About")

        about_card = self._card(content)
        about_inner = ctk.CTkFrame(about_card, fg_color="transparent")
        about_inner.pack(fill="x", padx=24, pady=20)

        info_lines = [
            f"ExpenseAI v{APP_VERSION}",
            "Smart Expense Tracker — Built with Python",
            "",
            "Tech Stack:",
            "• CustomTkinter (UI Framework)",
            "• Matplotlib (Charts)",
            "• SQLite (Database)",
            "• pandas (Data Processing)",
        ]

        for line in info_lines:
            if line:
                ctk.CTkLabel(
                    about_inner, text=line,
                    font=FONTS["body"],
                    text_color=self.theme.get("text_secondary", "#b0b0c0"),
                    anchor="w"
                ).pack(fill="x", pady=2)
            else:
                # Empty spacer line
                ctk.CTkFrame(about_inner, fg_color="transparent", height=6).pack(fill="x")

        # Bottom padding
        ctk.CTkFrame(content, fg_color="transparent", height=24).pack()

    def _section_header(self, parent, text):
        """Create a section header label."""
        ctk.CTkLabel(
            parent, text=text, font=FONTS["title"],
            text_color=self.theme.get("text", "#f0f0f5"), anchor="w"
        ).pack(fill="x", padx=28, pady=(20, 8))

    def _card(self, parent):
        """Create a styled card frame."""
        card = ctk.CTkFrame(
            parent, fg_color=self.theme.get("card", "#1a1a2e"),
            corner_radius=16, border_width=1,
            border_color=self.theme.get("border", "#2a2a3e"),
        )
        card.pack(fill="x", padx=28)
        return card

    def _on_theme_toggle(self):
        """Handle theme switch."""
        mode = self.theme_switch.get()
        if self.on_theme_change:
            self.on_theme_change(mode)

    def _on_save_budget(self):
        """Save monthly budget setting."""
        val = self.budget_var.get().strip()
        try:
            budget = float(val) if val else 0
            if budget < 0:
                raise ValueError
            self.db.set_setting("monthly_budget", str(budget))
            self.budget_msg.configure(
                text=f"✅ Budget set to {CURRENCY_SYMBOL}{budget:,.0f}" if budget > 0 else "✅ Budget disabled",
                text_color=self.theme.get("success", "#00cec9"),
            )
            self.after(4000, lambda: self.budget_msg.configure(text=""))
        except ValueError:
            self.budget_msg.configure(
                text="❌ Enter a valid number",
                text_color=self.theme.get("danger", "#ff7675"),
            )
            self.after(4000, lambda: self.budget_msg.configure(text=""))

    def _on_export(self):
        """Export data to CSV."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="expenses_export.csv",
            title="Export Expenses",
        )
        if filepath:
            success = self.db.export_to_csv(filepath)
            if success:
                messagebox.showinfo("Export", f"✅ Expenses exported successfully!\n\n{filepath}")
            else:
                messagebox.showwarning("Export", "⚠️ No expenses to export.")

    def _on_import(self):
        """Import data from CSV."""
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            title="Import Expenses",
        )
        if filepath:
            count = self.db.import_from_csv(filepath)
            messagebox.showinfo("Import", f"✅ Imported {count} expenses!")
            if self.on_data_changed:
                self.on_data_changed()

    def _on_clear_all(self):
        """Clear all expense data."""
        result = messagebox.askyesno(
            "Clear All Data",
            "⚠️ This will permanently delete ALL your expense data.\n\n"
            "Are you sure? This cannot be undone.",
            icon="warning",
        )
        if result:
            self.db.delete_all_expenses()
            messagebox.showinfo("Cleared", "✅ All expense data has been cleared.")
            if self.on_data_changed:
                self.on_data_changed()

    def refresh(self, theme=None, app_mode=None, **kwargs):
        """Rebuild with updated theme."""
        if theme:
            self.theme = theme
        if app_mode:
            self.app_mode = app_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
