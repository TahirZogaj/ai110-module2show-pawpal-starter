# 🐾 PawPal+

**PawPal+** is a pet care planning assistant built with Python and Streamlit. A busy pet owner enters their pets and care tasks (walks, feeding, meds, grooming, enrichment), and PawPal+ builds a daily schedule that fits the time they have. It puts the most important care first, warns about clashing times, keeps repeating tasks coming back automatically, and explains why it chose the plan it did.

## ✨ Features

- **Multi-pet planning:** one owner can have any number of pets. The scheduler plans across all of them together, because the owner can only do one thing at a time.
- **Priority-based scheduling:** tasks are placed by priority (high → medium → low), then by preferred time, then shortest first. Each task gets a start time, back-to-back from the owner's day start, until the available minutes run out.
- **Time budget with explanations:** tasks that don't fit are listed as *skipped* instead of silently dropped. The plan never runs past midnight, and "Why this plan?" explains the ordering.
- **Sorting by time:** tasks can be listed in chronological order by preferred `HH:MM` time, with untimed tasks last. Unpadded times like `8:00` sort correctly.
- **Filtering by pet and status:** view one pet's tasks, only pending or only completed tasks, or both together.
- **Daily and weekly recurrence:** marking a repeating task complete automatically creates the next one (due tomorrow or in 7 days, calculated with `timedelta`). One-time tasks don't repeat, and future tasks stay out of today's plan.
- **Conflict warnings:** detects tasks whose preferred times *overlap*, not just exact matches, for the same pet or across pets. It shows a clear warning with a suggestion instead of crashing.
- **Automated tests:** 31 pytest tests cover these behaviors and their edge cases.

## 🚀 Getting started

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

| To... | Run |
|---|---|
| Open the app | `streamlit run app.py` |
| Run the terminal demo | `python main.py` |
| Run the tests | `python -m pytest` |

## 🗂️ Project structure

| File | Purpose |
|---|---|
| `pawpal_system.py` | Logic layer: the `Owner`, `Pet`, `Task` and `Scheduler` classes |
| `app.py` | Streamlit user interface |
| `main.py` | Terminal demo that exercises every feature |
| `tests/test_pawpal.py` | Automated test suite |
| `diagrams/uml_final.mmd` | Final Mermaid UML class diagram |
| `reflection.md` | Design decisions, tradeoffs and AI collaboration notes |

## 🛠️ Implementation Summary

All of the backend logic is in `pawpal_system.py`, organized as four classes (see `diagrams/uml_final.mmd`):

- **`Task`** (dataclass): one care activity, with a title, duration, priority (`low`/`medium`/`high`), category, preferred time, frequency (`once`/`daily`/`weekly`), due date and completion status. `mark_complete()` marks it done and returns the next occurrence if it repeats.
- **`Pet`** (dataclass): a pet's details plus its own list of tasks. `add_task()` tags each task with the pet's name, so the schedule can say which pet each task is for.
- **`Owner`** (dataclass): the owner's available minutes, day start time and pets. `get_all_tasks()` combines every pet's tasks into one list, and `filter_tasks()` narrows it down by pet and/or status.
- **`Scheduler`**: the planning logic. It reads tasks only through `owner.get_all_tasks()`, so it always plans across every pet.
  - `generate_plan()` takes the tasks due today, sorts them, and assigns start times until the time runs out.
  - `detect_conflicts()` flags overlapping preferred times.
  - `mark_task_complete()` handles recurring tasks.
  - `explain_plan()` describes the result.

## 📐 Smarter Scheduling

Beyond basic planning, the scheduler has four features. All of them live in `pawpal_system.py` and are covered by `tests/test_pawpal.py`.

| Feature | Method(s) | How it works |
|---------|-----------|--------------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_tasks()` | `sort_by_time()` orders tasks by preferred `"HH:MM"` time using `sorted()` with a `lambda` key that converts to minutes after midnight; tasks with no time go last. `sort_tasks()` orders tasks for planning: priority first, then preferred time, then shortest duration. |
| Filtering | `Owner.filter_tasks(pet_name=None, completed=None)`, `Task.is_due()` | Returns tasks for one pet, by completion status, or both; any argument left as `None` is not filtered. `generate_plan()` uses `is_due()` to plan only pending tasks due today or earlier, and skips tasks that don't fit in the owner's available minutes. |
| Conflict detection | `Scheduler.detect_conflicts()` | Turns each preferred time and duration into a time window and checks every pair (`itertools.combinations`) for overlap, both for the same pet and across pets. It returns readable warning messages instead of raising errors; tasks that only touch (e.g. 07:30–08:00 and 08:00–08:10) don't count. Warnings appear in `explain_plan()` and in the Streamlit app. |
| Recurring tasks | `Task.mark_complete()`, `Scheduler.mark_task_complete()` | Completing a `"daily"` or `"weekly"` task creates a copy due 1 or 7 days later, calculated with `timedelta`, and adds it to the same pet. One-time (`"once"`) tasks don't repeat. Future copies are left out of today's plan. |

**Known limitation:** conflicts are *reported*, not resolved. The plan places tasks one after another by priority, so the final schedule never overlaps, but tasks may not run at their exact preferred times. See `reflection.md` section 2b.

## 📸 Demo Walkthrough

### Main UI features

The Streamlit app (`streamlit run app.py`) is one page with four areas:

| Area | What you can do |
|---|---|
| **Owner** | Set your name, how many minutes you have today, and what time your day starts. |
| **Pets** | Add a pet (name, species, age). Blank and duplicate names are rejected with an error. A table lists each pet and its task count. |
| **Tasks** | Add a task for a pet: title, category, duration, priority, optional preferred time, and whether it repeats (once/daily/weekly). The **Task list** is sorted by time and can be filtered by pet and by status (all/pending/completed). **Mark a task complete** finishes a task and, if it repeats, schedules the next one. |
| **Build Schedule** | Click **Generate schedule** to see today's plan as a table with start times, a summary of minutes used, any skipped tasks, any time conflicts, and a "Why this plan?" explanation. |

### Example workflow

1. **Set up the owner.** Enter "Jordan", set **Minutes available today** to 60, and leave the day starting at 08:00.
2. **Add two pets.** Add *Mochi* (dog, 3) and *Luna* (cat, 5). Both appear in the pets table with 0 tasks.
3. **Add tasks:**
   - Mochi: *Morning walk*, 30 min, high, 08:00, daily.
   - Luna: *Breakfast*, 10 min, high, 08:00, daily.
   - Luna: *Play session*, 30 min, low, no preferred time.
4. **Review the task list.** The table is sorted by time (the 08:00 tasks first, then the untimed play session last). A yellow warning appears right away: *"'Morning walk' for Mochi (08:00-08:30) overlaps 'Breakfast' for Luna (08:00-08:10) [different pets]"*, with a suggestion to move one task or get help.
5. **Filter.** Choose *Luna* under **Show pet** to see only Luna's tasks, then switch back to *All pets*.
6. **Generate today's schedule.** Click **Generate schedule**. A green banner reports *"Scheduled 2 task(s) for Jordan, using 40 of 60 available minutes"*. The table shows Breakfast for Luna at 08:00 and Morning walk for Mochi at 08:10: both are high priority, so the shorter task goes first. *Play session* (30 min) is listed as skipped because only 20 minutes are left, and the conflict warning appears again.
7. **Complete a recurring task.** Under **Mark a task complete**, pick Luna's Breakfast and click **Mark complete**. A green message confirms: *"It repeats daily, so the next one is due"* tomorrow's date. The conflict warning disappears, and choosing **Completed** under **Show status** shows the finished task.

### Key Scheduler behaviors shown

- **Sorting:** the task list is in chronological order via `Scheduler.sort_by_time()`, and the plan follows priority → time → duration via `sort_tasks()`.
- **Filtering:** the pet and status filters call `Owner.filter_tasks()`.
- **Conflict warnings:** overlapping preferred times are flagged by `Scheduler.detect_conflicts()` before and after planning.
- **Time budget:** tasks that don't fit in the available minutes are reported as skipped, not silently dropped.
- **Recurrence:** completing a daily task creates tomorrow's copy via `Scheduler.mark_task_complete()`, and that copy stays out of today's plan.

### CLI demo (`python main.py`)

`main.py` runs the same logic in the terminal: one owner, two pets, tasks added out of order, two recurring completions and two deliberate time conflicts. The end of its output is today's schedule. The full output is in **Sample Output** below.

```
Daily plan for Jordan (77 of 90 minutes used):
  07:30 - Morning walk for Mochi (30 min) [priority: high]
  08:00 - Breakfast for Mochi (10 min) [priority: high]
  08:10 - Breakfast for Luna (10 min) [priority: high]
  08:20 - Litter box cleaning for Luna (15 min) [priority: medium]
  08:35 - Fill water bowl for Mochi (2 min) [priority: medium]
  08:37 - Ear cleaning for Mochi (10 min) [priority: low]
Tasks were ordered by priority, then preferred time, then shortest first.
Skipped (not enough time left):
  Brushing for Mochi (15 min) [priority: low]
Time conflicts in preferred times:
  Warning: 'Morning walk' for Mochi (07:30-08:00) overlaps 'Ear cleaning' for Mochi (07:45-07:55) [same pet].
  Warning: 'Breakfast' for Mochi (08:00-08:10) overlaps 'Breakfast' for Luna (08:00-08:10) [different pets].
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

## 🖥️ Sample Output

Full output from running `python main.py`:

```
==================================================
Recurring Tasks
==================================================

Completed 'Give medication' (daily, due 2026-10-25).
  Next occurrence created for Luna, due 2026-10-26.

Completed 'Play session' (once).
  Next occurrence: None

Luna now has 5 tasks; tomorrow's medication is not in today's plan.

==================================================
Sorting and Filtering
==================================================

All tasks (in the order they were added):
  18:00  Brushing for Mochi (15 min) [pending, due 2026-10-25]
  07:30  Morning walk for Mochi (30 min) [pending, due 2026-10-25]
  08:00  Breakfast for Mochi (10 min) [pending, due 2026-10-25]
  --:--  Fill water bowl for Mochi (2 min) [pending, due 2026-10-25]
  07:45  Ear cleaning for Mochi (10 min) [pending, due 2026-10-25]
  12:00  Play session for Luna (20 min) [done, due 2026-10-25]
  17:00  Litter box cleaning for Luna (15 min) [pending, due 2026-10-25]
  08:15  Give medication for Luna (5 min) [done, due 2026-10-25]
  08:00  Breakfast for Luna (10 min) [pending, due 2026-10-25]
  08:15  Give medication for Luna (5 min) [pending, due 2026-10-26]

All tasks sorted by time:
  07:30  Morning walk for Mochi (30 min) [pending, due 2026-10-25]
  07:45  Ear cleaning for Mochi (10 min) [pending, due 2026-10-25]
  08:00  Breakfast for Mochi (10 min) [pending, due 2026-10-25]
  08:00  Breakfast for Luna (10 min) [pending, due 2026-10-25]
  08:15  Give medication for Luna (5 min) [done, due 2026-10-25]
  08:15  Give medication for Luna (5 min) [pending, due 2026-10-26]
  12:00  Play session for Luna (20 min) [done, due 2026-10-25]
  17:00  Litter box cleaning for Luna (15 min) [pending, due 2026-10-25]
  18:00  Brushing for Mochi (15 min) [pending, due 2026-10-25]
  --:--  Fill water bowl for Mochi (2 min) [pending, due 2026-10-25]

Luna's tasks:
  12:00  Play session for Luna (20 min) [done, due 2026-10-25]
  17:00  Litter box cleaning for Luna (15 min) [pending, due 2026-10-25]
  08:15  Give medication for Luna (5 min) [done, due 2026-10-25]
  08:00  Breakfast for Luna (10 min) [pending, due 2026-10-25]
  08:15  Give medication for Luna (5 min) [pending, due 2026-10-26]

Completed tasks:
  12:00  Play session for Luna (20 min) [done, due 2026-10-25]
  08:15  Give medication for Luna (5 min) [done, due 2026-10-25]

Mochi's pending tasks, sorted by time:
  07:30  Morning walk for Mochi (30 min) [pending, due 2026-10-25]
  07:45  Ear cleaning for Mochi (10 min) [pending, due 2026-10-25]
  08:00  Breakfast for Mochi (10 min) [pending, due 2026-10-25]
  18:00  Brushing for Mochi (15 min) [pending, due 2026-10-25]
  --:--  Fill water bowl for Mochi (2 min) [pending, due 2026-10-25]

==================================================
Conflict Check
==================================================
  Warning: 'Morning walk' for Mochi (07:30-08:00) overlaps 'Ear cleaning' for Mochi (07:45-07:55) [same pet].
  Warning: 'Breakfast' for Mochi (08:00-08:10) overlaps 'Breakfast' for Luna (08:00-08:10) [different pets].

==================================================
Today's Schedule
==================================================
Daily plan for Jordan (77 of 90 minutes used):
  07:30 - Morning walk for Mochi (30 min) [priority: high]
  08:00 - Breakfast for Mochi (10 min) [priority: high]
  08:10 - Breakfast for Luna (10 min) [priority: high]
  08:20 - Litter box cleaning for Luna (15 min) [priority: medium]
  08:35 - Fill water bowl for Mochi (2 min) [priority: medium]
  08:37 - Ear cleaning for Mochi (10 min) [priority: low]
Tasks were ordered by priority, then preferred time, then shortest first.
Skipped (not enough time left):
  Brushing for Mochi (15 min) [priority: low]
Time conflicts in preferred times:
  Warning: 'Morning walk' for Mochi (07:30-08:00) overlaps 'Ear cleaning' for Mochi (07:45-07:55) [same pet].
  Warning: 'Breakfast' for Mochi (08:00-08:10) overlaps 'Breakfast' for Luna (08:00-08:10) [different pets].
```

## 🧪 Testing PawPal+

Run the full test suite from the project root (with the virtual environment activated):

```bash
python -m pytest
```

The 31 tests in `tests/test_pawpal.py` cover both normal use and edge cases:

- **Sorting:** tasks come back in chronological order with no-time tasks last, unpadded times like `"8:00"` sort correctly, and the plan follows priority → preferred time → shortest duration.
- **Recurring tasks:** completing a daily task creates a new one due the next day; weekly tasks come back in 7 days; one-time tasks don't repeat. Also checks overdue tasks, tasks completed early, Dec 31 → Jan 1 rollover, and that the new copy keeps the task's details but stays out of today's plan.
- **Conflict detection:** flags tasks at the exact same time or with overlapping durations (same pet and across pets), produces one warning per clashing pair, ignores tasks that only touch, completed tasks and future tasks, and warns about invalid times instead of crashing.
- **Scheduling:** start times run back-to-back from the owner's day start, the time budget is respected (exact fits are scheduled, zero minutes skips everything), the plan never runs past midnight, overdue tasks are still planned, re-running `generate_plan()` doesn't duplicate tasks, and empty owners or pets give an empty plan.
- **Basics and filtering:** `mark_complete()`, adding tasks to a pet, filtering by pet and/or completion status, and a clear error for a misspelled priority.

Successful test run:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.15, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/tahirzogaj/ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 31 items

tests/test_pawpal.py ...............................                     [100%]

============================== 31 passed in 0.01s ==============================
```

**Confidence level: ⭐⭐⭐⭐☆ (4/5)**

All 31 tests pass, including the edge cases most likely to break a scheduler: ties, boundaries, empty inputs, date rollovers and overlapping times. Writing them also caught two real bugs, which are now fixed: times were being compared as text, and plans could run past midnight. I'm not giving it 5 stars because a few things are still untested or unhandled. Completing a recurring task after its pet has been removed raises an unclear error. The Streamlit UI is only checked by hand. And the scheduler warns about conflicts rather than resolving them.
