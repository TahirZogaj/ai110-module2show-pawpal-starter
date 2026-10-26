# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ Implementation Summary

All of the backend logic is in `pawpal_system.py`, organized as four classes (see `diagrams/uml.mmd`):

- **`Task`** (dataclass): one care activity, with a title, duration, priority (`low`/`medium`/`high`), category, preferred time, frequency and completion status. `mark_complete()` sets the task as done, and `priority_score()` turns the priority into a number for sorting.
- **`Pet`** (dataclass): a pet's details plus its own list of tasks. `add_task()` tags each task with the pet's name, so the schedule can say which pet each task is for.
- **`Owner`** (dataclass): the owner's free minutes for the day, day start time, and pets. `get_all_tasks()` combines every pet's tasks into one list.
- **`Scheduler`**: the planning logic. `generate_plan()` reads from `owner.get_all_tasks()`, so it plans across every pet. It drops completed tasks and sorts the rest by priority, then preferred time, then shortest duration. It then gives each task a start time, one after another from the owner's day start, until the available time runs out. Tasks that don't fit go to a `skipped` list. `explain_plan()` prints the plan and the reason for its order.

`main.py` is a terminal demo with one owner and two pets, and `tests/test_pawpal.py` holds the pytest suite.

## 🖥️ Sample Output

Output from running `python main.py` (one owner, two pets, recurring tasks, and two deliberate time conflicts):

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

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
