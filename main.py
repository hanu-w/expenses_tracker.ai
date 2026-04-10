from modules.storage import initialize_file
from modules.add_expense import add_expense
from modules.view_expense import view_expenses
from modules.analytics import show_total_expense

def menu():
    print("\n==== EXPENSE TRACKER ====")
    print("1. Add Expense")
    print("2. View Expenses")
    print("3. Show Total Spending")
    print("4. Exit")

def main():
    initialize_file()

    while True:
        menu()
        choice = input("Enter choice: ")

        if choice == "1":
            amount = input("Enter amount: ")
            category = input("Enter category: ")
            date = input("Enter date (YYYY-MM-DD): ")
            note = input("Enter note (optional): ")

            add_expense(amount, category, date, note)

        elif choice == "2":
            view_expenses()

        elif choice == "3":
            show_total_expense()

        elif choice == "4":
            print("Exiting...")
            break

        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()