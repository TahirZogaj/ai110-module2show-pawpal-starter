"""Quick tests for the PawPal+ logic layer."""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", 10, "high"))

    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_sort_by_time_orders_by_preferred_time_with_unset_last():
    owner = Owner("Jordan", 60)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Evening walk", 30, preferred_time="18:00"))
    pet.add_task(Task("Water", 2))
    pet.add_task(Task("Breakfast", 10, preferred_time="08:00"))

    ordered = Scheduler(owner).sort_by_time(pet.tasks)

    assert [t.title for t in ordered] == ["Breakfast", "Evening walk", "Water"]


def test_filter_tasks_by_pet_and_status():
    owner = Owner("Jordan", 60)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Walk", 30))
    luna.add_task(Task("Feeding", 10))
    luna.add_task(Task("Meds", 5))
    luna.tasks[1].mark_complete()

    assert [t.title for t in owner.filter_tasks(pet_name="Luna")] == ["Feeding", "Meds"]
    assert [t.title for t in owner.filter_tasks(completed=True)] == ["Meds"]
    assert [t.title for t in owner.filter_tasks(pet_name="Luna", completed=False)] == ["Feeding"]


def test_completing_daily_task_creates_next_day_occurrence():
    owner = Owner("Jordan", 60)
    pet = Pet("Luna", "cat")
    owner.add_pet(pet)
    meds = Task("Meds", 5, "high", frequency="daily")
    pet.add_task(meds)

    next_meds = Scheduler(owner).mark_task_complete(meds)

    assert meds.completed is True
    assert next_meds is not None
    assert next_meds.completed is False
    assert next_meds.due_date == date.today() + timedelta(days=1)
    assert next_meds.pet_name == "Luna"
    assert len(pet.tasks) == 2


def test_completing_weekly_task_creates_occurrence_seven_days_later():
    owner = Owner("Jordan", 60)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    bath = Task("Bath", 20, frequency="weekly")
    pet.add_task(bath)

    next_bath = Scheduler(owner).mark_task_complete(bath)

    assert next_bath.due_date == date.today() + timedelta(days=7)


def test_one_time_task_does_not_recur():
    owner = Owner("Jordan", 60)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    vet = Task("Vet visit", 60)
    pet.add_task(vet)

    assert Scheduler(owner).mark_task_complete(vet) is None
    assert len(pet.tasks) == 1


def test_future_occurrence_is_not_in_todays_plan():
    owner = Owner("Jordan", 60)
    pet = Pet("Luna", "cat")
    owner.add_pet(pet)
    feeding = Task("Feeding", 10, frequency="daily")
    pet.add_task(feeding)
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete(feeding)

    assert scheduler.generate_plan() == []


def _owner_with_two_pets():
    owner = Owner("Jordan", 120)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna


def test_detect_conflicts_flags_same_time_across_pets():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Breakfast", 10, preferred_time="08:00"))
    luna.add_task(Task("Breakfast", 10, preferred_time="08:00"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "Mochi" in warnings[0] and "Luna" in warnings[0]
    assert "different pets" in warnings[0]


def test_detect_conflicts_flags_overlap_for_same_pet():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30, preferred_time="07:30"))
    mochi.add_task(Task("Ear cleaning", 10, preferred_time="07:45"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "same pet" in warnings[0]


def test_back_to_back_tasks_are_not_conflicts():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30, preferred_time="07:30"))
    luna.add_task(Task("Feeding", 10, preferred_time="08:00"))
    mochi.add_task(Task("Water", 2))  # no preferred time, never conflicts

    assert Scheduler(owner).detect_conflicts() == []


def test_invalid_time_gives_warning_instead_of_crashing():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30, preferred_time="morning"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "invalid time" in warnings[0]
