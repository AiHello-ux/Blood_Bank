"""
main.py

This file holds all the printing and input() calls, and the state
that changes while the program runs (stock, pending_requests, etc).
All the "thinking" is done by calling functions from
blood_bank_logic.py.
"""

from datetime import date

import blood_bank_logic as logic
import storage


GROUP_ORDER = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


def render_stock_table(stock):
    """Build the eight-row stock table as printable text."""
    lines = []
    header = "Group".ljust(6) + "Available".ljust(12) + "Nearest Expiry"
    lines.append(header)

    for group in GROUP_ORDER:
        count = 0
        nearest = None

        for unit in stock:
            if unit["group"] == group and unit["status"] == "Available":
                count = count + 1
                if nearest is None or unit["expiry"] < nearest:
                    nearest = unit["expiry"]

        if nearest is None:
            nearest_display = "-"
        else:
            nearest_display = nearest

        line = group.ljust(6) + str(count).ljust(12) + nearest_display
        lines.append(line)

    table_text = "\n".join(lines)
    return table_text


def render_menu():
    """Build the seven-option menu as printable text."""
    lines = []
    lines.append("1. Add stock")
    lines.append("2. Submit request")
    lines.append("3. Generate allocation plan")
    lines.append("4. Confirm & issue plan")
    lines.append("5. View progress report")
    lines.append("6. View expired/wasted report")
    lines.append("7. Exit")
    menu_text = "\n".join(lines)
    return menu_text


def read_add_stock_input():
    """
    Prompt for one or more 'group expiry' pairs, comma-separated.
    Return them as a list of dicts: {"group": str, "expiry": str}.
    """
    raw = input("Enter group and expiry date (e.g., O+ 2026-10-01), comma-separated: ")

    pairs = []
    pieces = raw.split(",")

    for piece in pieces:
        piece = piece.strip()
        if piece == "":
            continue

        parts = piece.split()
        if len(parts) < 2:
            print("Error: Could not read \"" + piece + "\". Expected a group and a date.")
            continue

        pair = {}
        pair["group"] = parts[0]
        pair["expiry"] = parts[1]
        pairs.append(pair)

    return pairs


def read_request_input():
    """
    Prompt for hospital details, urgency, and multiple blood groups.
    """
    hospital = input("Hospital name: ")
    hospital_type = input("Hospital type (Private/Govt): ")
    urgency = input("Urgency (High/Mid/Low): ")
    items_raw = input("Enter blood groups and quantities (e.g., A+ 2, B+ 1): ")

    raw_request = {}
    raw_request["hospital"] = hospital
    raw_request["hospital_type"] = hospital_type
    raw_request["urgency"] = urgency
    raw_request["items_raw"] = items_raw
    return raw_request


def print_bill(allocation):
    """Print the itemized bill for a Total/Partial allocation, or the rejection message."""
    if allocation["status"] == "Total" or allocation["status"] == "Partial":
        print("-------- BILL --------")
        print("Request: " + allocation["request_id"] + " (" + allocation["hospital"] + ")")
        for item in allocation["item_results"]:
            if item["status"] == "Rejected":
                print(" - " + item["group"] + ": Rejected (Need " + str(item["needed"]) + ", Have 0)")
            else:
                print(" - " + item["group"] + ": " + item["status"] + " (" + str(item["allocated_qty"]) + " of " + str(item["needed"]) + " issued)")
                
        print("Unit ID   Group   Expiry       Fee")
        for detail in allocation["units"]:
            line = (detail["id"].ljust(10) + detail["group"].ljust(8)
                    + detail["expiry"].ljust(13) + "Rs " + str(detail["fee"]))
            print(line)
        print("-----------------------")
        if allocation["hospital_type"] == "Govt":
            print("Transportation Charge: Rs 0")
        else:
            print("Transportation Charge: Rs 100")
        print("-----------------------")
        print("TOTAL AMOUNT: Rs " + str(allocation["total"]))
        print("Overall Status: " + allocation["status"])
        print("-----------------------")
    else:
        print("-------- BILL --------")
        print("Request: " + allocation["request_id"] + " (" + allocation["hospital"] + ")")
        for item in allocation["item_results"]:
            print("Requested: " + str(item["needed"]) + " units of " + item["group"])
            print("Available (compatible): " + str(item["available"]) + " units")
        print("Overall Status: Completely Rejected - insufficient stock for all items.")
        print("-----------------------")


def print_plan(plan):
    """Print every request's proposed outcome in a plan, then the proposed total revenue."""
    for allocation in plan["allocations"]:
        items_str = ", ".join([str(i["needed"]) + " " + i["group"] for i in allocation["item_results"]])
        header = ("Request " + allocation["request_id"] + " (" + allocation["hospital"]
                   + ", " + allocation["hospital_type"] + ", " + items_str
                   + ", " + allocation["urgency"] + ")")
        print(header)

        if allocation["status"] == "Total" or allocation["status"] == "Partial":
            for detail in allocation["units"]:
                line = ("Proposed: " + detail["id"] + " " + detail["group"]
                        + " (exp " + detail["expiry"] + ") Rs " + str(detail["fee"]))
                print(line)
            
            if allocation["hospital_type"] == "Govt":
                print("Transportation: Rs 0")
            else:
                print("Transportation: Rs 100")
                
            print("Overall Status: " + allocation["status"] + " - Total Rs " + str(allocation["total"]))
        else:
            print("Overall Status: Completely Rejected - insufficient stock for all items.")
        print("")

    print("Proposed Total Revenue: Rs " + str(plan["proposed_revenue"]))
    print("Choose option 4 to confirm and issue this plan.")


def print_progress_report(report):
    """Print the FR 7 progress report."""
    print("Requests handled: " + str(report["handled"]) + " total")
    print("Fulfilled: " + str(report["fulfilled"]))
    print("Rejected: " + str(report["rejected"]))
    print("Total Revenue so far: Rs " + str(report["revenue"]))


def print_wasted_report(report, stock):
    """Print the FR 8 expired/wasted report."""
    print("Expired / Wasted Units: " + str(report["count"]))
    for unit in stock:
        if unit["status"] == "Wasted":
            print(unit["id"] + " " + unit["group"] + " expired " + unit["expiry"])
    print("Total Value Lost: Rs " + str(report["value"]))


def save_if_changed(stock, last_saved):
    """
    Save stock to disk only if it differs from what is already saved.
    Returns the stock that is now on disk: the new stock if the save
    worked, or the old one if it failed (so we automatically try again
    after the next action).
    """
    if stock == last_saved:
        return last_saved
    if storage.save_stock(stock):
        return stock
    return last_saved


def main():
    """Run the session loop: expire units, show table/menu, dispatch, repeat until Exit."""
    # Step 1 (Program Flow): Stock is loaded from stock.csv, so it survives
    # between runs. Everything else still starts empty/zero each session.
    stock = storage.load_stock()
    pending_requests = []
    current_plan = None
    session_log = logic.new_session_log()
    unit_counter = storage.next_unit_counter(stock)   # continues from the highest id in the file

    # Units already marked Wasted in the file were lost in an earlier run.
    # Fold them back into the wasted log so the FR 8 report (count + value)
    # matches the list of Wasted units it prints. Pending requests and the
    # plan are NOT saved: they only live for one session.
    for unit in stock:
        if unit["status"] == "Wasted":
            session_log["wasted_units"].append(unit)
            session_log["wasted_value"] = session_log["wasted_value"] + 500

    # What is currently on disk. Whenever `stock` differs from this, the
    # single save point below writes it out.
    last_saved = stock
    request_counter = 1    # next request gets ID "R001", then "R002", etc.

    while True:
        today = date.today().isoformat()

        # Step 2: Check for expired blood. Anything Available whose date
        # has already passed gets flipped to Wasted before we show anything.
        stock, wasted = logic.expire_units(stock, today)
        if len(wasted) > 0:
            # Build the "[N units expired and discarded: ...]" message and
            # fold each wasted unit's value into the running loss total.
            parts = []
            for unit in wasted:
                parts.append(unit["id"] + " (" + unit["group"] + ", exp " + unit["expiry"] + ")")
                session_log["wasted_units"].append(unit)
                session_log["wasted_value"] = session_log["wasted_value"] + 500

            if len(wasted) == 1:
                word = "unit"
            else:
                word = "units"

            joined = ", ".join(parts)
            print("[" + str(len(wasted)) + " " + word + " expired and discarded: " + joined + "]")

        # Single save point (1 of 2): after the expiry step.
        last_saved = save_if_changed(stock, last_saved)

        # Step 3: Show the stock table and menu.
        print("")
        print(render_stock_table(stock))
        print("Pending requests: " + str(len(pending_requests)))
        print("")
        print(render_menu())

        # Step 4: Ask the staff to choose an option.
        choice_text = input("Choose an option: ").strip()

        # Step 5: If it's not a valid number 1-7, show an error and loop
        # back to step 3 (the "continue" skips straight to the top of the
        # while loop, re-printing the table and menu).
        if not choice_text.isdigit():
            print("Error: Invalid option. Please choose a number between 1 and 7.")
            continue

        choice = int(choice_text)

        if choice < 1 or choice > 7:
            print("Error: Invalid option. Please choose a number between 1 and 7.")
            continue

        print("")

        # Step 6: Run whichever action they picked. Each branch below does
        # its own reading, validating, and calling into blood_bank_logic.py
        # (the "brain" file) for anything that needs deciding.

        if choice == 1:
            # --- Add stock (FR 2) ---
            # Read one or more "group expiry" pairs, then add each one that
            # passes validation (real group, not expired, within 35 days).
            pairs = read_add_stock_input()

            for pair in pairs:
                group = pair["group"].strip().upper()
                expiry = pair["expiry"].strip()

                if not logic.is_valid_group(group):
                    print("Error: Invalid blood group \"" + group + "\". Unit not added.")
                    continue

                if not logic.is_valid_date(expiry):
                    print("Error: Invalid date \"" + expiry + "\". Use YYYY-MM-DD. Unit not added.")
                    continue

                if logic.is_expired(expiry, today):
                    print("Error: Expiry date " + expiry + " is in the past. Unit not added.")
                    continue

                if not logic.is_within_shelf_life(expiry, today):
                    print("Error: Expiry date " + expiry + " is more than 35 days from today. Unit not added.")
                    continue

                # All checks passed -- give it the next unit ID and add it.
                unit_id = "U" + str(unit_counter).zfill(3)
                stock = logic.add_unit(stock, unit_id, group, expiry, today)
                unit_counter = unit_counter + 1
                print("Added: " + unit_id + " " + group + " (exp " + expiry + ")")

        elif choice == 2:
            # --- Submit request (FR 3) ---
            # Read the request, validate every field, then either decide it
            # immediately (High urgency) or queue it (Mid/Low urgency).
            raw = read_request_input()
            hospital = raw["hospital"].strip()

            if hospital == "":
                print("Error: Hospital name cannot be blank.")
            else:
                lowered_type = raw["hospital_type"].strip().lower()
                if lowered_type == "private":
                    hospital_type = "Private"
                elif lowered_type == "govt":
                    hospital_type = "Govt"
                else:
                    hospital_type = raw["hospital_type"].strip()

                lowered_urgency = raw["urgency"].strip().lower()
                if lowered_urgency == "high":
                    urgency = "High"
                elif lowered_urgency == "mid":
                    urgency = "Mid"
                elif lowered_urgency == "low":
                    urgency = "Low"
                else:
                    urgency = raw["urgency"].strip()

                if not logic.is_valid_urgency(urgency):
                    print("Error: Invalid urgency \"" + raw["urgency"] + "\". Must be High, Mid, or Low.")
                    print("Status: Rejected")
                elif not logic.is_valid_hospital_type(hospital_type):
                    print("Error: Invalid hospital type \"" + raw["hospital_type"] + "\". Must be Private or Govt.")
                    print("Status: Rejected")
                else:
                    # Process comma-separated items like "A+ 2, B+ 1"
                    pieces = raw["items_raw"].split(",")
                    items = []
                    valid = True
                    
                    for piece in pieces:
                        piece = piece.strip()
                        if piece == "":
                            continue
                        
                        parts = piece.split()
                        if len(parts) < 2:
                            print("Error: Could not read \"" + piece + "\". Expected group and quantity.")
                            valid = False
                            break
                            
                        group = parts[0].strip().upper()
                        quantity_text = parts[1].strip()

                        if not logic.is_valid_group(group):
                            print("Error: Invalid blood group \"" + group + "\".")
                            valid = False
                            break
                        elif not logic.is_valid_quantity(quantity_text):
                            print("Error: Invalid quantity \"" + quantity_text + "\". Quantity must be a positive number.")
                            valid = False
                            break
                            
                        items.append({"group": group, "quantity": int(quantity_text)})

                    if not valid or len(items) == 0:
                        print("Status: Rejected")
                        continue

                    # Everything checks out! Create ONE single request.
                    request_id = "R" + str(request_counter).zfill(3)
                    request_counter = request_counter + 1

                    request = {}
                    request["id"] = request_id
                    request["hospital"] = hospital
                    request["hospital_type"] = hospital_type
                    request["items"] = items
                    request["urgency"] = urgency
                    request["status"] = "Pending"

                    if urgency == "High":
                        # High urgency is decided right now
                        allocation = logic.allocate_request(stock, request)
                        print_bill(allocation)
                        if allocation["status"] == "Total" or allocation["status"] == "Partial":
                            stock = logic.issue_units(stock, allocation["unit_ids"])
                            session_log["revenue"] = session_log["revenue"] + allocation["total"]
                            session_log["fulfilled"] = session_log["fulfilled"] + 1
                        else:
                            session_log["rejected"] = session_log["rejected"] + 1
                    else:
                        # Mid/Low -- queue it
                        pending_requests.append(request)
                        print("Request " + request_id + " for " + str(len(items)) + " items (" + urgency + ") queued.")

        elif choice == 3:
            # --- Generate allocation plan (FR 4) ---
            # Only makes sense if there's at least one pending Mid/Low
            # request; otherwise there's nothing to simulate.
            has_mid_low = False
            for request in pending_requests:
                if request["status"] == "Pending" and (request["urgency"] == "Mid" or request["urgency"] == "Low"):
                    has_mid_low = True

            if not has_mid_low:
                print("No pending requests to process. Nothing generated.")
                current_plan = None
            else:
                # generate_plan() is a rehearsal only -- it never touches
                # the real stock, it just proposes what *would* happen.
                current_plan = logic.generate_plan(stock, pending_requests)
                print_plan(current_plan)

        elif choice == 4:
            # --- Confirm & issue plan (FR 5) ---
            if current_plan is None:
                print("Error: No allocation plan has been generated yet. Choose option 3 (Generate allocation plan) first.")
            elif not logic.is_plan_valid(stock, current_plan):
                # Something proposed in the plan is no longer Available
                # (expired, or issued elsewhere since the plan was made).
                print("Error: This plan is no longer valid (a proposed unit has expired or was issued elsewhere).")
                print("Regenerate the plan (option 3) before confirming.")
                current_plan = None
            else:
                # Plan is still good -- commit it for real.
                stock, session_log = logic.apply_plan(stock, current_plan, session_log)

                # Remove every request the plan just confirmed from the
                # pending queue, since they're no longer waiting.
                confirmed_ids = []
                for allocation in current_plan["allocations"]:
                    confirmed_ids.append(allocation["request_id"])

                new_pending = []
                for request in pending_requests:
                    if request["id"] not in confirmed_ids:
                        new_pending.append(request)
                pending_requests = new_pending

                print("Plan confirmed. Units issued, stock updated.")
                print("Total revenue this session: Rs " + str(session_log["revenue"]))

                current_plan = None

        elif choice == 5:
            # --- View progress report (FR 7) ---
            # Read-only -- doesn't change any state.
            report = logic.progress_report(session_log)
            print_progress_report(report)

        elif choice == 6:
            # --- View expired/wasted report (FR 8) ---
            # Also read-only.
            report = logic.wasted_report(session_log)
            print_wasted_report(report, stock)

        elif choice == 7:
            # Step 8: Exit chosen -- print Goodbye and stop the loop.
            # Final save on the way out, in case an earlier save failed
            # (for example, the file was open in Excel at the time).
            last_saved = save_if_changed(stock, last_saved)
            if stock != last_saved:
                print("Warning: the latest stock changes were NOT saved to stock.csv.")
            print("Goodbye")
            break

        # Single save point (2 of 2): after ANY action that may have
        # changed stock. New actions can't forget to save.
        last_saved = save_if_changed(stock, last_saved)

        # Step 7: Unless Exit was chosen, we fall through to the top of
        # the while loop and go back to step 2 automatically.


if __name__ == "__main__":
    main()