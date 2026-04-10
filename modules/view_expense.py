from modules.storage import load_data

def view_expenses():
    df = load_data()

    if df.empty:
        print("⚠️ No expenses found.")
    else:
        print("\n📊 All Expenses:\n")
        print(df)