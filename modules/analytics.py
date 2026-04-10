
from modules.storage import load_data

def show_total_expense():
    df = load_data()
    total = df["amount"].sum()
    print(f"\n💰 Total Spending: ₹{total}")