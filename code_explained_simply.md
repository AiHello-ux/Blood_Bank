# Blood Bank Program — Explained in Plain English

This is your "cheat sheet." It goes through every function in both files,
in simple words, so you can explain any part if you're asked.

---

## The Big Idea First

The program has **two files** because we split the work into two jobs:

- **`blood_bank_logic.py`** — this is the "brain." It only *decides* things
  (is this date okay? does this request get filled?). It never prints
  anything and never asks the user to type anything.
- **`main.py`** — this is the "mouth and ears." It's the only file that
  prints things on screen and reads what the user types. Whenever it
  needs to *decide* something, it calls a function from the brain file
  and uses the answer.

Why split it like this? So the "deciding" part can be tested and trusted
on its own, without needing a person to sit and type things every time
you test it. It also makes each file shorter and easier to read.

A **parameter** is just a piece of information you hand to a function
so it has what it needs to do its job — like handing someone ingredients
before asking them to cook.

**One note on matching the design doc:** every function in this version
of the code has the exact name and job the design doc describes — with
one small exception, `_sort_key` in `blood_bank_logic.py`, a tiny private
helper used only to tell Python's `sorted()` how to order units by expiry
then by ID inside `compatible_available_units`. It's not a new feature or
a structural change, just a one-line sort key pulled out for readability,
and it's invisible to anything outside that one function. Everything else
— every function name in both files, and the whole shape of `main()` —
now matches the doc's Function Signatures table and algorithm exactly.

---

## PART 1 — `blood_bank_logic.py` (the "brain")

### `new_session_log()`
- **Parameters:** none — it doesn't need any information to do its job.
- **What it does:** builds a brand-new scoreboard dictionary with everything
  set to zero: how many requests fulfilled, how many rejected, how much
  money earned, and an empty list of wasted units.
- **Used where:** called exactly once, right at the start of `main()`,
  before the loop begins — so we have a scoreboard to fill in as we go.

### `is_valid_group(group)`
- **Parameter `group`:** a piece of text, like `"O+"` or `"AB-"` — whatever
  blood group someone typed in.
- **What it does:** checks if `group` is one of the 8 real blood groups.
  If someone typed `"C+"` (not a real group), this returns `False`.
- **Used where:** called inside `handle_add_stock` (when adding stock) and
  `handle_submit_request` (when someone asks for blood), to catch typos.

### `is_valid_quantity(quantity)`
- **Parameter `quantity`:** whatever the user typed for "how many units,"
  as text — could be `"5"`, `"-3"`, or even `"abc"`.
- **What it does:** first checks `quantity.isdigit()` — this is a built-in
  text method that returns `True` only if every character is a plain
  digit (0-9). It returns `False` for `"-3"` (the minus sign isn't a
  digit) and for `"abc"` (letters aren't digits) and for `""` (nothing to
  check). Only once we know it's safely digits-only do we turn it into a
  real number with `int(quantity)` and check it's bigger than zero.
- **Used where:** `handle_submit_request`, to reject bad quantities.
- **Note:** this is why there's no need for `try`/`except` here — checking
  `.isdigit()` *first* means `int(quantity)` can never fail afterwards.

### `is_valid_urgency(urgency)`
- **Parameter `urgency`:** text that should say `"High"`, `"Mid"`, or `"Low"`.
- **What it does:** simple exact match check.
- **Used where:** `handle_submit_request`.

### `is_valid_hospital_type(hospital_type)`
- **Parameter `hospital_type`:** text that should say `"Private"` or `"Govt"`.
- **What it does:** exact match check, same idea as above.
- **Used where:** `handle_submit_request`.

### `is_expired(expiry, today)`
- **Parameter `expiry`:** the date written on a blood unit, as text,
  like `"2026-09-20"`.
- **Parameter `today`:** today's date, as text, same format.
- **What it does:** `datetime.strptime(expiry, "%Y-%m-%d")` reads that
  text and turns it into a real calendar date Python understands
  (instead of just a string). We do this for both `expiry` and `today`,
  then use a normal `<` to check if `expiry` comes before `today` — the
  same way you'd write `if 3 < 5`. We're trusting the date was typed
  correctly (the program always asks for `YYYY-MM-DD`), so there's no
  need to catch a bad-format error here.
- **Used where:** inside `add_unit`, inside `expire_units`, and inside
  `handle_add_stock` (to build the error message).

### `is_within_shelf_life(expiry, today)`
- **Parameters:** same two, `expiry` and `today`.
- **What it does:** adds 35 days to `today` (using `timedelta(days=35)`,
  a small helper from the `datetime` module that means "a stretch of 35
  days") to get a cutoff date, then checks that `expiry` is not later
  than that cutoff. This is the *only* place in the whole program that
  has the number 35 written down — if the rule ever changes to 40 days,
  you'd only need to change it here.
- **Used where:** inside `add_unit` and inside `handle_add_stock`.

### `add_unit(stock, unit_id, group, expiry, today)`
- **Parameter `stock`:** the full inventory — a list where each item is a
  dictionary describing one blood unit (id, group, expiry, status).
- **Parameter `unit_id`:** the ID we're about to give this new unit,
  like `"U005"`.
- **Parameter `group`:** blood group of the new unit.
- **Parameter `expiry`:** the date typed in for this unit.
- **Parameter `today`:** today's date.
- **What it does:** checks the date is good using the two functions above.
  If good, it makes a **new** list that's a copy of `stock` plus the new
  unit added at the end. If bad, it just hands back `stock` completely
  unchanged (nothing added).
- **Used where:** called from `handle_add_stock`, once for every group/date
  pair the user typed.

### `expire_units(stock, today)`
- **Parameters:** `stock`, `today`.
- **What it does:** looks at every unit in stock. Any unit that is still
  `"Available"` but whose date has already passed gets its status changed
  to `"Wasted"`.
- **Returns two things at once:** the updated stock list, *and* a separate
  small list containing just the units that got wasted this round (so we
  can print "these units just expired" and add their value to the loss
  total).
- **Used where:** called at the very top of the main loop in `main()`,
  every single time through — before the stock table is even printed.

### `compatible_available_units(stock, request_group)`
- **Parameter `stock`:** the inventory.
- **Parameter `request_group`:** the blood group a hospital is asking for,
  like `"A+"`.
- **What it does:** goes through every unit that is `"Available"`, and uses
  the compatibility table (the `COMPATIBILITY` dictionary at the top of the
  file) to check whether that unit's group is *allowed* to be given to
  someone who needs `request_group`. All the matching units get collected,
  then sorted so the one expiring soonest is first (if two expire on the
  same day, the one with the smaller ID goes first).
- **Used where:** called from inside `allocate_request`.

### `per_unit_fee(group, urgency, hospital_type)`
- **Parameter `group`:** blood group of the *unit being handed out*.
- **Parameter `urgency`:** urgency of the request (`High`/`Mid`/`Low`).
- **Parameter `hospital_type`:** `Private` or `Govt`.
- **What it does:** starts at Rs 500, adds money for urgency, adds Rs 150
  if the group is Rh-negative, then subtracts Rs 150 if it's a Govt hospital.
- **Used where:** called once for *each* unit being issued, from inside
  `allocate_request`.

### `allocate_request(stock, request)`
- **Parameter `stock`:** the inventory (never changed by this function).
- **Parameter `request`:** a dictionary with everything about one request —
  hospital name, type, group, quantity, urgency, id.
- **What it does:** the core decision-maker. It checks if there's enough
  compatible stock. If not enough, it builds a "Rejected" result showing
  how many are available vs needed. If enough, it picks the soonest-expiring
  units, works out the fee for each one, adds them up plus Rs 100 delivery,
  and builds a "Fulfilled" result.
- **Used where:** called from `handle_submit_request` (for High urgency,
  right away) and from `generate_plan` (one request at a time, for Mid/Low).

### `issue_units(stock, unit_ids)`
- **Parameter `stock`:** the inventory.
- **Parameter `unit_ids`:** a list of the specific unit IDs to mark as
  given out, like `["U004", "U011"]`.
- **What it does:** builds a new stock list where those particular units
  now say `"Issued"` instead of `"Available"`. Everything else stays the same.
- **Used where:** called from `handle_submit_request`, from `generate_plan`
  (during the simulation), and from `apply_plan` (for real, on confirm).

### `sort_for_plan(requests)`
- **Parameter `requests`:** the whole list of requests waiting to be
  processed (`pending_requests`).
- **What it does:** keeps only the ones that are still `"Pending"` and are
  `Mid` or `Low` urgency, then puts **all** the Mid ones first, followed by
  **all** the Low ones — keeping each group's original order.
- **Used where:** called from inside `generate_plan`.

### `generate_plan(stock, requests)`
- **Parameter `stock`:** the real inventory (this function never actually
  changes it).
- **Parameter `requests`:** the pending requests list.
- **What it does:** pretends to hand out units to each Mid/Low request, one
  at a time in the sorted order, writing down what *would* happen — but it's
  only a rehearsal. The real `stock` you passed in stays completely untouched.
- **Used where:** called from `handle_generate_plan` (menu option 3).

### `is_plan_valid(stock, plan)`
- **Parameter `stock`:** the real, current inventory right now.
- **Parameter `plan`:** the plan that was generated earlier (maybe a few
  minutes ago).
- **What it does:** double-checks that every unit the plan wants to hand
  out is *still* actually `"Available"` — nobody else took it, and it
  hasn't expired since the plan was made.
- **Used where:** called from `handle_confirm_plan` (menu option 4), before
  anything is actually committed.

### `apply_plan(stock, plan, session_log)`
- **Parameter `stock`:** the real inventory.
- **Parameter `plan`:** the plan being confirmed.
- **Parameter `session_log`:** the scoreboard.
- **What it does:** this is where things become *real*. It issues every
  fulfilled unit for good, and updates the scoreboard (adds up revenue,
  counts fulfilled/rejected).
- **Used where:** called from `handle_confirm_plan`, but only after
  `is_plan_valid` says `True`.

### `wasted_report(session_log)`
- **Parameter `session_log`:** the scoreboard.
- **What it does:** pulls out just the wasted-unit count and the money
  lost from wasted units.
- **Used where:** called when the user picks option 6.

### `progress_report(session_log)`
- **Parameter `session_log`:** the scoreboard.
- **What it does:** pulls out handled/fulfilled/rejected counts and total
  revenue.
- **Used where:** called when the user picks option 5.

---

## PART 2 — `main.py` (the "mouth and ears")

### `render_stock_table(stock)`
- **Parameter `stock`:** the inventory.
- **What it does:** for each of the 8 groups, counts how many are
  `"Available"` and finds the nearest expiry date, then builds the text
  table you see printed every loop.
- **Used where:** called every time through the main loop, right before
  printing.

### `render_menu()`
- **Parameters:** none.
- **What it does:** builds the 7-line numbered menu text.
- **Used where:** called every loop, right after the stock table.

### `read_add_stock_input()`
- **Parameters:** none (it reads directly from the keyboard using `input()`).
- **What it does:** asks the user to type group+date pairs separated by
  commas, splits that one big line apart, and returns a list of small
  dictionaries like `{"group": "O+", "expiry": "2026-10-01"}`.
- **Used where:** called from `handle_add_stock`.

### `read_request_input()`
- **Parameters:** none.
- **What it does:** asks 5 questions one at a time (hospital, type, group,
  quantity, urgency) and returns them as one dictionary — nothing is
  checked for correctness yet, that happens afterwards.
- **Used where:** called from `handle_submit_request`.

### `print_bill(allocation)`
- **Parameter `allocation`:** the dictionary that came back from
  `allocate_request` — either a "Fulfilled" one or a "Rejected" one.
- **What it does:** if Fulfilled, prints the itemized bill (each unit,
  its fee, the transport charge, the total). If Rejected, prints the
  rejection message instead.
- **Used where:** called from `handle_submit_request`, right after a
  High-urgency request is decided.

### `print_plan(plan)`
- **Parameter `plan`:** the whole plan built by `generate_plan`.
- **What it does:** prints every request in the plan and what would happen
  to it, then the total proposed revenue at the bottom.
- **Used where:** called from `handle_generate_plan`.

### `print_progress_report(report)`
- **Parameter `report`:** the dictionary returned by `progress_report()`.
- **What it does:** prints the four numbers in it.
- **Used where:** option 5 in `main()`.

### `print_wasted_report(report, stock)`
- **Parameter `report`:** the dictionary from `wasted_report()`.
- **Parameter `stock`:** needed separately because `report` only has the
  *count* and *value* — to list each individual wasted unit by name, we
  have to look through `stock` for anything marked `"Wasted"`.
- **Used where:** option 6 in `main()`.

### `main()`
- **Parameters:** none.
- **What it does:** this is the "conductor," and it's the *only* function
  in `main.py` that does the actual work of all seven menu options — there
  are no separate `handle_...` functions anymore. It sets up everything
  empty at the start (`stock = []`, `pending_requests = []`,
  `current_plan = None`, a fresh `session_log`, counters at 1), then loops
  forever:
  1. Expire old units (calls `logic.expire_units`), print what got wasted
     if anything did.
  2. Print the stock table and menu.
  3. Read the user's choice; if it's not a number 1–7, show an error and
     loop again.
  4. Run an `if`/`elif` chain — one branch per menu option — right there
     inside the loop. Each branch does its own reading, validating, and
     calling into `blood_bank_logic.py`, the same way the design doc's
     algorithm for `main()` describes it.
  5. Keep looping until the user picks option 7 (Exit).

  **Why no `handle_...` functions?** An earlier draft split each menu
  option into its own function (`handle_add_stock`, `handle_submit_request`,
  and so on) to keep `main()` shorter. That's a reasonable way to write
  Python, but it doesn't match the design doc, which describes `main()`
  as one continuous block of steps with no named sub-functions. So the
  final version inlines all of that logic directly into the loop, the way
  the doc lays it out. The trade-off: `main()` is a long function now, but
  every line of it can be pointed to a specific line in the design doc.

  **What happened to case-insensitive matching (Govt/govt, High/high)?**
  Same story — there used to be two small helper functions,
  `normalize_hospital_type` and `normalize_urgency`, that did this
  conversion. The design doc's algorithm for option 2 doesn't name any
  such function, so that conversion now happens inline, right where
  `hospital_type` and `urgency` get read and checked, using a small
  `if`/`elif` chain instead of a function call.

---

## Where are the `input()` statements?

There are **7 `input()` lines** total. Six of them are tucked inside two
small functions whose whole job is "ask this one question" —
`read_add_stock_input()` and `read_request_input()`. The seventh, reading
the menu choice, lives directly inside `main()`, since that's the one
piece of input `main()`'s own loop needs to keep going.

Here's exactly where each one is, by function:

**Inside `read_add_stock_input()`** (1 input):
```python
raw = input("Enter group and expiry date (e.g., O+ 2026-10-01), comma-separated: ")
```

**Inside `read_request_input()`** (5 inputs, one after another):
```python
hospital = input("Hospital name: ")
hospital_type = input("Hospital type (Private/Govt): ")
group = input("Blood group: ")
quantity = input("Quantity: ")
urgency = input("Urgency (High/Mid/Low): ")
```

**Inside `main()` itself** (1 input — this is the only one that lives
directly in `main()`, because reading the menu choice *is* the main
loop's own job):
```python
choice_text = input("Choose an option: ").strip()
```

So the flow is: `main()` doesn't ask about hospitals or stock directly —
it calls `read_add_stock_input()` or `read_request_input()` when it needs
that information, and those functions do the actual asking, then hand
the answer back as a return value.

---

## If your teacher asks you to trace through an example

A good way to explain it out loud: **"a request goes in, a decision comes
out, nothing changes until it's confirmed."**

For example, if someone submits a High-urgency request:
1. `main()` sees the user picked option 2, so it enters that branch of
   the `if`/`elif` chain right there in the loop.
2. It calls `read_request_input()` to get the raw answers, then checks
   each field is valid (group, quantity, urgency, hospital type) using
   the `is_valid_...` functions from `blood_bank_logic.py`.
3. Because it's High urgency, `main()` calls
   `allocate_request(stock, request)` right away — this *only decides*,
   it doesn't touch `stock` yet.
4. If it says "Fulfilled", `main()` then calls `issue_units(stock, ...)`
   to actually update the stock, and updates `session_log` with the new
   revenue.
5. `print_bill(allocation)` shows the result to the user.

Note there's no separate `handle_submit_request` function doing steps
2–5 anymore — it's all just sequential code inside `main()`'s option-2
branch, matching how the design doc describes it.

For Mid/Low requests, steps 3–4 don't happen right away — the request
just waits in `pending_requests` until someone picks option 3
(`generate_plan`, a rehearsal) and then option 4 (`apply_plan`, for real).
