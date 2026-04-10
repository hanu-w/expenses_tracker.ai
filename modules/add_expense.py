from modules.storage import load_data, save_data

def add_expense(amount, category, date, note):
    df = load_data()

    new_expense = {
        "amount": float(amount),
        "category": category,
        "date": date,
        "note": note
    }

    df = df._append(new_expense, ignore_index=True)
    save_data(df)

    print("✅ Expense added successfully!")