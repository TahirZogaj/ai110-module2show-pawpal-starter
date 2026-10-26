"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    category: str = "general"
    preferred_time: str = ""  # e.g. "08:00"; empty means no preference
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def priority_score(self) -> int:
        """Return a numeric score for sorting (higher = more important)."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        pass

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        pass


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
        pass

    def remove_pet(self, name: str) -> None:
        """Remove the pet with the given name."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        pass


class Scheduler:
    """Builds and explains a daily care plan for an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.scheduled: list[Task] = []
        self.skipped: list[Task] = []

    def generate_plan(self) -> list[Task]:
        """Choose and order tasks that fit in the owner's available time."""
        pass

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority (and other tie-breakers)."""
        pass

    def fits_in_time(self, task: Task, minutes_left: int) -> bool:
        """Return True if the task fits in the remaining minutes."""
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the generated plan."""
        pass
