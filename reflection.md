# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML design centered on four classes with clearly separated responsibilities:

- **Task** (dataclass): holds all data about a single care activity — title, scheduled time in HH:MM format, duration in minutes, priority level, frequency (once/daily/weekly), completion status, and due date. It owns one behavior: `mark_complete()`, which handles its own recurrence by returning a copy of itself with an updated due date.
- **Pet** (dataclass): owns a list of tasks and provides `add_task()` and `remove_task()`. It is purely a data container for one animal.
- **Owner**: holds a list of pets and provides `get_all_tasks()`, which flattens all pets' tasks into a single list of `(pet_name, task)` tuples. This flat view is the data contract the rest of the system depends on.
- **Scheduler**: a service object (not a data holder) that takes an Owner and provides all scheduling algorithms — sorting, filtering, today's schedule, conflict detection, and completing tasks.

The key relationship is: Owner → Pets → Tasks, with Scheduler sitting outside that hierarchy and operating on it through `owner.get_all_tasks()`.

**b. Design changes**

The main design decision was keeping Scheduler as a pure service object rather than having it own pets directly. An early draft considered giving Scheduler its own `pets` list and `add_pet()` method, which would have made it both a data store and an algorithm provider. Separating those concerns — Owner holds data, Scheduler provides algorithms — made each class easier to test in isolation and easier to reason about. The `mark_complete()` method on Task was also a deliberate choice: rather than having the Scheduler reconstruct next-occurrence tasks from scratch, Task knows its own recurrence rules and returns the next copy itself. The Scheduler just decides where to put it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two main constraints:

1. **Time** — tasks are sorted chronologically by their HH:MM time string. This ensures the daily schedule is always presented in the order things actually need to happen.
2. **Due date** — `get_todays_schedule()` only returns tasks whose `due_date` is today (or null, for one-offs). This keeps tomorrow's recurring tasks out of today's view.

Priority (low/medium/high) is stored on each task and displayed to the owner, but the current scheduler sorts strictly by time rather than by priority. This reflects the reality that pet care usually has fixed time windows (the dog needs a morning walk at 8am regardless of priority level), so time is the more useful axis for daily planning.

**b. Tradeoffs**

The conflict detection uses **exact time-string matching** rather than checking for overlapping time windows. Two tasks conflict if and only if their `time` field is identical (e.g., both say `"09:00"`). This means a 30-minute task starting at 9:00 and a 10-minute task starting at 9:20 are not flagged as a conflict even though they overlap.

This tradeoff is reasonable for this scenario because: (1) it keeps the algorithm simple and transparent — no arithmetic or datetime parsing required; (2) pet owners typically schedule tasks at discrete, round times; (3) a warning system that produces too many false positives becomes noise that owners start ignoring. Exact matching catches the clearest conflicts without overwhelming the user.

---

## 3. AI Collaboration

**a. How you used AI**

AI tools were used across every phase of the project:

- **System design** — to brainstorm the four-class architecture and generate the initial Mermaid UML diagram. Asking "design a pet care scheduling app with Owner, Pet, Task, and Scheduler classes" produced a solid starting structure that only needed minor adjustments.
- **Implementation** — to draft the `detect_conflicts()` method using `defaultdict`, the `mark_complete()` recurrence logic using `copy.copy()` and `timedelta`, and the `get_todays_schedule()` filter.
- **Testing** — to generate test scaffolding and identify edge cases worth covering (empty pet, same-time conflicts, weekly vs. daily recurrence).
- **UI wiring** — to figure out the correct `st.session_state` pattern for persisting Python objects across Streamlit rerenders.

The most useful prompt pattern was providing context + constraint: "I need `detect_conflicts()` to return warning strings, not raise exceptions, and should only consider incomplete tasks." Specificity about output format and constraints produced directly usable code.

**b. Judgment and verification**

When AI generated the Scheduler with its own `pets` list and `add_pet()` method (conflating data storage with scheduling logic), I did not accept that design. I evaluated it against the Single Responsibility Principle: a class that both holds data and provides algorithms is harder to test and harder to extend. I restructured so Owner holds the data and Scheduler only holds a reference to Owner. The verification was simple — I asked "if I want to unit-test conflict detection without touching the UI, can I do it?" With the service-object design the answer was yes; with the combined design it was harder. I also ran `main.py` after the restructure to confirm the output was identical.

---

## 4. Testing and Verification

**a. What you tested**

Five behaviors were tested:

1. `mark_complete()` flips `completed` to `True` and returns `None` for one-time tasks
2. `add_task()` correctly increases the pet's task count
3. `sort_by_time()` returns tasks in chronological order even when added out of order
4. `mark_complete()` on a daily task returns a copy with `due_date = today + 1 day`
5. `detect_conflicts()` identifies exactly one conflict when two tasks share the same time

These tests matter because they cover the two things that would be most painful to debug in the UI: incorrect sort order (the schedule would look wrong) and broken recurrence (tasks would disappear after being marked complete instead of rescheduling).

**b. Confidence**

Confidence level: **4/5 stars**. The core happy paths are verified. Edge cases to test next:

- A pet with zero tasks (does `get_todays_schedule()` return an empty list gracefully?)
- An invalid time string like `"9:5"` instead of `"09:05"` (lexicographic sort would silently produce wrong order)
- Weekly recurrence across a month boundary
- Two tasks with the same title for the same pet (which one gets marked complete?)
- Calling `mark_task_complete()` with a pet name that does not exist

---

## 5. Reflection

**a. What went well**

The clearest win was the decision to store time as a plain "HH:MM" string and sort it lexicographically. This seems like a simplification that would break, but it works correctly for all valid times and eliminates the need to import or parse datetime objects throughout the algorithm layer. The demo in `main.py` validated this immediately — the schedule printed in the right order on the first run.

The separation of Owner (data) from Scheduler (algorithms) also paid off immediately in testing: every test could construct a minimal Owner/Pet/Task graph and call Scheduler methods directly without mocking anything.

**b. What you would improve**

The main thing to redesign would be adding **priority-aware scheduling**. Currently, if two tasks could be rescheduled and only one fits in the available time, the scheduler has no way to choose between them — it just shows everything sorted by time. A proper priority-first sort (high before medium before low, then by time within each priority tier) would make the daily schedule more useful when the owner is overbooked.

I would also add **duration-aware conflict detection**: instead of flagging only exact time matches, flag any two tasks whose time ranges overlap based on their duration.

**c. Key takeaway**

The most important thing I learned is that AI is most useful for the *implementation* of decisions you have already made, not for making the decisions themselves. When I asked AI to "build a scheduler," it produced a working but architecturally murky result. When I asked it to "implement `detect_conflicts()` as a method on a Scheduler service object that only reads from `owner.get_all_tasks()`," it produced exactly what I needed. The architect's job is to make those structural decisions before delegating the code-writing — and that part cannot be skipped.
