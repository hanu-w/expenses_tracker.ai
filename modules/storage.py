import pandas as pd
import os

FILE_PATH = "data/expenses.csv"

def initialize_file():
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=["amount", "category", "date", "note"])
        df.to_csv(FILE_PATH, index=False)

def load_data():
    return pd.read_csv(FILE_PATH)

def save_data(df):
    df.to_csv(FILE_PATH, index=False)
