"""Demo script: build a sample owner with two pets and print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_tasks(heading: str, tasks: list[Task]) -> None:
    """Print a heading followed by one line per task."""
    print(f"\n{heading}")
    if not tasks:
        print("  (none)")
    for t in tasks:
        time_label = t.preferred_time or "--:--"
        status = "done" if t.completed else "pending"
        print(
            f"  {time_label}  {t.title} for {t.pet_name} ({t.duration_minutes} min) "
            f"[{status}, due {t.due_date}]"
        )


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90, day_start="07:30")

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of time order to show sort_by_time() working.
    mochi.add_task(Task("Brushing", 15, "low", category="grooming", preferred_time="18:00", frequency="weekly"))
    luna.add_task(Task("Play session", 20, "medium", category="enrichment", preferred_time="12:00"))
    mochi.add_task(Task("Morning walk", 30, "high", category="exercise", preferred_time="07:30", frequency="daily"))
    luna.add_task(Task("Litter box cleaning", 15, "medium", category="hygiene", preferred_time="17:00"))
    luna.add_task(Task("Give medication", 5, "high", category="meds", preferred_time="08:15", frequency="daily"))
    mochi.add_task(Task("Breakfast", 10, "high", category="feeding", preferred_time="08:00", frequency="daily"))
    mochi.add_task(Task("Fill water bowl", 2, "medium", category="feeding"))
    # Deliberate clashes to show detect_conflicts() working:
    luna.add_task(Task("Breakfast", 10, "high", category="feeding", preferred_time="08:00"))  # same time as Mochi's breakfast
    mochi.add_task(Task("Ear cleaning", 10, "low", category="grooming", preferred_time="07:45"))  # during Mochi's walk

    scheduler = Scheduler(owner)

    print("=" * 50)
    print("Recurring Tasks")
    print("=" * 50)
    medication = luna.tasks[2]
    next_meds = scheduler.mark_task_complete(medication)  # daily: next one due tomorrow
    print(f"\nCompleted '{medication.title}' ({medication.frequency}, due {medication.due_date}).")
    print(f"  Next occurrence created for {next_meds.pet_name}, due {next_meds.due_date}.")
    play = luna.tasks[0]
    print(f"\nCompleted '{play.title}' ({play.frequency}).")
    print(f"  Next occurrence: {scheduler.mark_task_complete(play)}")
    print(f"\nLuna now has {len(luna.tasks)} tasks; tomorrow's medication is not in today's plan.")
    print()

    print("=" * 50)
    print("Sorting and Filtering")
    print("=" * 50)
    print_tasks("All tasks (in the order they were added):", owner.get_all_tasks())
    print_tasks("All tasks sorted by time:", scheduler.sort_by_time(owner.get_all_tasks()))
    print_tasks("Luna's tasks:", owner.filter_tasks(pet_name="Luna"))
    print_tasks("Completed tasks:", owner.filter_tasks(completed=True))
    print_tasks(
        "Mochi's pending tasks, sorted by time:",
        scheduler.sort_by_time(owner.filter_tasks(pet_name="Mochi", completed=False)),
    )

    print()
    print("=" * 50)
    print("Conflict Check")
    print("=" * 50)
    conflicts = scheduler.detect_conflicts()
    for warning in conflicts or ["No conflicts found."]:
        print(f"  {warning}")

    scheduler.generate_plan()

    print()
    print("=" * 50)
    print("Today's Schedule")
    print("=" * 50)
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
