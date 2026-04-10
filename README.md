# 💰 ExpenseAI — Smart Expense Tracker

A premium, fintech-grade desktop expense tracking application built entirely with Python. No HTML, no CSS — just Python.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-v1.0.0-purple?style=flat-square)

---

## ✨ Features

- **Dashboard** — Financial overview with stat cards, mini charts, and recent expenses
- **Add Expense** — Quick expense entry with validation and instant feedback
- **Expense List** — Searchable, filterable list with category badges and delete
- **Charts** — Pie (category breakdown), Bar (monthly spending), Line (weekly trend)
- **Dark/Light Mode** — Toggle between dark and light themes
- **Budget Tracking** — Set monthly budget with alerts at 80%+ usage
- **Data Export** — Export all expenses to CSV
- **Data Import** — Import expenses from CSV files
- **Persistent Storage** — SQLite database, data survives restarts
- **Smart Insights** — AI-powered spending pattern analysis

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| **CustomTkinter** | Modern UI framework with dark mode |
| **Matplotlib** | Interactive charts (pie, bar, line) |
| **SQLite3** | Local database storage |
| **pandas** | Data processing & CSV export |
| **Pillow** | Image handling |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd expense-tracker

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

---

## 📁 Project Structure

```
expense_tracker/
├── main.py                    # App entry point
├── config.py                  # App configuration & constants
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── data/
│   ├── expenses.db            # SQLite database
│   └── archive/               # Old data backups
├── modules/
│   ├── __init__.py
│   ├── database.py            # SQLite database layer
│   ├── models.py              # Expense data model
│   ├── analytics.py           # Insights & analytics engine
│   ├── export.py              # CSV export/import
│   ├── theme.py               # Dark/Light theme definitions
│   └── ui/
│       ├── __init__.py
│       ├── app.py             # Main application window
│       ├── sidebar.py         # Navigation sidebar
│       ├── dashboard.py       # Dashboard view
│       ├── add_expense.py     # Add expense form
│       ├── expense_list.py    # Expense list view
│       ├── charts.py          # Charts & analytics view
│       ├── settings.py        # Settings panel
│       └── components.py      # Reusable UI components
```

---

## 📸 Screenshots

*Run the app to see the beautiful dark-themed UI with charts and insights!*

---

## 🎯 Categories

| Category | Icon | Color |
|----------|------|-------|
| Food | 🍔 | Red |
| Transport | 🚗 | Teal |
| Shopping | 🛍️ | Blue |
| Bills | 📄 | Yellow |
| Entertainment | 🎮 | Purple |
| Health | 💊 | Green |
| Education | 📚 | Orange |
| Other | 📌 | Gray |

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Built with ❤️ using Python**
