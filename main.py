"""
💰 ExpenseAI — Smart Expense Tracker
A premium fintech-grade desktop expense tracking application.

Run this file to launch the app:
    python main.py
"""

import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.ui.app import ExpenseTrackerApp


def main():
    """Launch the ExpenseAI application."""
    app = ExpenseTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()