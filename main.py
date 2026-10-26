"""Demo script: build a sample owner with two pets and print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90, day_start="07:30")

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", 30, "high", category="exercise", preferred_time="07:30"))
    mochi.add_task(Task("Breakfast", 10, "high", category="feeding", preferred_time="08:00"))
    luna.add_task(Task("Give medication", 5, "high", category="meds", preferred_time="08:15"))
    luna.add_task(Task("Play session", 20, "medium", category="enrichment", preferred_time="12:00"))
    mochi.add_task(Task("Brushing", 15, "low", category="grooming", preferred_time="18:00"))
    luna.add_task(Task("Litter box cleaning", 15, "medium", category="hygiene", preferred_time="17:00"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    print("=" * 50)
    print("Today's Schedule")
    print("=" * 50)
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
