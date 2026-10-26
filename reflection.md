# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The PawPal+ application will allow users to perform three main actions:

1. **Add and Manage Pet Information:** Users can add their pets by entering basic information such as their name, species, age, and specific care needs.

2. **Create and Manage Pet Care Tasks:** Users can add, edit, or remove daily tasks such as feeding, walking, grooming, and giving medication. Each task can have a duration and priority level so the application can organize activities effectively.

3. **Generate and View a Daily Care Schedule:** Users can generate a daily schedule based on their available time and the priority of each task. The application will display the recommended order of activities and explain why certain tasks were prioritized.

To support these actions, my initial UML has four classes. Ownership runs in one direction: an Owner has many Pets, each Pet has its own Tasks, and the Scheduler works from a single Owner.

- **Owner** stores the person's name, how many minutes they have free each day, what time their day starts, any preferences, and their list of pets. It can add or remove pets and collect every task across all of its pets, which gives the scheduler one place to get its input.
- **Pet** stores basic info (name, species, age, notes) and the care tasks that pet needs. It adds and removes tasks and can return only the ones that are still pending.
- **Task** is one piece of care, like a walk, a feeding or a dose of medication. It stores a title, duration, priority, category, optional preferred time, and whether it's been completed. It can mark itself complete and turn its priority into a number for sorting.
- **Scheduler** holds the scheduling logic. Given an Owner, it sorts tasks by priority, checks whether each one fits in the time left, builds the daily plan, keeps track of which tasks were skipped, and explains why it made the plan it did.

I used Python dataclasses for Task, Pet and Owner because they mostly hold data. Scheduler is a regular class because it holds behavior and state that changes while a plan is built.

**b. Design changes**

Yes. I asked my AI assistant to review the skeleton for missing relationships and logic bottlenecks, and I made three changes:

1. **Added `pet_name` to Task.** `Owner.get_all_tasks()` returns one flat list, so the Scheduler had no way to know which pet a task belonged to. A plan that says "Walk (30 min)" without saying which pet isn't useful for an owner with more than one pet. `Pet.add_task()` now tags each task with the pet's name.
2. **The schedule now stores start times.** `scheduled` was a plain list of Tasks, which shows the order but not *when* each task happens. The scheduler is supposed to produce a daily plan, so it now stores `(start_time, task)` pairs, counting forward from the owner's `day_start`.
3. **Added a `PRIORITY_SCORES` mapping.** Priority is a string ("low", "medium", "high"). Keeping the string-to-number mapping in one place means sorting stays consistent and a typo can be caught instead of silently sorting wrong.

The review also pointed out that `generate_plan()` must clear the previous plan before building a new one. Streamlit reruns the script often, so without that, old results would pile up. I noted this in the method's docstring to handle during implementation. I also decided *not* to add a separate class for scheduled items, since a tuple is enough for now and a new class would add complexity before I need it.

The design kept growing during the algorithm phase. I added `due_date` and `is_due()` to Task for recurring tasks, `filter_tasks()` to Owner, and `sort_by_time()`, `detect_conflicts()` and `mark_task_complete()` to Scheduler. The final diagram (`diagrams/uml_final.mmd`) also shows relationships the first draft left out: the Scheduler works directly with Tasks, and completing a recurring task creates a new Task and adds it to a Pet.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

My scheduler considers these constraints:

- **Available time:** the owner's minutes for the day. This is a hard limit: tasks that don't fit are skipped, not squeezed in. The plan also can't run past midnight.
- **Priority:** high, medium or low. This decides the order tasks are placed in.
- **Preferred time:** used as a tie-breaker between tasks of the same priority, for the task list sorting, and for conflict warnings.
- **Duration:** shorter tasks go first when priority and time are tied, which fits more tasks into the day.
- **Due date and completion:** only pending tasks due today or earlier are planned. Finished tasks and future copies of recurring tasks are left out.

I decided **time and priority matter most** because they reflect what actually happens to a pet if the plan is wrong. Missing a medication or a meal is much worse than brushing happening late, and an owner can't do more than the time they have. Preferred times matter less: a walk at 08:10 instead of 08:00 is fine, so I treated them as a preference to warn about, not a rule to enforce. I did not use the owner's `preferences` field in scheduling. It's stored, but I kept the logic focused on the constraints that most affect the pet.

**b. Tradeoffs**

**Tradeoff: conflicts are warned about, not resolved.** `detect_conflicts()` checks for *overlapping durations*, not just exact time matches. For example, a 07:30 walk lasting 30 minutes conflicts with ear cleaning at 07:45. But the scheduler only *reports* these clashes; it doesn't move tasks to fix them. The plan itself is built greedily: tasks are sorted by priority and placed back-to-back from the start of the day, so the final schedule never overlaps, but tasks don't necessarily happen at their preferred times.

I think this is reasonable for a pet owner's day. The most important thing is that high-priority care like meds and feeding gets done within the time available, and a short warning lets the owner decide how to handle a clash (for example, asking someone else to feed the cat). Resolving conflicts automatically would mean rearranging lower-priority tasks around fixed time slots. That's much more complex logic, and it could still make choices the owner wouldn't.

A second, smaller tradeoff is performance. `detect_conflicts()` compares every pair of tasks with `itertools.combinations`, which is O(n²). Sorting by start time and stopping early would be faster, but a pet owner has maybe 5–20 tasks a day, so the simpler version is easier to read and fast enough.

**Simplifying the algorithm with AI.** I asked my AI assistant how `detect_conflicts()` could be made more readable or faster. It gave three options:

1. **Use `itertools.combinations(windows, 2)`** instead of a nested loop with `enumerate` and list slicing. **I accepted this.** It says exactly what the code does ("every pair"), removes the index bookkeeping, and saves a level of indentation.
2. **Sort the windows by start time and `break` out of the inner loop** once a task starts after the current one ends. This is faster for large lists, but the early `break` is easy to get wrong and hard to follow. **I rejected it** because my task lists are small.
3. **Collapse the whole check into a single list comprehension.** That's more "Pythonic" and shorter, but cramming the overlap test, the same-pet check and a multi-line f-string into one expression makes it much harder to read and debug. **I kept the explicit loop.**

I verified the change by re-running all 12 tests and the `main.py` demo; the same two conflicts were reported as before.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code in VS Code at every stage:

- **Design:** it drafted the Mermaid UML for my four classes. I then asked it to review that diagram for unnecessary complexity.
- **Review:** I gave it the `pawpal_system.py` skeleton and asked about missing relationships and logic bottlenecks.
- **Implementation:** in agent mode, it wrote out the four classes, the `main.py` demo script, the algorithmic features, the Streamlit UI and the pytest tests.
- **Documentation:** it added the docstrings and drafted the README and UML updates.

The most helpful prompts were narrow ones with a clear goal, like "review this skeleton for missing relationships or bottlenecks" or "check that relationships make sense and there's no unnecessary complexity." Pointing the AI at a specific file with a specific question got concrete, usable answers instead of generic advice.

**What AI suggested and what I accepted**

From the skeleton review I accepted three changes:

- adding `pet_name` to `Task`, so the schedule can say which pet a task is for;
- storing start times in the schedule, so it shows *when* each task happens and not just the order;
- a single `PRIORITY_SCORES` mapping, so a misspelled priority raises an error instead of sorting wrong.

I also kept its warning that `generate_plan()` must clear the old plan first, because Streamlit reruns the script.

**b. Judgment and verification**

I didn't accept every suggestion as-is:

- **Some features came out of the first draft.** The first UML draft included task frequency, an `is_due_today()` method and a `detect_conflicts()` method. I removed them during the complexity review because the first version of the scheduler didn't need them yet. I added them back later, when the algorithm phase actually called for recurring tasks and conflict detection, so each one arrived with a real use and tests.
- **No new class for scheduled items.** The review suggested scheduled items could become their own class. I decided a `(start_time, task)` tuple was enough and that a new class would add complexity I didn't need.
- **A mismatch in my own writing.** The review noticed that my reflection said pets have a "breed" while the code uses `species`, so I updated the reflection to match the code.

To verify the AI's code I didn't rely on it looking right:

- **Demo run:** I ran `main.py` with two pets and several tasks. I checked by hand that high-priority tasks came first, that start times added up correctly from the day start, and that a task was skipped when only 10 minutes were left.
- **Repeated calls:** I called `generate_plan()` twice in a row to confirm the plan didn't double up.
- **Completed tasks:** a task marked complete was correctly left out of the plan.
- **Tests:** I ran the pytest suite after every change. It started with two tests and ended with 31, all passing.

**c. AI strategy**

*Which AI features were most effective?*

- **Agent mode editing several files at once** was the biggest help. Recurring tasks, for example, touched `pawpal_system.py`, `main.py`, `app.py`, the tests and the UML in one change. Doing that by hand would have made it easy to update one file and forget another.
- **Running code and tests during the conversation** was just as important. The assistant ran `main.py`, `pytest`, and even simulated clicks in the Streamlit app, so problems showed up immediately instead of when I demoed the app. That's how we found that `st.selectbox` returns a *copy* of a Task, which meant "Mark complete" created tomorrow's task but never finished today's.
- **Asking it to explain test code** (like `pytest.raises` and the shared setup helper) before saving it helped me understand what each test actually proves.

*One AI suggestion I rejected or modified to keep the design clean:* when I asked how to simplify `detect_conflicts()`, the AI offered a faster version that sorts the tasks and breaks out of the loop early, and a shorter one-line list comprehension. I rejected both. For 5–20 tasks a day the speed gain is meaningless, and both versions are harder to read and easier to break. I kept only the `itertools.combinations` change, because it made the code *clearer*, not just shorter. Similarly, I rejected a separate `ScheduledItem` class because a tuple did the job.

*How did separate chat sessions help me stay organized?* To be honest, I did most of this project in one long chat session rather than opening a new one per phase. What kept it organized was working one checklist step at a time (one step per message), and committing at the end of each phase with a clear message: class skeletons, core implementation, algorithms, tests. Looking back, separate sessions would have helped in two ways. The testing phase would have started without the AI "remembering" how it meant the code to work, so it would be more likely to question that code, as an independent reviewer would. And each session would have stayed shorter and more focused. Next time I'd start a fresh session for planning algorithms and another for testing, and paste in a short summary of the design to start each one.

---

## 4. Testing and Verification

**a. What you tested**

The 31 tests in `tests/test_pawpal.py` cover:

- **Sorting:** tasks come back in chronological order; untimed tasks go last; `"8:00"` sorts before `"18:00"`; the plan follows priority → time → duration.
- **Recurring tasks:** daily tasks come back the next day and weekly tasks in 7 days; one-time tasks don't repeat. Also tested: overdue tasks, tasks completed early, Dec 31 → Jan 1 rollover, and that future copies stay out of today's plan.
- **Conflict detection:** exact same times and partial overlaps, for the same pet and across pets; tasks that only touch, completed tasks and future tasks are *not* flagged; invalid times give a warning instead of a crash.
- **Scheduling limits:** start times run back-to-back; exact fits are scheduled; zero minutes skips everything; the plan never passes midnight; re-running the plan doesn't duplicate tasks; empty owners and pets give an empty plan.
- **Basics:** marking complete, adding tasks, filtering by pet and status, and a clear error for a misspelled priority.

These tests mattered because scheduling bugs are quiet. Nothing crashes, the plan is just wrong, and a pet misses a meal. Writing edge-case tests found two real bugs that the demo never showed. First, `sort_tasks()` compared times as text, so `"8:00"` was treated as later than `"18:00"`. Second, a plan starting at 23:30 showed a task at `"24:00"`. One test also failed because *the test* was wrong: it expected the wrong order for two equal-priority tasks. Working out whether the bug was in the test or the code was a useful habit.

**b. Confidence**

I'd rate my confidence **4 out of 5**. All 31 tests pass, including the boundary and empty cases most likely to break a scheduler, and the app was tested end-to-end with simulated clicks. It isn't 5 because some things are still untested or unhandled. Next I would test:

- completing a recurring task after its pet has been removed (this currently raises an unclear error);
- two pets with the same name added in code, not through the app (filtering by name would mix their tasks up);
- `remove_task()` when a pet has several tasks with the same title (it removes all of them, including the history of completed recurring tasks);
- automated tests for the Streamlit UI, not just manual checks.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with how the backend and the UI ended up connected. Every feature in `pawpal_system.py` (sorting, filtering, recurrence and conflict warnings) is visible and usable in the app, and the conflict warnings are written for a pet owner, not a programmer. I'm also happy that the tests found real bugs instead of only confirming code I already believed worked.

**b. What you would improve**

- **Use preferred times in the plan itself.** Right now a 12:00 play session might run at 08:30. I'd try to start tasks at their preferred times where possible and only fall back to packing them in order.
- **Use the owner's preferences,** for example "walks in the morning".
- **Give tasks a unique ID** instead of looking them up by title or pet name. That would fix the duplicate-name issues above and the Streamlit selectbox problem.
- **Save data to a file,** so pets and tasks survive closing the browser.

**c. Key takeaway**

Being the "lead architect" with an AI assistant means owning the *decisions*, not the typing. The AI could write a whole feature across five files in seconds, but it couldn't decide whether conflicts should be resolved or only warned about, whether a faster algorithm was worth being harder to read, or whether a failing test meant the code was wrong or the test was. Those decisions shaped the system. The habits that worked best were to keep the design small until a feature was actually needed, to ask the AI narrow questions about specific files, and to never trust code just because it looked right: run it, test the edge cases, and check the output by hand.
