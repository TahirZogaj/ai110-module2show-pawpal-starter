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

Output from running `python main.py` (one owner, two pets, six tasks, 90 minutes available):

```
==================================================
Today's Schedule
==================================================
Daily plan for Jordan (80 of 90 minutes used):
  07:30 - Morning walk for Mochi (30 min) [priority: high]
  08:00 - Breakfast for Mochi (10 min) [priority: high]
  08:10 - Give medication for Luna (5 min) [priority: high]
  08:15 - Play session for Luna (20 min) [priority: medium]
  08:35 - Litter box cleaning for Luna (15 min) [priority: medium]
Tasks were ordered by priority, then preferred time, then shortest first.
Skipped (not enough time left):
  Brushing for Mochi (15 min) [priority: low]
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

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
