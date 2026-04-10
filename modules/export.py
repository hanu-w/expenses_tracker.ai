"""
Expense Tracker — Export Module
CSV export and import functionality.
"""

import csv
from datetime import datetime
from config import DATE_FORMAT


def export_to_csv(db, filepath):
    """Export all expenses to a CSV file."""
    return db.export_to_csv(filepath)


def export_filtered_csv(db, filepath, category=None, start_date=None, end_date=None):
    """Export filtered expenses to CSV."""
    expenses = db.get_expenses_filtered(
        category=category,
        start_date=start_date,
        end_date=end_date,
    )
    if not expenses:
        return False

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "amount", "category", "date", "note", "created_at"]
        )
        writer.writeheader()
        writer.writerows(expenses)

    return True


def import_from_csv(db, filepath):
    """Import expenses from a CSV file."""
    return db.import_from_csv(filepath)
