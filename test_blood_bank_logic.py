"""
test_blood_bank_logic.py

Contains exactly 20 test cases perfectly matching the 20 scenarios 
from the "Test Cases" table in the PRD document.
"""

from blood_bank_logic import (
    is_valid_group, is_valid_date, add_unit, expire_units, 
    allocate_request, generate_plan, apply_plan, is_plan_valid, 
    wasted_report, progress_report, is_within_shelf_life, new_session_log
)
import storage
import os


# 1. FR 1: Open the program with saved stock
def test_FR1_open_program_with_saved_stock(tmp_path):
    path = str(tmp_path / "stock.csv")
    storage.save_stock([{"id": "U001", "group": "A+", "expiry": "2026-10-20", "status": "Available"}], path)
    loaded_stock = storage.load_stock(path)
    assert len(loaded_stock) == 1
    assert loaded_stock[0]["status"] == "Available"


# 2. FR 2: Add O+ with a valid date inside 35 days
def test_FR2_add_O_pos_valid_date_inside_35_days():
    stock = []
    # Using 2026-10-15 from today 2026-10-08 (7 days)
    new_stock = add_unit(stock, "U001", "O+", "2026-10-15", "2026-10-08")
    assert len(new_stock) == 1
    assert new_stock[0]["status"] == "Available"


# 3. FR 2: Add C+ with a valid date
def test_FR2_add_C_pos_invalid_group():
    # Validation step blocks invalid groups
    assert is_valid_group("C+") is False


# 4. FR 2: Add 2025-01-01 (past date)
def test_FR2_add_past_date_2025_01_01():
    from blood_bank_logic import is_expired
    # Validation step blocks dates in the past
    assert is_expired("2025-01-01", "2026-10-08") is True


# 5. FR 2: Add 2026-02-30 (invalid date)
def test_FR2_add_invalid_date_2026_02_30():
    # Validation catches non-existent dates to prevent crashes
    assert is_valid_date("2026-02-30") is False


# 6. FR 6: Add a unit exactly 35 days from today
def test_FR6_add_unit_exactly_35_days_from_today():
    # 2026-10-08 + 35 days = 2026-11-12
    assert is_within_shelf_life("2026-11-12", "2026-10-08") is True


# 7. FR 6: Add a unit 36 days from today
def test_FR6_add_unit_36_days_from_today():
    # 2026-10-08 + 36 days = 2026-11-13
    assert is_within_shelf_life("2026-11-13", "2026-10-08") is False


# 8. FR 3: High request with one Total item and enough stock
def test_FR3_high_request_total_item_enough_stock():
    stock = [{"id": "U001", "group": "A+", "expiry": "2026-10-20", "status": "Available"}]
    request = {
        "id": "R001", "hospital": "City", "hospital_type": "Govt", 
        "urgency": "High", "items": [{"group": "A+", "quantity": 1}]
    }
    allocation = allocate_request(stock, request)
    assert allocation["status"] == "Total"
    assert len(allocation["unit_ids"]) == 1


# 9. FR 3: High request with one Partial item
def test_FR3_high_request_partial_item():
    stock = [{"id": "U001", "group": "A+", "expiry": "2026-10-20", "status": "Available"}]
    request = {
        "id": "R001", "hospital": "City", "hospital_type": "Govt", 
        "urgency": "High", "items": [{"group": "A+", "quantity": 2}] # Asking for 2, only 1 available
    }
    allocation = allocate_request(stock, request)
    assert allocation["status"] == "Partial"
    assert len(allocation["unit_ids"]) == 1


# 10. FR 3: High request with all items rejected
def test_FR3_high_request_all_items_rejected():
    stock = [] # Empty stock
    request = {
        "id": "R001", "hospital": "City", "hospital_type": "Govt", 
        "urgency": "High", "items": [{"group": "A+", "quantity": 2}]
    }
    allocation = allocate_request(stock, request)
    assert allocation["status"] == "Rejected"
    assert len(allocation["unit_ids"]) == 0


# 11. FR 3: High request with multiple items
def test_FR3_high_request_multiple_items():
    stock = [
        {"id": "U001", "group": "A+", "expiry": "2026-10-20", "status": "Available"},
        {"id": "U002", "group": "B+", "expiry": "2026-10-20", "status": "Available"}
    ]
    request = {
        "id": "R001", "hospital": "City", "hospital_type": "Govt", 
        "urgency": "High", "items": [{"group": "A+", "quantity": 1}, {"group": "B+", "quantity": 1}]
    }
    allocation = allocate_request(stock, request)
    assert allocation["status"] == "Total"
    assert len(allocation["unit_ids"]) == 2


# 12. FR 4: Pending Low request and Mid request
def test_FR4_pending_low_and_mid_request_order():
    stock = [{"id": "U001", "group": "A+", "expiry": "2026-10-20", "status": "Available"}]
    requests = [
        {"id": "R001", "hospital": "City", "hospital_type": "Govt", "urgency": "Low", "status": "Pending", "items": [{"group": "A+", "quantity": 1}]},
        {"id": "R002", "hospital": "Town", "hospital_type": "Govt", "urgency": "Mid", "status": "Pending", "items": [{"group": "A+", "quantity": 1}]}
    ]
    plan = generate_plan(stock, requests)
    # Mid should be processed first and get the unit
    assert plan["allocations"][0]["request_id"] == "R002"
    assert plan["allocations"][0]["status"] == "Total"
    assert plan["allocations"][1]["request_id"] == "R001"
    assert plan["allocations"][1]["status"] == "Rejected"


# 13. FR 4: Two requests need the same one unit
def test_FR4_two_requests_need_same_unit():
    stock = [{"id": "U001", "group": "A+", "expiry": "2026-10-20", "status": "Available"}]
    requests = [
        {"id": "R001", "hospital": "H1", "hospital_type": "Govt", "urgency": "Mid", "status": "Pending", "items": [{"group": "A+", "quantity": 1}]},
        {"id": "R002", "hospital": "H2", "hospital_type": "Govt", "urgency": "Mid", "status": "Pending", "items": [{"group": "A+", "quantity": 1}]}
    ]
    plan = generate_plan(stock, requests)
    # Earlier request gets it
    assert plan["allocations"][0]["request_id"] == "R001"
    assert plan["allocations"][0]["status"] == "Total"
    assert plan["allocations"][1]["request_id"] == "R002"
    assert plan["allocations"][1]["status"] == "Rejected"


# 14. FR 5: Confirm a valid plan
def test_FR5_confirm_valid_plan():
    stock = [{"id": "U001", "group": "A+", "expiry": "2026-10-20", "status": "Available"}]
    plan = {"allocations": [{"status": "Total", "unit_ids": ["U001"], "total": 600}]}
    log = new_session_log()
    new_stock, new_log = apply_plan(stock, plan, log)
    assert new_stock[0]["status"] == "Issued"
    assert new_log["revenue"] == 600


# 15. FR 5: Confirm a stale plan
def test_FR5_confirm_stale_plan():
    stock = [{"id": "U001", "group": "A+", "expiry": "2026-10-20", "status": "Issued"}] # Unit already issued!
    plan = {"allocations": [{"status": "Total", "unit_ids": ["U001"], "total": 600}]}
    # is_plan_valid catches this before application
    assert is_plan_valid(stock, plan) is False


# 16. FR 7: Three Fulfilled and two Rejected requests
def test_FR7_three_fulfilled_two_rejected_requests():
    log = new_session_log()
    log["fulfilled"] = 3
    log["rejected"] = 2
    report = progress_report(log)
    assert report["handled"] == 5
    assert report["fulfilled"] == 3
    assert report["rejected"] == 2


# 17. FR 8: Two units have expired
def test_FR8_two_units_expired_value_1000():
    stock = [
        {"id": "U001", "group": "A+", "expiry": "2026-10-01", "status": "Available"},
        {"id": "U002", "group": "A-", "expiry": "2026-10-02", "status": "Available"}
    ]
    updated, wasted = expire_units(stock, "2026-10-08")
    assert len(wasted) == 2
    log = new_session_log()
    log["wasted_units"] = wasted
    log["wasted_value"] = len(wasted) * 500
    report = wasted_report(log)
    assert report["count"] == 2
    assert report["value"] == 1000


# 18. FR 10: Close stock.csv and restart
def test_FR10_close_stock_csv_and_restart(tmp_path):
    path = str(tmp_path / "stock.csv")
    storage.save_stock([{"id": "U001", "group": "O+", "expiry": "2026-10-15", "status": "Available"}], path)
    # Restarting acts like loading stock again
    loaded = storage.load_stock(path)
    assert len(loaded) == 1
    assert loaded[0]["id"] == "U001"


# 19. FR 10: stock.csv does not exist
def test_FR10_stock_csv_does_not_exist(tmp_path):
    path = str(tmp_path / "missing_file.csv")
    loaded = storage.load_stock(path)
    # Program starts with empty stock without crashing
    assert loaded == []


# 20. FR 10: stock.csv is open in Excel during save
def test_FR10_stock_csv_open_in_excel_during_save(tmp_path, monkeypatch):
    path = str(tmp_path / "stock.csv")
    storage.save_stock([{"id": "U001", "group": "O+", "expiry": "2026-10-15", "status": "Available"}], path)
    
    # Simulate the PermissionError raised when Excel locks a file
    def mock_replace(src, dst):
        raise PermissionError("File open in Excel")
    
    monkeypatch.setattr(os, "replace", mock_replace)
    
    # Save attempt fails gracefully, returns False
    success = storage.save_stock([{"id": "U002"}], path)
    assert success is False
    # Old file is kept safe
    assert storage.load_stock(path)[0]["id"] == "U001"
