from modules.database import ExpenseDB

db = ExpenseDB()

db.add_expense(500, "Food", "2026-04-11", "demo")
db.add_expense(1200, "Shopping", "2026-04-10", "demo")
db.add_expense(300, "Transport", "2026-04-09", "demo")

db.close()

print("Demo data added!")