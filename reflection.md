# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

### 1a. Initial Design

The PawPal+ application will allow users to perform three main actions:

1. **Add and Manage Pet Information:** Users can add their pets by entering basic information such as their name, age, breed, and specific care needs.

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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

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
- **Implementation:** in agent mode, it wrote out the four classes, the `main.py` demo script and the pytest tests.
- **Documentation:** it added the docstrings and drafted the README summary.

The most helpful prompts were narrow ones with a clear goal, like "review this skeleton for missing relationships or bottlenecks" or "check that relationships make sense and there's no unnecessary complexity." Pointing the AI at a specific file with a specific question got concrete, usable answers instead of generic advice.

**What AI suggested and what I accepted**

From the skeleton review I accepted three changes:

- adding `pet_name` to `Task`, so the schedule can say which pet a task is for;
- storing start times in the schedule, so it shows *when* each task happens and not just the order;
- a single `PRIORITY_SCORES` mapping, so a misspelled priority raises an error instead of sorting wrong.

I also kept its warning that `generate_plan()` must clear the old plan first, because Streamlit reruns the script.

**b. Judgment and verification**

I didn't accept every suggestion as-is:

- **Some features came out of the first draft.** The first UML draft included task frequency, an `is_due_today()` method and a `detect_conflicts()` method. I removed them during the complexity review because the first version of the scheduler didn't need them. Later, the assignment's Task description asked for frequency, so I added that field back. Frequency is stored but not yet used in scheduling.
- **No new class for scheduled items.** The review suggested scheduled items could become their own class. I decided a `(start_time, task)` tuple was enough for now and that a new class would add complexity before I needed it.
- **A mismatch in my own writing.** The review noticed that my reflection said pets have a "breed" while the code uses `species`, so I knew to make the two consistent.

To verify the AI's code I didn't rely on it looking right:

- **Demo run:** I ran `main.py` with two pets and six tasks. I checked by hand that high-priority tasks came first, that start times added up correctly from 07:30, and that the 15-minute brushing task was skipped because only 10 minutes were left.
- **Repeated calls:** I called `generate_plan()` twice in a row to confirm the plan didn't double up.
- **Completed tasks:** a task marked complete was correctly left out of the plan.
- **Tests:** I ran the pytest tests (task completion and task addition), and both pass.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
