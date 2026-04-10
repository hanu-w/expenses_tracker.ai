"""
Expense Tracker — Data Models
Defines the Expense dataclass with validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from config import CATEGORIES, DATE_FORMAT


@dataclass
class Expense:
    """Represents a single expense entry."""

    id: int = 0
    amount: float = 0.0
    category: str = "Other"
    date: str = ""
    note: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.date:
            self.date = datetime.now().strftime(DATE_FORMAT)
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @staticmethod
    def validate_amount(amount_str):
        """Validate and return amount as float. Returns None if invalid."""
        try:
            amount = float(amount_str)
            if amount <= 0:
                return None
            return amount
        except (ValueError, TypeError):
            return None

    @staticmethod
    def validate_date(date_str):
        """Validate date string. Returns formatted date or None."""
        try:
            parsed = datetime.strptime(date_str, DATE_FORMAT)
            return parsed.strftime(DATE_FORMAT)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def validate_category(category):
        """Check if category is valid."""
        return category in CATEGORIES

    @classmethod
    def from_dict(cls, data):
        """Create Expense from dictionary."""
        return cls(
            id=data.get("id", 0),
            amount=float(data.get("amount", 0)),
            category=data.get("category", "Other"),
            date=data.get("date", ""),
            note=data.get("note", ""),
            created_at=data.get("created_at", ""),
        )
