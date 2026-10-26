"""Quick tests for the PawPal+ logic layer."""

from datetime import date, timedelta

import pytest

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


# --- Sorting edge cases ---


def test_sort_by_time_handles_unpadded_hours():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.add_task(Task("Dinner", 10, preferred_time="18:00"))
    mochi.add_task(Task("Breakfast", 10, preferred_time="8:00"))

    ordered = Scheduler(owner).sort_by_time(mochi.tasks)

    assert [t.title for t in ordered] == ["Breakfast", "Dinner"]


def test_plan_order_is_priority_then_time_then_duration():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Brushing", 15, "low", preferred_time="07:00"))
    mochi.add_task(Task("Dinner", 10, "high", preferred_time="18:00"))
    luna.add_task(Task("Breakfast", 10, "high", preferred_time="8:00"))  # unpadded
    luna.add_task(Task("Long play", 20, "medium"))
    luna.add_task(Task("Short play", 5, "medium"))

    plan = Scheduler(owner).generate_plan()

    assert [t.title for _, t in plan] == [
        "Breakfast", "Dinner", "Short play", "Long play", "Brushing",
    ]


# --- Scheduling edge cases ---


def test_owner_with_no_pets_gets_empty_plan():
    scheduler = Scheduler(Owner("Jordan", 60))

    assert scheduler.generate_plan() == []
    assert scheduler.explain_plan() == "No pending tasks to schedule."


def test_pet_with_no_tasks_gets_empty_plan():
    owner, _, _ = _owner_with_two_pets()

    assert Scheduler(owner).generate_plan() == []


def test_start_times_are_back_to_back_from_day_start():
    owner = Owner("Jordan", 60, day_start="07:30")
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high"))
    pet.add_task(Task("Breakfast", 10, "medium"))

    plan = Scheduler(owner).generate_plan()

    assert [(start, t.title) for start, t in plan] == [("07:30", "Walk"), ("08:00", "Breakfast")]


def test_task_that_exactly_fits_is_scheduled():
    owner = Owner("Jordan", 30)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30))

    scheduler = Scheduler(owner)

    assert len(scheduler.generate_plan()) == 1
    assert scheduler.skipped == []


def test_zero_available_minutes_skips_everything():
    owner = Owner("Jordan", 0)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30))
    pet.add_task(Task("Water", 2))

    scheduler = Scheduler(owner)

    assert scheduler.generate_plan() == []
    assert [t.title for t in scheduler.skipped] == ["Water", "Walk"]  # shorter first on ties


def test_generate_plan_twice_does_not_duplicate():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30))
    scheduler = Scheduler(owner)

    scheduler.generate_plan()
    scheduler.generate_plan()

    assert len(scheduler.scheduled) == 1


def test_overdue_task_is_still_planned():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.add_task(Task("Nail trim", 15, due_date=date.today() - timedelta(days=2)))

    assert len(Scheduler(owner).generate_plan()) == 1


def test_plan_does_not_run_past_midnight():
    owner = Owner("Jordan", 120, day_start="23:30")
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Late walk", 20, "high"))
    pet.add_task(Task("Bedtime brushing", 15, "low"))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    assert [(start, t.title) for start, t in plan] == [("23:30", "Late walk")]
    assert [t.title for t in scheduler.skipped] == ["Bedtime brushing"]


def test_unknown_priority_raises_clear_error():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30, priority="urgent"))

    with pytest.raises(ValueError, match="Unknown priority 'urgent'"):
        Scheduler(owner).generate_plan()


# --- Recurrence edge cases ---


def test_overdue_daily_task_next_due_tomorrow_not_in_past():
    owner, mochi, _ = _owner_with_two_pets()
    walk = Task("Walk", 30, frequency="daily", due_date=date.today() - timedelta(days=3))
    mochi.add_task(walk)

    next_walk = Scheduler(owner).mark_task_complete(walk)

    assert next_walk.due_date == date.today() + timedelta(days=1)


def test_weekly_task_completed_early_counts_from_due_date():
    owner, mochi, _ = _owner_with_two_pets()
    due = date.today() + timedelta(days=3)
    bath = Task("Bath", 20, frequency="weekly", due_date=due)
    mochi.add_task(bath)

    next_bath = Scheduler(owner).mark_task_complete(bath)

    assert next_bath.due_date == due + timedelta(days=7)


def test_recurrence_rolls_over_to_new_year():
    owner, mochi, _ = _owner_with_two_pets()
    nye = date(date.today().year + 1, 12, 31)
    feeding = Task("Feeding", 10, frequency="daily", due_date=nye)
    mochi.add_task(feeding)

    next_feeding = Scheduler(owner).mark_task_complete(feeding)

    assert next_feeding.due_date == date(nye.year + 1, 1, 1)


def test_next_occurrence_keeps_task_details():
    owner, _, luna = _owner_with_two_pets()
    meds = Task("Meds", 5, "high", category="meds", preferred_time="08:15", frequency="daily")
    luna.add_task(meds)

    next_meds = Scheduler(owner).mark_task_complete(meds)

    assert (next_meds.title, next_meds.priority, next_meds.preferred_time, next_meds.category) == (
        "Meds", "high", "08:15", "meds",
    )
    assert next_meds is not meds


# --- Conflict edge cases ---


def test_three_overlapping_tasks_give_one_warning_per_pair():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30, preferred_time="08:00"))
    luna.add_task(Task("Feeding", 10, preferred_time="08:00"))
    mochi.add_task(Task("Meds", 5, preferred_time="08:05"))

    assert len(Scheduler(owner).detect_conflicts()) == 3


def test_completed_and_future_tasks_are_not_conflicts():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30, preferred_time="08:00"))
    done = Task("Feeding", 10, preferred_time="08:00")
    luna.add_task(done)
    done.mark_complete()
    luna.add_task(Task("Meds", 5, preferred_time="08:00", due_date=date.today() + timedelta(days=1)))

    assert Scheduler(owner).detect_conflicts() == []


def test_conflicts_appear_in_plan_explanation():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Breakfast", 10, preferred_time="08:00"))
    luna.add_task(Task("Breakfast", 10, preferred_time="08:00"))
    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    assert len(scheduler.conflicts) == 1
    assert "Time conflicts" in scheduler.explain_plan()


# --- Filtering edge cases ---


def test_filter_by_unknown_pet_returns_empty_list():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30))

    assert owner.filter_tasks(pet_name="Rex") == []
