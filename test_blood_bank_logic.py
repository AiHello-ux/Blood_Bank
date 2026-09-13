"""Unit tests for blood_bank_logic.py"""

from blood_bank_logic import (
    new_session_log,
    is_valid_group,
    is_valid_quantity,
    is_valid_urgency,
    is_valid_hospital_type,
    is_expired,
    is_within_shelf_life,
    add_unit,
    expire_units,
    compatible_available_units,
    per_unit_fee,
    allocate_request,
    issue_units,
    sort_for_plan,
    generate_plan,
    is_plan_valid,
    apply_plan,
    wasted_report,
    progress_report,
)


# --- new_session_log ---

def test_new_session_log_starts_at_zero():
    log = new_session_log()
    assert log["fulfilled"] == 0
    assert log["rejected"] == 0
    assert log["revenue"] == 0
    assert log["wasted_units"] == []
    assert log["wasted_value"] == 0


# --- is_valid_group ---

def test_is_valid_group_true_for_real_group():
    assert is_valid_group("O+") is True

def test_is_valid_group_false_for_fake_group():
    assert is_valid_group("C+") is False


# --- is_valid_quantity ---

def test_is_valid_quantity_true_for_positive_number():
    assert is_valid_quantity("5") is True

def test_is_valid_quantity_false_for_negative():
    assert is_valid_quantity("-3") is False

def test_is_valid_quantity_false_for_zero():
    assert is_valid_quantity("0") is False

def test_is_valid_quantity_false_for_non_numeric():
    assert is_valid_quantity("abc") is False


# --- is_valid_urgency ---

def test_is_valid_urgency_true_for_high():
    assert is_valid_urgency("High") is True

def test_is_valid_urgency_false_for_bad_value():
    assert is_valid_urgency("Urgent") is False


# --- is_valid_hospital_type ---

def test_is_valid_hospital_type_true_for_govt():
    assert is_valid_hospital_type("Govt") is True

def test_is_valid_hospital_type_false_for_bad_value():
    assert is_valid_hospital_type("Clinic") is False


# --- is_expired ---

def test_is_expired_true_for_past_date():
    assert is_expired("2025-01-01", "2026-09-11") is True

def test_is_expired_false_for_future_date():
    assert is_expired("2026-10-01", "2026-09-11") is False

def test_is_expired_false_for_today():
    # EC12: a unit expiring exactly today is not treated as expired yet.
    assert is_expired("2026-09-11", "2026-09-11") is False


# --- is_within_shelf_life ---

def test_is_within_shelf_life_true_for_35_days_out():
    # EC17: exactly 35 days from today is the accepted boundary.
    assert is_within_shelf_life("2026-10-16", "2026-09-11") is True

def test_is_within_shelf_life_false_for_36_days_out():
    # EC18: one day past the cutoff must fail.
    assert is_within_shelf_life("2026-10-17", "2026-09-11") is False


# --- add_unit ---

def test_add_unit_adds_valid_unit():
    stock = []
    stock = add_unit(stock, "U001", "O+", "2026-10-01", "2026-09-11")
    assert len(stock) == 1
    assert stock[0]["id"] == "U001"
    assert stock[0]["group"] == "O+"
    assert stock[0]["status"] == "Available"

def test_add_unit_rejects_past_date():
    stock = []
    stock = add_unit(stock, "U001", "A+", "2025-01-01", "2026-09-11")
    assert stock == []

def test_add_unit_rejects_date_too_far_out():
    stock = []
    stock = add_unit(stock, "U001", "O+", "2026-12-15", "2026-09-11")
    assert stock == []

def test_add_unit_does_not_mutate_original_list():
    # add_unit must return a NEW list, not change the one passed in.
    original = []
    result = add_unit(original, "U001", "O+", "2026-10-01", "2026-09-11")
    assert original == []
    assert len(result) == 1


# --- expire_units ---

def test_expire_units_marks_past_date_as_wasted():
    stock = [{"id": "U005", "group": "A+", "expiry": "2026-09-08", "status": "Available"}]
    new_stock, wasted = expire_units(stock, "2026-09-11")
    assert new_stock[0]["status"] == "Wasted"
    assert len(wasted) == 1
    assert wasted[0]["id"] == "U005"

def test_expire_units_leaves_future_units_alone():
    stock = [{"id": "U001", "group": "O+", "expiry": "2026-10-01", "status": "Available"}]
    new_stock, wasted = expire_units(stock, "2026-09-11")
    assert new_stock[0]["status"] == "Available"
    assert wasted == []

def test_expire_units_leaves_today_expiry_available():
    # EC12 again, this time through expire_units directly.
    stock = [{"id": "U020", "group": "A+", "expiry": "2026-09-11", "status": "Available"}]
    new_stock, wasted = expire_units(stock, "2026-09-11")
    assert new_stock[0]["status"] == "Available"
    assert wasted == []


# --- compatible_available_units ---

def test_compatible_available_units_o_negative_matches_everything():
    stock = [{"id": "U001", "group": "O-", "expiry": "2026-09-20", "status": "Available"}]
    matches = compatible_available_units(stock, "AB+")
    assert len(matches) == 1

def test_compatible_available_units_ab_positive_matches_only_itself():
    stock = [{"id": "U001", "group": "AB+", "expiry": "2026-09-20", "status": "Available"}]
    assert compatible_available_units(stock, "A+") == []
    assert len(compatible_available_units(stock, "AB+")) == 1

def test_compatible_available_units_ignores_non_available_status():
    stock = [{"id": "U001", "group": "O-", "expiry": "2026-09-20", "status": "Issued"}]
    assert compatible_available_units(stock, "A+") == []

def test_compatible_available_units_sorted_soonest_expiry_first():
    stock = [
        {"id": "U002", "group": "A+", "expiry": "2026-10-05", "status": "Available"},
        {"id": "U001", "group": "A+", "expiry": "2026-09-18", "status": "Available"},
    ]
    matches = compatible_available_units(stock, "A+")
    assert matches[0]["id"] == "U001"
    assert matches[1]["id"] == "U002"

def test_compatible_available_units_ties_broken_by_id():
    stock = [
        {"id": "U002", "group": "A+", "expiry": "2026-09-18", "status": "Available"},
        {"id": "U001", "group": "A+", "expiry": "2026-09-18", "status": "Available"},
    ]
    matches = compatible_available_units(stock, "A+")
    assert matches[0]["id"] == "U001"


# --- per_unit_fee ---

def test_per_unit_fee_high_urgency_rh_positive_private():
    # 500 base + 300 high + 0 group + 0 discount
    assert per_unit_fee("O+", "High", "Private") == 800

def test_per_unit_fee_high_urgency_rh_negative_private():
    # 500 base + 300 high + 150 group + 0 discount = 950 (matches FR3 example)
    assert per_unit_fee("O-", "High", "Private") == 950

def test_per_unit_fee_low_urgency_rh_positive_govt():
    # 500 base + 0 low + 0 group - 150 govt discount
    assert per_unit_fee("A+", "Low", "Govt") == 350

def test_per_unit_fee_mid_urgency_rh_negative_govt():
    # 500 base + 100 mid + 150 group - 150 govt discount
    assert per_unit_fee("O-", "Mid", "Govt") == 600


# --- allocate_request ---

def test_allocate_request_fulfilled_when_enough_stock():
    stock = [
        {"id": "U001", "group": "O-", "expiry": "2026-09-20", "status": "Available"},
        {"id": "U002", "group": "O-", "expiry": "2026-09-25", "status": "Available"},
    ]
    request = {"id": "R001", "hospital": "City Hospital", "hospital_type": "Govt",
               "group": "O-", "quantity": 2, "urgency": "High"}
    result = allocate_request(stock, request)
    assert result["status"] == "Fulfilled"
    assert result["total"] == 1700  # matches the PRD's own worked example

def test_allocate_request_rejected_when_not_enough_stock():
    stock = [{"id": "U001", "group": "O+", "expiry": "2026-09-20", "status": "Available"}]
    request = {"id": "R001", "hospital": "City Hospital", "hospital_type": "Private",
               "group": "O+", "quantity": 5, "urgency": "High"}
    result = allocate_request(stock, request)
    assert result["status"] == "Rejected"
    assert result["available"] == 1
    assert result["needed"] == 5

def test_allocate_request_rejected_with_zero_compatible_stock():
    stock = []
    request = {"id": "R001", "hospital": "City Hospital", "hospital_type": "Private",
               "group": "AB-", "quantity": 1, "urgency": "High"}
    result = allocate_request(stock, request)
    assert result["status"] == "Rejected"
    assert result["available"] == 0

def test_allocate_request_picks_soonest_expiry_units():
    stock = [
        {"id": "U002", "group": "A+", "expiry": "2026-10-05", "status": "Available"},
        {"id": "U001", "group": "A+", "expiry": "2026-09-18", "status": "Available"},
    ]
    request = {"id": "R001", "hospital": "District Hospital", "hospital_type": "Govt",
               "group": "A+", "quantity": 1, "urgency": "Low"}
    result = allocate_request(stock, request)
    assert result["unit_ids"] == ["U001"]

def test_allocate_request_never_changes_stock():
    stock = [{"id": "U001", "group": "O+", "expiry": "2026-09-20", "status": "Available"}]
    request = {"id": "R001", "hospital": "City Hospital", "hospital_type": "Private",
               "group": "O+", "quantity": 1, "urgency": "High"}
    allocate_request(stock, request)
    assert stock[0]["status"] == "Available"


# --- issue_units ---

def test_issue_units_marks_given_ids_issued():
    stock = [{"id": "U001", "group": "O+", "expiry": "2026-09-20", "status": "Available"}]
    new_stock = issue_units(stock, ["U001"])
    assert new_stock[0]["status"] == "Issued"

def test_issue_units_leaves_other_units_alone():
    stock = [
        {"id": "U001", "group": "O+", "expiry": "2026-09-20", "status": "Available"},
        {"id": "U002", "group": "O+", "expiry": "2026-09-22", "status": "Available"},
    ]
    new_stock = issue_units(stock, ["U001"])
    assert new_stock[1]["status"] == "Available"


# --- sort_for_plan ---

def test_sort_for_plan_mid_before_low():
    requests = [
        {"id": "R001", "status": "Pending", "urgency": "Low"},
        {"id": "R002", "status": "Pending", "urgency": "Mid"},
    ]
    ordered = sort_for_plan(requests)
    assert ordered[0]["id"] == "R002"
    assert ordered[1]["id"] == "R001"

def test_sort_for_plan_ignores_non_pending_and_high():
    requests = [
        {"id": "R001", "status": "Fulfilled", "urgency": "Mid"},
        {"id": "R002", "status": "Pending", "urgency": "High"},
        {"id": "R003", "status": "Pending", "urgency": "Low"},
    ]
    ordered = sort_for_plan(requests)
    assert len(ordered) == 1
    assert ordered[0]["id"] == "R003"


# --- generate_plan ---

def test_generate_plan_matches_prd_example():
    stock = [
        {"id": "U007", "group": "A+", "expiry": "2026-09-18", "status": "Available"},
        {"id": "U012", "group": "A+", "expiry": "2026-10-05", "status": "Available"},
    ]
    requests = [
        {"id": "R1", "hospital": "District Hospital", "hospital_type": "Govt",
         "group": "A+", "quantity": 2, "urgency": "Low", "status": "Pending"},
        {"id": "R2", "hospital": "Metro Clinic", "hospital_type": "Private",
         "group": "AB-", "quantity": 2, "urgency": "Mid", "status": "Pending"},
    ]
    plan = generate_plan(stock, requests)
    assert plan["proposed_revenue"] == 800
    assert plan["allocations"][0]["request_id"] == "R2"  # Mid processed first
    assert plan["allocations"][0]["status"] == "Rejected"
    assert plan["allocations"][1]["request_id"] == "R1"
    assert plan["allocations"][1]["status"] == "Fulfilled"

def test_generate_plan_does_not_touch_real_stock():
    stock = [{"id": "U001", "group": "A+", "expiry": "2026-09-20", "status": "Available"}]
    requests = [{"id": "R1", "hospital": "X", "hospital_type": "Private",
                 "group": "A+", "quantity": 1, "urgency": "Low", "status": "Pending"}]
    generate_plan(stock, requests)
    assert stock[0]["status"] == "Available"

def test_generate_plan_later_request_loses_out_on_same_units():
    # Two Low requests for the same group, only one unit exists.
    stock = [{"id": "U001", "group": "A+", "expiry": "2026-09-20", "status": "Available"}]
    requests = [
        {"id": "R1", "hospital": "A", "hospital_type": "Private", "group": "A+",
         "quantity": 1, "urgency": "Low", "status": "Pending"},
        {"id": "R2", "hospital": "B", "hospital_type": "Private", "group": "A+",
         "quantity": 1, "urgency": "Low", "status": "Pending"},
    ]
    plan = generate_plan(stock, requests)
    assert plan["allocations"][0]["status"] == "Fulfilled"
    assert plan["allocations"][1]["status"] == "Rejected"


# --- is_plan_valid ---

def test_is_plan_valid_true_when_units_still_available():
    stock = [{"id": "U007", "group": "A+", "expiry": "2026-09-18", "status": "Available"}]
    plan = {"allocations": [{"status": "Fulfilled", "unit_ids": ["U007"]}]}
    assert is_plan_valid(stock, plan) is True

def test_is_plan_valid_false_when_unit_no_longer_available():
    # EC13: a proposed unit has since expired / been issued elsewhere.
    stock = [{"id": "U007", "group": "A+", "expiry": "2026-09-18", "status": "Wasted"}]
    plan = {"allocations": [{"status": "Fulfilled", "unit_ids": ["U007"]}]}
    assert is_plan_valid(stock, plan) is False

def test_is_plan_valid_ignores_rejected_allocations():
    stock = []
    plan = {"allocations": [{"status": "Rejected", "available": 0, "needed": 1}]}
    assert is_plan_valid(stock, plan) is True


# --- apply_plan ---

def test_apply_plan_issues_units_and_updates_revenue():
    stock = [{"id": "U007", "group": "A+", "expiry": "2026-09-18", "status": "Available"}]
    plan = {"allocations": [{"status": "Fulfilled", "unit_ids": ["U007"], "total": 800}]}
    session_log = new_session_log()
    new_stock, new_log = apply_plan(stock, plan, session_log)
    assert new_stock[0]["status"] == "Issued"
    assert new_log["revenue"] == 800
    assert new_log["fulfilled"] == 1

def test_apply_plan_counts_rejected_allocations():
    stock = []
    plan = {"allocations": [{"status": "Rejected", "available": 0, "needed": 1}]}
    session_log = new_session_log()
    _, new_log = apply_plan(stock, plan, session_log)
    assert new_log["rejected"] == 1
    assert new_log["fulfilled"] == 0


# --- wasted_report ---

def test_wasted_report_reads_count_and_value():
    session_log = new_session_log()
    session_log["wasted_units"] = [{"id": "U002"}, {"id": "U008"}]
    session_log["wasted_value"] = 1000
    report = wasted_report(session_log)
    assert report["count"] == 2
    assert report["value"] == 1000

def test_wasted_report_fresh_session_is_zero():
    report = wasted_report(new_session_log())
    assert report["count"] == 0
    assert report["value"] == 0


# --- progress_report ---

def test_progress_report_adds_fulfilled_and_rejected():
    session_log = new_session_log()
    session_log["fulfilled"] = 3
    session_log["rejected"] = 2
    session_log["revenue"] = 3600
    report = progress_report(session_log)
    assert report["handled"] == 5
    assert report["fulfilled"] == 3
    assert report["rejected"] == 2
    assert report["revenue"] == 3600

def test_progress_report_fresh_session_is_zero():
    report = progress_report(new_session_log())
    assert report["handled"] == 0
    assert report["fulfilled"] == 0
    assert report["rejected"] == 0
    assert report["revenue"] == 0
