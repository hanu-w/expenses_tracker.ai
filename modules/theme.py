"""
Expense Tracker — Theme System
Dark and light theme definitions with matching chart styles.
"""

# ─── Dark Theme (Default) ────────────────────────────────────
DARK_THEME = {
    "bg":              "#0b0b10",
    "surface":         "#12121a",
    "card":            "#1a1a2e",
    "card_hover":      "#1f1f35",
    "sidebar":         "#0f0f18",
    "sidebar_active":  "#1a1a2e",
    "accent":          "#6c5ce7",
    "accent_hover":    "#7d6ff0",
    "primary":         "#a29bfe",
    "success":         "#00cec9",
    "success_bg":      "#0a2e2d",
    "danger":          "#ff7675",
    "danger_bg":       "#2e0a0a",
    "warning":         "#ffeaa7",
    "warning_bg":      "#2e2a0a",
    "text":            "#f0f0f5",
    "text_secondary":  "#b0b0c0",
    "text_muted":      "#808098",
    "border":          "#2a2a3e",
    "input_bg":        "#16162a",
    "input_border":    "#2a2a40",
    "scrollbar":       "#2a2a3e",
    "chart_bg":        "#12121a",
    "chart_text":      "#f0f0f5",
    "chart_grid":      "#1a1a2e",
}

# ─── Light Theme ──────────────────────────────────────────────
LIGHT_THEME = {
    "bg":              "#f0f2f5",
    "surface":         "#ffffff",
    "card":            "#ffffff",
    "card_hover":      "#f8f8fc",
    "sidebar":         "#1a1a2e",
    "sidebar_active":  "#2a2a42",
    "accent":          "#6c5ce7",
    "accent_hover":    "#5a4bd4",
    "primary":         "#6c5ce7",
    "success":         "#00b894",
    "success_bg":      "#e8f8f5",
    "danger":          "#e17055",
    "danger_bg":       "#fdecea",
    "warning":         "#f39c12",
    "warning_bg":      "#fef9e7",
    "text":            "#2d3436",
    "text_secondary":  "#4a5568",
    "text_muted":      "#718096",
    "border":          "#dfe6e9",
    "input_bg":        "#f5f6fa",
    "input_border":    "#dcdde1",
    "scrollbar":       "#b2bec3",
    "chart_bg":        "#ffffff",
    "chart_text":      "#2d3436",
    "chart_grid":      "#dfe6e9",
}

# ─── Fonts ────────────────────────────────────────────────────
FONTS = {
    "heading":      ("Segoe UI", 22, "bold"),
    "subheading":   ("Segoe UI", 18, "bold"),
    "title":        ("Segoe UI", 16, "bold"),
    "body":         ("Segoe UI", 14),
    "body_bold":    ("Segoe UI", 14, "bold"),
    "small":        ("Segoe UI", 12),
    "small_bold":   ("Segoe UI", 12, "bold"),
    "tiny":         ("Segoe UI", 11),
    "amount_large": ("Segoe UI", 34, "bold"),
    "nav":          ("Segoe UI", 14),
    "nav_active":   ("Segoe UI", 14, "bold"),
    "button":       ("Segoe UI", 14, "bold"),
}


def get_theme(mode="dark"):
    """Return theme dict based on mode."""
    return DARK_THEME if mode == "dark" else LIGHT_THEME


def get_chart_style(mode="dark"):
    """Return matplotlib rcParams dict matching the current theme."""
    theme = get_theme(mode)
    return {
        "figure.facecolor": theme["chart_bg"],
        "axes.facecolor": theme["chart_bg"],
        "axes.edgecolor": theme["chart_grid"],
        "axes.labelcolor": theme["chart_text"],
        "text.color": theme["chart_text"],
        "xtick.color": theme["chart_text"],
        "ytick.color": theme["chart_text"],
        "grid.color": theme["chart_grid"],
        "grid.alpha": 0.3,
        "figure.autolayout": True,
        "font.family": "Segoe UI",
        "font.size": 12,
    }
