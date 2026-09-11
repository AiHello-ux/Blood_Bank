"""
blood_bank_logic.py

This file holds the "thinking" part of the program.
None of the functions in this file print anything or ask for input.
They just take some data in, and return some new data out.
That is why the design doc calls them "pure" functions.
"""

from datetime import datetime, timedelta


# The fixed list of the eight blood groups the bank deals with.
VALID_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# The fixed compatibility table from FR 3.
# Key = the blood group of a unit sitting in stock (the donor group).
# Value = the list of requested groups that unit is allowed to be issued to.
COMPATIBILITY = {
    "O-":  ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    "O+":  ["O+", "A+", "B+", "AB+"],
    "A-":  ["A-", "A+", "AB-", "AB+"],
    "A+":  ["A+", "AB+"],
    "B-":  ["B-", "B+", "AB-", "AB+"],
    "B+":  ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"],
}


def new_session_log():
    """Return a brand new, empty totals dict for a fresh session."""
    log = {}
    log["fulfilled"] = 0
    log["rejected"] = 0
    log["revenue"] = 0
    log["wasted_units"] = []
    log["wasted_value"] = 0
    return log


def is_valid_group(group):
    """True if group is one of the eight valid blood groups."""
    if group in VALID_GROUPS:
        return True
    return False


def is_valid_quantity(quantity):
    """
    True if quantity is text made only of digits (like "5"), and that
    number is greater than zero.
    quantity.isdigit() is False for things like "-3" (has a minus sign)
    or "abc" (not digits at all) or "" (empty), so those are caught
    before we ever try to turn it into a number.
    """
    if not quantity.isdigit():
        return False

    value = int(quantity)
    if value > 0:
        return True
    return False


def is_valid_urgency(urgency):
    """True if urgency is exactly 'High', 'Mid', or 'Low'."""
    if urgency == "High" or urgency == "Mid" or urgency == "Low":
        return True
    return False


def is_valid_hospital_type(hospital_type):
    """True if hospital_type is exactly 'Private' or 'Govt'."""
    if hospital_type == "Private" or hospital_type == "Govt":
        return True
    return False


def is_expired(expiry, today):
    """
    True if expiry is strictly before today.

    Both expiry and today are text like "2026-09-20". We turn each one
    into a real date using datetime.strptime, then Python can compare
    dates with a normal < sign, the same way you'd compare two numbers.
    We assume the text is always typed in the correct YYYY-MM-DD shape
    (the interface tells the user to type it that way).
    """
    expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
    today_date = datetime.strptime(today, "%Y-%m-%d").date()

    if expiry_date < today_date:
        return True
    return False


def is_within_shelf_life(expiry, today):
    """
    True if expiry is on or before (today + 35 days).
    """
    expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
    today_date = datetime.strptime(today, "%Y-%m-%d").date()

    cutoff_date = today_date + timedelta(days=35)

    if expiry_date <= cutoff_date:
        return True
    return False


def add_unit(stock, unit_id, group, expiry, today):
    """
    Return a NEW stock list with one more Available unit appended.
    If the date is already past, or more than 35 days out, the
    stock list is returned unchanged (unit not added).
    """
    if is_expired(expiry, today):
        return stock

    if not is_within_shelf_life(expiry, today):
        return stock

    new_stock = list(stock)
    new_unit = {}
    new_unit["id"] = unit_id
    new_unit["group"] = group
    new_unit["expiry"] = expiry
    new_unit["status"] = "Available"
    new_stock.append(new_unit)
    return new_stock


def expire_units(stock, today):
    """
    Return (new_stock, newly_wasted_units).
    Any Available unit whose date has passed becomes Wasted.
    """
    new_stock = []
    wasted_list = []

    for unit in stock:
        if unit["status"] == "Available" and is_expired(unit["expiry"], today):
            wasted_unit = {}
            wasted_unit["id"] = unit["id"]
            wasted_unit["group"] = unit["group"]
            wasted_unit["expiry"] = unit["expiry"]
            wasted_unit["status"] = "Wasted"
            new_stock.append(wasted_unit)
            wasted_list.append(wasted_unit)
        else:
            new_stock.append(unit)

    return (new_stock, wasted_list)


def _sort_key(unit):
    """Small helper used only for sorting: (expiry, id)."""
    return (unit["expiry"], unit["id"])


def compatible_available_units(stock, request_group):
    """
    Return every Available unit whose group can be issued to
    request_group, sorted soonest-expiry first, ties broken by
    unit id.
    """
    matches = []

    for unit in stock:
        if unit["status"] == "Available":
            donor_group = unit["group"]
            allowed_targets = COMPATIBILITY[donor_group]
            if request_group in allowed_targets:
                matches.append(unit)

    sorted_matches = sorted(matches, key=_sort_key)
    return sorted_matches


def per_unit_fee(group, urgency, hospital_type):
    """Compute one issued unit's fee using the FR 3 formula."""
    fee = 500

    if urgency == "High":
        fee = fee + 300
    elif urgency == "Mid":
        fee = fee + 100
    elif urgency == "Low":
        fee = fee + 0

    if group == "A-" or group == "B-" or group == "AB-" or group == "O-":
        fee = fee + 150

    if hospital_type == "Govt":
        fee = fee - 150

    return fee


def allocate_request(stock, request):
    """
    Decide one request against current stock.
    Never changes stock. Returns an allocation dict.
    """
    group = request["group"]
    quantity = request["quantity"]

    compatible_units = compatible_available_units(stock, group)

    if len(compatible_units) < quantity:
        result = {}
        result["status"] = "Rejected"
        result["request_id"] = request["id"]
        result["hospital"] = request["hospital"]
        result["hospital_type"] = request["hospital_type"]
        result["group"] = group
        result["quantity"] = quantity
        result["urgency"] = request["urgency"]
        result["available"] = len(compatible_units)
        result["needed"] = quantity
        return result

    # We only want the first "quantity" units from compatible_units
    # (they're already sorted soonest-expiry-first). Instead of slicing,
    # we build the list by hand: start a counter at 0, and keep grabbing
    # one item and adding 1 to the counter until we've got enough.
    chosen_units = []
    counter = 0
    while counter < quantity:
        chosen_units.append(compatible_units[counter])
        counter = counter + 1

    unit_ids = []
    fees = []
    units_detail = []

    for unit in chosen_units:
        fee = per_unit_fee(unit["group"], request["urgency"], request["hospital_type"])
        unit_ids.append(unit["id"])
        fees.append(fee)

        detail = {}
        detail["id"] = unit["id"]
        detail["group"] = unit["group"]
        detail["expiry"] = unit["expiry"]
        detail["fee"] = fee
        units_detail.append(detail)

    total = sum(fees) + 100

    result = {}
    result["status"] = "Fulfilled"
    result["request_id"] = request["id"]
    result["hospital"] = request["hospital"]
    result["hospital_type"] = request["hospital_type"]
    result["group"] = group
    result["quantity"] = quantity
    result["urgency"] = request["urgency"]
    result["unit_ids"] = unit_ids
    result["fees"] = fees
    result["units"] = units_detail
    result["total"] = total
    return result


def issue_units(stock, unit_ids):
    """Return a NEW stock list with the given unit ids marked Issued."""
    new_stock = []

    for unit in stock:
        if unit["id"] in unit_ids:
            issued_unit = {}
            issued_unit["id"] = unit["id"]
            issued_unit["group"] = unit["group"]
            issued_unit["expiry"] = unit["expiry"]
            issued_unit["status"] = "Issued"
            new_stock.append(issued_unit)
        else:
            new_stock.append(unit)

    return new_stock


def sort_for_plan(requests):
    """Return pending Mid/Low requests: all Mid first, then all Low."""
    mid_list = []
    low_list = []

    for request in requests:
        if request["status"] == "Pending" and request["urgency"] == "Mid":
            mid_list.append(request)
        elif request["status"] == "Pending" and request["urgency"] == "Low":
            low_list.append(request)

    combined = mid_list + low_list
    return combined


def generate_plan(stock, requests):
    """
    Simulate allocate_request over every pending Mid/Low request,
    in sort_for_plan order. Never changes the real stock.
    """
    working_stock = stock
    ordered_requests = sort_for_plan(requests)

    allocations = []
    proposed_revenue = 0

    for request in ordered_requests:
        allocation = allocate_request(working_stock, request)
        allocations.append(allocation)

        if allocation["status"] == "Fulfilled":
            working_stock = issue_units(working_stock, allocation["unit_ids"])
            proposed_revenue = proposed_revenue + allocation["total"]

    plan = {}
    plan["allocations"] = allocations
    plan["proposed_revenue"] = proposed_revenue
    return plan


def is_plan_valid(stock, plan):
    """
    True if every unit proposed in the plan's Fulfilled allocations
    is still Available in stock right now.
    """
    for allocation in plan["allocations"]:
        if allocation["status"] == "Fulfilled":
            for unit_id in allocation["unit_ids"]:
                found_available = False
                for unit in stock:
                    if unit["id"] == unit_id and unit["status"] == "Available":
                        found_available = True
                if not found_available:
                    return False
    return True


def apply_plan(stock, plan, session_log):
    """
    Commit a plan. Assumes the caller already checked is_plan_valid.
    Returns (new_stock, new_session_log).
    """
    new_stock = stock

    new_session_log = {}
    new_session_log["fulfilled"] = session_log["fulfilled"]
    new_session_log["rejected"] = session_log["rejected"]
    new_session_log["revenue"] = session_log["revenue"]
    new_session_log["wasted_units"] = list(session_log["wasted_units"])
    new_session_log["wasted_value"] = session_log["wasted_value"]

    for allocation in plan["allocations"]:
        if allocation["status"] == "Fulfilled":
            new_stock = issue_units(new_stock, allocation["unit_ids"])
            new_session_log["revenue"] = new_session_log["revenue"] + allocation["total"]
            new_session_log["fulfilled"] = new_session_log["fulfilled"] + 1
        else:
            new_session_log["rejected"] = new_session_log["rejected"] + 1

    return (new_stock, new_session_log)


def wasted_report(session_log):
    """Return the count and total value of all wasted units so far."""
    report = {}
    report["count"] = len(session_log["wasted_units"])
    report["value"] = session_log["wasted_value"]
    return report


def progress_report(session_log):
    """Return total handled, fulfilled, rejected, and revenue so far."""
    report = {}
    report["handled"] = session_log["fulfilled"] + session_log["rejected"]
    report["fulfilled"] = session_log["fulfilled"]
    report["rejected"] = session_log["rejected"]
    report["revenue"] = session_log["revenue"]
    return report
