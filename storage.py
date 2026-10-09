"""
storage.py

The only file in this program that touches the disk. It knows how to
save the stock list to a CSV file, and read it back later.

blood_bank_logic.py stays "pure" (no file reading/writing at all), and
main.py just calls the functions below whenever the stock changes.
"""

import csv
import os

# Build the path from THIS file's own folder, not from whatever folder the
# program happened to be started in. That way there is only ever one
# stock.csv, no matter how or where you run main.py.
STOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock.csv")
FIELDNAMES = ["id", "group", "expiry", "status"]

# Set to False once you no longer want the "Saved to ..." line.
SHOW_SAVE_PATH = True


def save_stock(stock, path=None):
    """
    Write the stock list to the CSV file, overwriting it.
    Returns True if the file was written, False if it could not be.

    The data is written to a temporary file first and then renamed over
    the real file. If anything goes wrong halfway, the real stock.csv is
    left untouched instead of being half-written.

    If the file is open in Excel (Windows locks it), we print a clear
    message instead of crashing.
    """
    if path is None:
        path = STOCK_FILE
    temp_path = path + ".tmp"

    try:
        with open(temp_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(stock)
        os.replace(temp_path, path)
    except PermissionError:
        _remove_quietly(temp_path)
        print("Error: Could not save " + path + ".")
        print("Close stock.csv in Excel (or any other program) and try again.")
        return False
    except OSError as error:
        _remove_quietly(temp_path)
        print("Error: Could not save " + path + " (" + str(error) + ").")
        return False

    if SHOW_SAVE_PATH:
        print("Saved to " + path)
    return True


def _remove_quietly(path):
    """Delete a leftover temp file if it exists; never raise."""
    try:
        os.remove(path)
    except OSError:
        pass


def load_stock(path=None):
    """
    Read the CSV file and return it as a list of dicts, in the same shape
    as the in-memory stock list. If the file doesn't exist yet (the
    very first run), just return an empty list instead of crashing.

    "utf-8-sig" quietly drops the invisible marker Excel sometimes adds at
    the start of a CSV file, which would otherwise corrupt the first
    column name.
    """
    if path is None:
        path = STOCK_FILE

    stock = []
    try:
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
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
