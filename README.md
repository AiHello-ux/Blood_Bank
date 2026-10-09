# 🩸 Blood Bank Unit Allocation System

A CLI-based blood bank management system built with Python for staff members to manage blood inventory, process hospital requests, and generate allocation plans.

## 📋 Table of Contents

- [About](#about)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Blood Compatibility Table](#blood-compatibility-table)
- [Pricing Structure](#pricing-structure)
- [Functional Requirements](#functional-requirements)
- [Testing](#testing)

## About

This project is a **Command-Line Interface (CLI)** application designed for blood bank staff members to:
- Track blood inventory with expiry dates
- Process hospital requests with urgency-based prioritization
- Allocate compatible blood units using a smart matching algorithm
- Generate itemized bills with pricing based on hospital type and urgency
- Maintain persistent records via CSV storage

The system follows **Modular Programming** principles, splitting the code into three files with clear separation of concerns.

## Features

- ✅ **Multi-unit stock entry** — Add multiple blood bags in one command
- ✅ **Multi-group requests** — Hospitals can request multiple blood groups at once (e.g., `A+ 2, B+ 4`)
- ✅ **Smart compatibility matching** — Automatically finds compatible donors (e.g., O- matches all groups)
- ✅ **Nearest-expiry-first allocation** — Always issues the soonest-to-expire units first to reduce waste
- ✅ **Partial fulfillment** — If 3 units are requested but only 2 are available, the system issues 2 (Partial) instead of rejecting the entire order
- ✅ **Urgency-based processing** — High urgency is processed immediately; Mid/Low are queued for batch planning
- ✅ **Differential pricing** — Private hospitals pay surcharges; Govt hospitals get free transportation
- ✅ **Automatic expiry detection** — Expired units are automatically marked as Wasted on every refresh
- ✅ **35-day shelf life validation** — Rejects stock with expiry dates beyond 35 days
- ✅ **Excel-safe CSV storage** — Safe file writing with PermissionError handling (won't crash if Excel has the file open)
- ✅ **Progress & waste reports** — Track fulfilled/rejected requests and financial losses from expired units

## Project Structure

```
blood-bank-allocation/
│
├── main.py                    # CLI interface, menus, input/output (10 functions)
├── blood_bank_logic.py        # Core logic, matching, pricing (21 functions)
├── storage.py                 # CSV read/write operations (4 functions)
├── test_blood_bank_logic.py   # 20 test cases matching PRD scenarios
├── stock.csv                  # Persistent blood inventory (auto-generated)
└── README.md                  # This file
```

### Architecture

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────┐
│   main.py   │────▶│  blood_bank_logic.py  │     │ storage.py  │
│  (UI Layer) │     │    (Logic Layer)      │     │ (Data Layer)│
│             │◀────│                       │     │             │
│ - Menus     │     │ - Compatibility       │     │ - save_stock│
│ - Input     │     │ - Fee calculation     │     │ - load_stock│
│ - Bills     │     │ - Allocation engine   │     │             │
└─────────────┘     └───────────────────────┘     └─────────────┘
       │                                                 ▲
       └─────────────────────────────────────────────────┘
                        Reads/Writes stock.csv
```

## Installation

### Prerequisites
- Python 3.7 or higher
- `pytest` (for running tests)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/blood-bank-allocation.git
cd blood-bank-allocation

# Install pytest (if not already installed)
pip install pytest
```

## Usage

### Running the Application

```bash
python main.py
```

### Menu Options

```
1. Add stock           - Add blood units with expiry dates
2. Submit request      - Process a hospital blood request
3. Generate plan       - Create allocation plan for queued requests
4. Confirm & issue     - Execute the generated plan
5. Progress report     - View fulfilled/rejected/revenue summary
6. Wasted report       - View expired units and financial loss
7. Exit                - Save and quit
```

### Quick Start Example

**Step 1: Add stock**
```
Choose an option: 1
Enter group and expiry date: A+ 2026-10-25, A+ 2026-10-28, B+ 2026-10-20, O- 2026-11-02
```

**Step 2: Submit a hospital request**
```
Choose an option: 2
Hospital name: Apollo Hospital
Hospital type (Private/Govt): Private
Urgency (High/Mid/Low): High
Enter blood groups and quantities: A+ 2, B+ 1
```

**Step 3: View the generated bill**
```
-------- BILL --------
Request: R001 (Apollo Hospital)
 - A+: Total (2 of 2 issued)
 - B+: Total (1 of 1 issued)
Unit ID   Group   Expiry       Fee
U001      A+      2026-10-25   Rs 950
U002      A+      2026-10-28   Rs 950
U003      B+      2026-10-20   Rs 950
-----------------------
Transportation Charge: Rs 100
-----------------------
TOTAL AMOUNT: Rs 2950
Overall Status: Total
-----------------------
```

## Blood Compatibility Table

The system uses real-world blood group compatibility rules:

| Donor Group | Can Be Given To |
|:-----------:|:----------------|
| **O-**  | A+, A-, B+, B-, AB+, AB-, O+, O- *(Universal Donor)* |
| **O+**  | O+, A+, B+, AB+ |
| **A-**  | A-, A+, AB-, AB+ |
| **A+**  | A+, AB+ |
| **B-**  | B-, B+, AB-, AB+ |
| **B+**  | B+, AB+ |
| **AB-** | AB-, AB+ |
| **AB+** | AB+ only *(Universal Recipient)* |

## Pricing Structure

### Per-Unit Fee Formula

```
Fee = Base (Rs 500)
    + Urgency Surcharge (High: +300, Mid: +100, Low: +0)
    + Rh-Negative Surcharge (+150 for A-, B-, AB-, O-)
    + Private Hospital Surcharge (+150)
```

### Transportation Fee (Per Bill)
- **Private:** Rs 100
- **Govt:** Rs 0 (Free)

### Price Table — Govt Hospital

| Blood Group | Low | Mid | High |
|:-----------:|:---:|:---:|:----:|
| A+, B+, AB+, O+ | Rs 500 | Rs 600 | Rs 800 |
| A-, B-, AB-, O-  | Rs 650 | Rs 750 | Rs 950 |

### Price Table — Private Hospital

| Blood Group | Low | Mid | High |
|:-----------:|:---:|:---:|:----:|
| A+, B+, AB+, O+ | Rs 650 | Rs 750 | Rs 950 |
| A-, B-, AB-, O-  | Rs 800 | Rs 900 | Rs 1,100 |

## Functional Requirements

| FR | Description | Menu Option |
|:--:|:------------|:-----------:|
| FR 1 | Display stock table and menu | Auto |
| FR 2 | Add blood stock units with validation | Option 1 |
| FR 3 | Submit hospital request with pricing | Option 2 |
| FR 4 | Generate allocation plan for Mid/Low requests | Option 3 |
| FR 5 | Confirm and issue the allocation plan | Option 4 |
| FR 6 | Auto-expire units & enforce 35-day shelf life | Auto |
| FR 7 | View progress report (fulfilled/rejected/revenue) | Option 5 |
| FR 8 | View expired/wasted units report | Option 6 |
| FR 9 | Return to menu after every action (loop) | Auto |
| FR 10 | Persistent CSV storage with Excel-safe writing | Auto |

## Testing

The project includes **20 test cases** mapped to the PRD test scenarios.

### Run All Tests

```bash
python -m pytest test_blood_bank_logic.py
```

### Run with Verbose Output

```bash
python -m pytest -v test_blood_bank_logic.py
```

### Expected Output

```
test_blood_bank_logic.py::test_FR1_open_program_with_saved_stock PASSED
test_blood_bank_logic.py::test_FR2_add_O_pos_valid_date_inside_35_days PASSED
test_blood_bank_logic.py::test_FR2_add_C_pos_invalid_group PASSED
test_blood_bank_logic.py::test_FR2_add_past_date_2025_01_01 PASSED
test_blood_bank_logic.py::test_FR2_add_invalid_date_2026_02_30 PASSED
test_blood_bank_logic.py::test_FR6_add_unit_exactly_35_days_from_today PASSED
test_blood_bank_logic.py::test_FR6_add_unit_36_days_from_today PASSED
test_blood_bank_logic.py::test_FR3_high_request_total_item_enough_stock PASSED
test_blood_bank_logic.py::test_FR3_high_request_partial_item PASSED
test_blood_bank_logic.py::test_FR3_high_request_all_items_rejected PASSED
test_blood_bank_logic.py::test_FR3_high_request_multiple_items PASSED
test_blood_bank_logic.py::test_FR4_pending_low_and_mid_request_order PASSED
test_blood_bank_logic.py::test_FR4_two_requests_need_same_unit PASSED
test_blood_bank_logic.py::test_FR5_confirm_valid_plan PASSED
test_blood_bank_logic.py::test_FR5_confirm_stale_plan PASSED
test_blood_bank_logic.py::test_FR7_three_fulfilled_two_rejected_requests PASSED
test_blood_bank_logic.py::test_FR8_two_units_expired_value_1000 PASSED
test_blood_bank_logic.py::test_FR10_close_stock_csv_and_restart PASSED
test_blood_bank_logic.py::test_FR10_stock_csv_does_not_exist PASSED
test_blood_bank_logic.py::test_FR10_stock_csv_open_in_excel_during_save PASSED

============================= 20 passed ==============================
```

## Data Persistence

| Data | Saved Between Runs? | Storage |
|:-----|:-------------------:|:--------|
| Blood Stock (units, expiry, status) | ✅ Yes | `stock.csv` |
| Pending Requests | ❌ No | Memory only |
| Session Revenue | ❌ No | Memory only |
| Allocation Plan | ❌ No | Memory only |

## License

This project was built as an academic assignment for learning purposes.
