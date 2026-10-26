"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field

PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}


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
    frequency: str = "daily"  # e.g. "daily", "weekly"
    pet_name: str = ""  # set by Pet.add_task so the plan can say which pet
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

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


class Scheduler:
    """Builds and explains a daily care plan for an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner with an empty plan."""
        self.owner = owner
        self.scheduled: list[tuple[str, Task]] = []  # (start time "HH:MM", task)
        self.skipped: list[Task] = []

    def generate_plan(self) -> list[tuple[str, Task]]:
        """Build a fresh plan of pending tasks that fit in the owner's available time."""
        self.scheduled = []
        self.skipped = []

        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
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
        return "\n".join(lines)
