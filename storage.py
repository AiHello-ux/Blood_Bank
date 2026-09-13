"""
storage.py

The only file in this program that touches the disk. It knows how to
save the stock list to a CSV file, and read it back later.

blood_bank_logic.py stays "pure" (no file reading/writing at all), and
main.py just calls the two functions below whenever the stock changes.
"""

import csv

STOCK_FILE = "stock.csv"
FIELDNAMES = ["id", "group", "expiry", "status"]


def save_stock(stock):
    """Write the current stock list to stock.csv, overwriting it."""
    with open(STOCK_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(stock)


def load_stock():
    """
    Read stock.csv and return it as a list of dicts, in the same shape
    as the in-memory stock list. If the file doesn't exist yet (the
    very first run), just return an empty list instead of crashing.
    """
    stock = []
    try:
        with open(STOCK_FILE, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stock.append(dict(row))
    except FileNotFoundError:
        pass
    return stock


def next_unit_counter(stock):
    """
    Look at every id already in stock (like "U007") and return one
    more than the highest number found. This stops freshly added
    units from reusing an id that's already sitting in the file.
    Returns 1 if stock is empty.
    """
    highest = 0
    for unit in stock:
        number_part = unit["id"][1:]   # strip the leading "U"
        number = int(number_part)
        if number > highest:
            highest = number
    return highest + 1