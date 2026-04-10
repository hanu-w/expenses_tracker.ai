"""
Expense Tracker — Application Configuration
Central configuration for app settings, categories, and defaults.
"""

# ─── App Info ────────────────────────────────────────────────
APP_NAME = "ExpenseAI"
APP_VERSION = "1.0.0"
APP_TITLE = "💰 ExpenseAI — Smart Expense Tracker"

# ─── Window Settings ─────────────────────────────────────────
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 750
MIN_WIDTH = 900
MIN_HEIGHT = 600
SIDEBAR_WIDTH = 220

# ─── Currency ─────────────────────────────────────────────────
CURRENCY_SYMBOL = "₹"
CURRENCY_NAME = "INR"

# ─── Categories ───────────────────────────────────────────────
CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Education",
    "Other",
]

# Category colors (for charts and badges)
CATEGORY_COLORS = {
    "Food":          "#ff6b6b",
    "Transport":     "#4ecdc4",
    "Shopping":      "#45b7d1",
    "Bills":         "#f9ca24",
    "Entertainment": "#a55eea",
    "Health":        "#26de81",
    "Education":     "#fd9644",
    "Other":         "#778ca3",
}

# Category icons (emoji)
CATEGORY_ICONS = {
    "Food":          "🍔",
    "Transport":     "🚗",
    "Shopping":      "🛍️",
    "Bills":         "📄",
    "Entertainment": "🎮",
    "Health":        "💊",
    "Education":     "📚",
    "Other":         "📌",
}

# ─── Database ─────────────────────────────────────────────────
DB_PATH = "data/expenses.db"
OLD_CSV_PATH = "data/expenses.csv"

# ─── Budget ───────────────────────────────────────────────────
DEFAULT_BUDGET = 0  # 0 means no budget set

# ─── Date Formats ─────────────────────────────────────────────
DATE_FORMAT = "%Y-%m-%d"
DISPLAY_DATE_FORMAT = "%d %b %Y"
