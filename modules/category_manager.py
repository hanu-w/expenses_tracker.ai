"""
Expense Tracker — Category Manager
Merges built-in and user-defined (custom) categories at runtime,
providing icon/color lookups that fall back to sensible defaults.
"""

from config import CATEGORIES as _BUILTIN_CATEGORIES
from config import CATEGORY_COLORS as _BUILTIN_COLORS
from config import CATEGORY_ICONS as _BUILTIN_ICONS

# A curated palette auto-assigned to new custom categories (cycles).
_CUSTOM_PALETTE = [
    "#e84393", "#00b4d8", "#f4a261", "#2dc653", "#e63946",
    "#7b2fff", "#ff9f1c", "#06d6a0", "#118ab2", "#ef476f",
    "#8338ec", "#fb5607", "#3a86ff", "#ffbe0b", "#ff006e",
]


def _pick_color(index: int) -> str:
    """Cycle through the palette for a consistent auto-color."""
    return _CUSTOM_PALETTE[index % len(_CUSTOM_PALETTE)]


# ─── Public API ───────────────────────────────────────────────────────────────

def get_all_categories(db) -> list[str]:
    """
    Return the full ordered category list:
    built-ins first (minus 'Other'), custom ones next, then 'Other' last.
    """
    custom = [c["name"] for c in db.get_custom_categories()]
    builtin_without_other = [c for c in _BUILTIN_CATEGORIES if c != "Other"]
    merged = builtin_without_other + [c for c in custom if c not in _BUILTIN_CATEGORIES]
    # Always keep "Other" at the end
    merged.append("Other")
    return merged


def get_category_icon(db, category: str) -> str:
    """Return the icon emoji for a category (built-in or custom)."""
    if category in _BUILTIN_ICONS:
        return _BUILTIN_ICONS[category]
    for c in db.get_custom_categories():
        if c["name"] == category:
            return c["icon"]
    return "📌"


def get_category_color(db, category: str) -> str:
    """Return the display color for a category (built-in or custom)."""
    if category in _BUILTIN_COLORS:
        return _BUILTIN_COLORS[category]
    for idx, c in enumerate(db.get_custom_categories()):
        if c["name"] == category:
            return c.get("color") or _pick_color(idx)
    return "#778ca3"


def build_option_labels(db, include_add_option: bool = True) -> list[str]:
    """
    Build display strings for a category OptionMenu.
    Returns plain category names (no emoji prefix).
    Optionally appends '＋ Add Category'.
    """
    labels = list(get_all_categories(db))
    if include_add_option:
        labels.append("＋ Add Category")
    return labels


def label_to_name(label: str) -> str:
    """Return the category name from an option label (plain names, no prefix to strip)."""
    return label
