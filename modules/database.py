"""
Expense Tracker — SQLite Database Layer
Handles all database operations: CRUD, analytics queries, migration.
"""

import sqlite3
import os
import csv
from datetime import datetime, timedelta
from config import DB_PATH, OLD_CSV_PATH, DATE_FORMAT, CATEGORIES


class ExpenseDB:
    """SQLite database manager for expense data."""

    def __init__(self):
        """Initialize DB connection and create tables if needed."""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._query_cache = {}
        self.create_tables()
        self._migrate_csv_if_needed()

    def create_tables(self):
        """Create expenses and settings tables."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                note TEXT DEFAULT '',
                bill_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bill_id) REFERENCES bills (id) ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                icon TEXT DEFAULT '📌',
                color TEXT DEFAULT '#778ca3',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: Add bill_id to expenses if it doesn't exist (for existing DBs)
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [col["name"] for col in cursor.fetchall()]
        if "bill_id" not in columns:
            cursor.execute("ALTER TABLE expenses ADD COLUMN bill_id INTEGER")

        self.conn.commit()

    def clear_cache(self):
        """Clear the internal query results cache."""
        self._query_cache = {}

    # ─── CRUD Operations ──────────────────────────────────────

    def add_expense(self, amount, category, date, note="", bill_id=None):
        """Add a new expense to the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (amount, category, date, note, bill_id) VALUES (?, ?, ?, ?, ?)",
            (float(amount), category, date, note, bill_id),
        )
        self.conn.commit()
        self.clear_cache()
        return cursor.lastrowid

    def get_all_expenses(self):
        """Get all expenses ordered by date descending."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM expenses ORDER BY date DESC, id DESC")
        return [dict(row) for row in cursor.fetchall()]

    def get_expense_by_id(self, expense_id):
        """Get a single expense by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_expense(self, expense_id, amount, category, date, note="", bill_id=None):
        """Update an existing expense."""
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE expenses 
               SET amount = ?, category = ?, date = ?, note = ?, bill_id = ?
               WHERE id = ?""",
            (float(amount), category, date, note, bill_id, expense_id),
        )
        self.conn.commit()
        self.clear_cache()

    def delete_expense(self, expense_id):
        """Delete an expense by ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        self.conn.commit()
        self.clear_cache()

    def delete_all_expenses(self):
        """Delete all expenses (with caution!)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM expenses")
        self.conn.commit()
        self.clear_cache()

    # ─── Filtered Queries ─────────────────────────────────────

    def get_expenses_filtered(self, category=None, start_date=None, end_date=None, search=None, limit=None, offset=None):
        """Get expenses with optional filters."""
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []

        if category and category != "All":
            query += " AND category = ?"
            params.append(category)

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        if search:
            query += " AND (note LIKE ? OR category LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY date DESC, id DESC"

        if limit:
            query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_filtered_total_and_count(self, category=None, start_date=None, end_date=None, search=None):
        """Get sum of amounts and total count for filtered results without fetching all rows."""
        query = "SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count FROM expenses WHERE 1=1"
        params = []

        if category and category != "All":
            query += " AND category = ?"
            params.append(category)

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        if search:
            query += " AND (note LIKE ? OR category LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return dict(cursor.fetchone())

    # ─── Aggregation Queries ──────────────────────────────────

    def get_total(self):
        """Get total of all expenses (cached)."""
        if "total" in self._query_cache:
            return self._query_cache["total"]
            
        cursor = self.conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM expenses")
        res = cursor.fetchone()["total"]
        self._query_cache["total"] = res
        return res

    def get_weekly_total(self):
        """Get total expenses for the current week (Monday–Sunday)."""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_str = start_of_week.strftime(DATE_FORMAT)
        end_str = today.strftime(DATE_FORMAT)

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date >= ? AND date <= ?",
            (start_str, end_str),
        )
        return cursor.fetchone()["total"]

    def get_monthly_total(self):
        """Get total expenses for the current month."""
        today = datetime.now()
        start_str = today.strftime("%Y-%m-01")
        end_str = today.strftime(DATE_FORMAT)

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date >= ? AND date <= ?",
            (start_str, end_str),
        )
        return cursor.fetchone()["total"]

    def get_category_breakdown(self):
        """Get spending breakdown by category (cached)."""
        if "category_breakdown" in self._query_cache:
            return self._query_cache["category_breakdown"]
            
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT category, COALESCE(SUM(amount), 0) as total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
        """)
        res = [dict(row) for row in cursor.fetchall()]
        self._query_cache["category_breakdown"] = res
        return res

    def get_monthly_breakdown(self, months=6):
        """Get monthly spending for the last N months."""
        today = datetime.now()
        results = []

        for i in range(months - 1, -1, -1):
            # Calculate month
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1

            month_str = f"{year}-{month:02d}"
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE strftime('%Y-%m', date) = ?",
                (month_str,),
            )
            total = cursor.fetchone()["total"]

            # Get month name
            month_name = datetime(year, month, 1).strftime("%b %Y")
            results.append({"month": month_name, "total": total})

        return results

    def get_weekly_trend(self, weeks=8):
        """Get weekly spending trend for last N weeks."""
        today = datetime.now()
        results = []

        for i in range(weeks - 1, -1, -1):
            end = today - timedelta(weeks=i)
            start = end - timedelta(days=6)

            start_str = start.strftime(DATE_FORMAT)
            end_str = end.strftime(DATE_FORMAT)

            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date >= ? AND date <= ?",
                (start_str, end_str),
            )
            total = cursor.fetchone()["total"]

            week_label = f"W{weeks - i}"
            results.append({"week": week_label, "total": total, "start": start_str, "end": end_str})

        return results

    def get_recent_expenses(self, limit=5):
        """Get the most recent N expenses."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM expenses ORDER BY date DESC, id DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_expense_count(self):
        """Get total number of expenses."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM expenses")
        return cursor.fetchone()["count"]

    # ─── Bill Management ──────────────────────────────────────

    def add_bill(self, name):
        """Add a new bill/group."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO bills (name) VALUES (?)", (name,))
        self.conn.commit()
        return cursor.lastrowid

    def get_all_bills(self):
        """Get all bills ordered by creation date."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bills ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def get_expenses_by_bill(self, bill_id):
        """Get all expenses linked to a specific bill."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM expenses WHERE bill_id = ? ORDER BY date DESC",
            (bill_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_bill_summary(self):
        """Get all bills with their total spent amount."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT b.id, b.name, b.created_at, COALESCE(SUM(e.amount), 0) as total
            FROM bills b
            LEFT JOIN expenses e ON b.id = e.bill_id
            GROUP BY b.id
            ORDER BY b.created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def delete_bill(self, bill_id, delete_expenses=False):
        """Delete a bill. Optionally delete all its linked expenses."""
        cursor = self.conn.cursor()
        if delete_expenses:
            cursor.execute("DELETE FROM expenses WHERE bill_id = ?", (bill_id,))
        else:
            # unlink expenses
            cursor.execute("UPDATE expenses SET bill_id = NULL WHERE bill_id = ?", (bill_id,))
        
        cursor.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
        self.conn.commit()
        self.clear_cache()

    # ─── Custom Categories ────────────────────────────────────

    def add_custom_category(self, name, icon="📌", color="#778ca3"):
        """Add a new user-defined category. Returns new id, or None if duplicate."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO custom_categories (name, icon, color) VALUES (?, ?, ?)",
                (name.strip(), icon, color),
            )
            self.conn.commit()
            self.clear_cache()
            return cursor.lastrowid
        except Exception:
            return None  # Duplicate or error

    def get_custom_categories(self):
        """Return all user-defined categories ordered by name."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM custom_categories ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def delete_custom_category(self, name):
        """Delete a custom category by name."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM custom_categories WHERE name = ?", (name,))
        self.conn.commit()
        self.clear_cache()

    # ─── Settings ─────────────────────────────────────────────

    def get_setting(self, key, default=None):
        """Get a setting value by key."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        """Set a setting value (upsert)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value)),
        )
        self.conn.commit()

    # ─── Migration ────────────────────────────────────────────

    def _migrate_csv_if_needed(self):
        """Migrate data from old CSV if it exists and DB is empty."""
        if not os.path.exists(OLD_CSV_PATH):
            return

        # Only migrate if DB has no expenses yet
        if self.get_expense_count() > 0:
            return

        try:
            with open(OLD_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    amount = row.get("amount", "0")
                    category = row.get("category", "Other")
                    date = row.get("date", datetime.now().strftime(DATE_FORMAT))
                    note = row.get("note", "")

                    try:
                        self.add_expense(float(amount), category, date, note)
                        count += 1
                    except (ValueError, TypeError):
                        continue

                if count > 0:
                    print(f"[OK] Migrated {count} expenses from CSV to SQLite")

        except Exception as e:
            print(f"[WARN] CSV migration skipped: {e}")

    # ─── Export ────────────────────────────────────────────────

    def export_to_csv(self, filepath):
        """Export all expenses to a CSV file."""
        expenses = self.get_all_expenses()
        if not expenses:
            return False

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "amount", "category", "date", "note", "created_at"])
            writer.writeheader()
            writer.writerows(expenses)

        return True

    def _parse_date(self, date_str):
        """Try parsing date with multiple formats."""
        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", 
            "%d-%m-%Y", "%Y/%m/%d", "%d %b %Y"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime(DATE_FORMAT)
            except ValueError:
                continue
        return None

    def import_from_csv(self, filepath):
        """Import expenses from a CSV file with flexible validation."""
        import_results = {"success": 0, "total": 0, "skipped": 0}
        
        try:
            with open(filepath, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    import_results["total"] += 1
                    
                    # 0. Lowercase all keys for case-insensitive lookup
                    clean_row = {k.lower().strip(): v for k, v in row.items()}
                    
                    try:
                        # 1. Validate Amount
                        amount_raw = clean_row.get("amount", "0")
                        amount = float(amount_raw)
                        if amount <= 0:
                            raise ValueError("Amount must be positive")

                        # 2. Validate Category
                        category = clean_row.get("category", "").strip()
                        if category not in CATEGORIES:
                            # Map to 'Other' if it's non-empty but unknown
                            category = category if category else "Other"
                            if category not in CATEGORIES:
                                category = "Other"

                        # 3. Validate Date
                        date_raw = clean_row.get("date", "").strip()
                        if not date_raw:
                            raise ValueError("Date missing")
                            
                        parsed_date = self._parse_date(date_raw)
                        if not parsed_date:
                            raise ValueError(f"Unsupported date format: {date_raw}")
                        
                        # 4. Note (Consolidate note, payment_mode, month)
                        note_parts = []
                        main_note = clean_row.get("note", "").strip()
                        if main_note: note_parts.append(main_note)
                        
                        payment = clean_row.get("payment_mode", "").strip()
                        if payment: note_parts.append(f"via {payment}")
                        
                        month_context = clean_row.get("month", "").strip()
                        if month_context: note_parts.append(f"({month_context})")
                        
                        final_note = " ".join(note_parts)

                        # Insert
                        self.add_expense(amount, category, parsed_date, final_note)
                        import_results["success"] += 1

                    except (ValueError, TypeError):
                        import_results["skipped"] += 1
                        continue
                        
        except Exception:
            return {"success": 0, "total": 0, "skipped": 0, "error": True}

        return import_results

    def close(self):
        """Close database connection."""
        self.conn.close()
