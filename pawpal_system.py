"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from itertools import combinations

PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}  # any other frequency does not repeat


def _to_minutes(hhmm: str) -> int:
    """Convert "HH:MM" to minutes after midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _to_hhmm(total_minutes: int) -> str:
    """Convert minutes after midnight to "HH:MM"."""
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # must be a key of PRIORITY_SCORES
    category: str = "general"
    preferred_time: str = ""  # e.g. "08:00"; empty means no preference
    frequency: str = "once"  # "once", "daily", or "weekly"
    due_date: date = field(default_factory=date.today)
    pet_name: str = ""  # set by Pet.add_task so the plan can say which pet
    completed: bool = False

    def mark_complete(self) -> Task | None:
        """Mark this task as done and return its next occurrence if it recurs, else None.

        "daily" tasks come back 1 day later and "weekly" tasks 7 days later, counted
        from the later of the due date and today (so an overdue task isn't re-created
        already late). The copy keeps every field except due_date and completed.
        """
        self.completed = True
        days = RECURRENCE_DAYS.get(self.frequency)
        if days is None:
            return None
        # Count from today if the task was overdue, so the next one isn't already late.
        base = max(self.due_date, date.today())
        return replace(self, due_date=base + timedelta(days=days), completed=False)

    def is_due(self, on: date) -> bool:
        """Return True if the task is pending and due on or before the given date."""
        return not self.completed and self.due_date <= on

    def priority_score(self) -> int:
        """Return a numeric score for sorting (higher = more important)."""
        if self.priority not in PRIORITY_SCORES:
            raise ValueError(
                f"Unknown priority {self.priority!r} for task {self.title!r}; "
                f"expected one of {list(PRIORITY_SCORES)}"
            )
        return PRIORITY_SCORES[self.priority]


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    """A pet owner, their daily availability, and their pets."""

    name: str
    available_minutes: int
    day_start: str = "08:00"
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove the pet with the given name."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list[Task]:
        """Return tasks matching the given pet name and/or completion status.

        Each filter is optional: leaving it as None means "don't filter on this", so
        filter_tasks() returns everything and filter_tasks(pet_name="Luna",
        completed=False) returns only Luna's pending tasks.
        """
        return [
            t
            for t in self.get_all_tasks()
            if (pet_name is None or t.pet_name == pet_name)
            and (completed is None or t.completed == completed)
        ]


class Scheduler:
    """Builds and explains a daily care plan for an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner with an empty plan."""
        self.owner = owner
        self.scheduled: list[tuple[str, Task]] = []  # (start time "HH:MM", task)
        self.skipped: list[Task] = []
        self.conflicts: list[str] = []

    def generate_plan(self) -> list[tuple[str, Task]]:
        """Build a fresh plan of tasks due today that fit in the owner's available time.

        Greedy: clears the previous plan, records preferred-time conflicts, then walks
        the tasks in sort_tasks() order, giving each one the next start time from
        day_start if it fits in the minutes left and adding it to skipped otherwise.
        """
        self.scheduled = []
        self.skipped = []

        today = date.today()
        pending = [t for t in self.owner.get_all_tasks() if t.is_due(today)]
        self.conflicts = self.detect_conflicts(pending)
        minutes_left = self.owner.available_minutes
        clock = _to_minutes(self.owner.day_start)

        for task in self.sort_tasks(pending):
            if self.fits_in_time(task, minutes_left):
                self.scheduled.append((_to_hhmm(clock), task))
                clock += task.duration_minutes
                minutes_left -= task.duration_minutes
            else:
                self.skipped.append(task)

        return self.scheduled

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task and, if it recurs, add the next occurrence to the same pet.

        Returns the new Task (due on a later date, so it won't appear in today's plan)
        or None for one-time tasks.
        """
        next_task = task.mark_complete()
        if next_task is not None:
            pet = next(p for p in self.owner.pets if p.name == task.pet_name)
            pet.add_task(next_task)
        return next_task

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by priority, then earliest preferred time, then shortest duration."""
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority_score(),
                t.preferred_time == "",
                t.preferred_time,
                t.duration_minutes,
            ),
        )

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by preferred time ("HH:MM"), with no-preference tasks last.

        The sort key is (has no time, minutes after midnight). Converting to minutes
        keeps the order right even for unpadded times like "8:00" vs "18:00".
        """
        return sorted(
            tasks,
            key=lambda t: (
                t.preferred_time == "",
                _to_minutes(t.preferred_time) if t.preferred_time else 0,
            ),
        )

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return warning messages for tasks whose preferred time windows overlap.

        Each task with a preferred time becomes a [start, start + duration) window, and
        every pair is compared (O(n^2), fine for a day's tasks). Windows that only touch,
        like 07:30-08:00 and 08:00-08:10, don't count. Tasks without a time are ignored,
        and an unreadable time produces a warning instead of raising an error. Checks
        across all pets, since the owner can only do one thing at a time.
        Defaults to every pending task due today.
        """
        if tasks is None:
            tasks = [t for t in self.owner.get_all_tasks() if t.is_due(date.today())]

        warnings = []
        windows = []  # (start, end, task) for tasks with a usable preferred time
        for t in tasks:
            if not t.preferred_time:
                continue
            try:
                start = _to_minutes(t.preferred_time)
            except ValueError:
                warnings.append(
                    f"Warning: '{t.title}' for {t.pet_name} has an invalid time "
                    f"{t.preferred_time!r}; skipped in conflict check."
                )
                continue
            windows.append((start, start + t.duration_minutes, t))

        # Check every pair: two windows overlap when each starts before the other ends.
        for (a_start, a_end, a), (b_start, b_end, b) in combinations(windows, 2):
            if a_start < b_end and b_start < a_end:
                scope = "same pet" if a.pet_name == b.pet_name else "different pets"
                warnings.append(
                    f"Warning: '{a.title}' for {a.pet_name} "
                    f"({_to_hhmm(a_start)}-{_to_hhmm(a_end)}) overlaps '{b.title}' "
                    f"for {b.pet_name} ({_to_hhmm(b_start)}-{_to_hhmm(b_end)}) [{scope}]."
                )
        return warnings

    def fits_in_time(self, task: Task, minutes_left: int) -> bool:
        """Return True if the task fits in the remaining minutes."""
        return task.duration_minutes <= minutes_left

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the generated plan."""
        if not self.scheduled and not self.skipped:
            return "No pending tasks to schedule."

        used = sum(task.duration_minutes for _, task in self.scheduled)
        lines = [
            f"Daily plan for {self.owner.name} "
            f"({used} of {self.owner.available_minutes} minutes used):"
        ]
        for start, task in self.scheduled:
            lines.append(
                f"  {start} - {task.title} for {task.pet_name} "
                f"({task.duration_minutes} min) [priority: {task.priority}]"
            )
        lines.append(
            "Tasks were ordered by priority, then preferred time, then shortest first."
        )

        if self.skipped:
            lines.append("Skipped (not enough time left):")
            for task in self.skipped:
                lines.append(
                    f"  {task.title} for {task.pet_name} "
                    f"({task.duration_minutes} min) [priority: {task.priority}]"
                )

        if self.conflicts:
            lines.append("Time conflicts in preferred times:")
            lines.extend(f"  {warning}" for warning in self.conflicts)
        return "\n".join(lines)
