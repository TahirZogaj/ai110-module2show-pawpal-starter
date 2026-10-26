from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
col1, col2, col3 = st.columns(3)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input(
        "Minutes available today", min_value=0, max_value=1440, value=60
    )
with col3:
    day_start = st.time_input("Day starts at", value=time(8, 0))

# Streamlit reruns this script on every interaction, so keep the Owner in
# session_state and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_minutes=60)
owner = st.session_state.owner
owner.name = owner_name
owner.available_minutes = int(available_minutes)
owner.day_start = day_start.strftime("%H:%M")

st.markdown("### Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        name = pet_name.strip()
        if not name:
            st.error("Please enter a pet name.")
        elif any(p.name == name for p in owner.pets):
            st.error(f"{owner.name} already has a pet named {name}.")
        else:
            owner.add_pet(Pet(name=name, species=species, age=int(age)))
            st.success(f"Added {name}.")

if owner.pets:
    st.table(
        [
            {"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
            for p in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
if not owner.pets:
    st.caption("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            task_pet = st.selectbox("Pet", [p.name for p in owner.pets])
            task_title = st.text_input("Task title", value="Morning walk")
            category = st.selectbox(
                "Category",
                ["exercise", "feeding", "meds", "grooming", "enrichment", "hygiene", "general"],
            )
        with col2:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            preferred = st.time_input("Preferred time (optional)", value=None)
            frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == task_pet)
            pet.add_task(
                Task(
                    title=task_title.strip() or "Untitled task",
                    duration_minutes=int(duration),
                    priority=priority,
                    category=category,
                    preferred_time=preferred.strftime("%H:%M") if preferred else "",
                    frequency=frequency,
                )
            )
            st.success(f"Added {task_title} for {pet.name}.")

scheduler = Scheduler(owner)


def task_rows(tasks: list[Task]) -> list[dict]:
    """Turn tasks into table rows for st.table."""
    return [
        {
            "Time": t.preferred_time or "—",
            "Pet": t.pet_name,
            "Task": t.title,
            "Minutes": t.duration_minutes,
            "Priority": t.priority,
            "Repeats": t.frequency,
            "Due": t.due_date.isoformat(),
            "Status": "✅ Done" if t.completed else "Pending",
        }
        for t in tasks
    ]


def show_conflicts(conflicts: list[str]) -> None:
    """Show time conflicts as one warning with a suggestion the owner can act on."""
    if not conflicts:
        return
    lines = "\n".join(f"- {c.removeprefix('Warning: ')}" for c in conflicts)
    st.warning(
        f"**⚠️ {len(conflicts)} time conflict(s) in your preferred times**\n\n{lines}\n\n"
        "You can only do one thing at a time. Consider moving one of these tasks to a "
        "different time, or ask someone to help. The schedule below still runs them one "
        "after another, highest priority first."
    )


if owner.get_all_tasks():
    st.markdown("#### Task list")
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.radio(
            "Show status", ["All", "Pending", "Completed"], horizontal=True
        )

    filtered = owner.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
    )
    if filtered:
        st.caption("Sorted by preferred time; tasks with no time are listed last.")
        st.table(task_rows(scheduler.sort_by_time(filtered)))
    else:
        st.info("No tasks match these filters.")

    show_conflicts(scheduler.detect_conflicts())

    pending = scheduler.sort_by_time(owner.filter_tasks(completed=False))
    if pending:
        st.markdown("#### Mark a task complete")
        col1, col2 = st.columns([3, 1])
        with col1:
            # Select by index: st.selectbox returns a copy of object options, and we
            # need the real Task stored on the pet.
            choice = st.selectbox(
                "Task",
                range(len(pending)),
                format_func=lambda i: (
                    f"{pending[i].preferred_time or '--:--'}  {pending[i].title} for "
                    f"{pending[i].pet_name} (due {pending[i].due_date.isoformat()})"
                ),
                label_visibility="collapsed",
            )
            to_complete = pending[choice]
        with col2:
            if st.button("Mark complete", use_container_width=True):
                next_task = scheduler.mark_task_complete(to_complete)
                if next_task:
                    st.session_state.flash = (
                        f"Completed {to_complete.title} for {to_complete.pet_name}. "
                        f"It repeats {to_complete.frequency}, so the next one is due "
                        f"{next_task.due_date.isoformat()}."
                    )
                else:
                    st.session_state.flash = (
                        f"Completed {to_complete.title} for {to_complete.pet_name}."
                    )
                st.rerun()
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))
elif owner.pets:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption(
    "Plans every pet's tasks that are due today by priority, then preferred time, "
    "then shortest first, until the available time runs out."
)

if st.button("Generate schedule", type="primary"):
    plan = scheduler.generate_plan()
    if not plan and not scheduler.skipped:
        st.info("No tasks are due today. Nothing to schedule.")
    else:
        used = sum(t.duration_minutes for _, t in plan)
        if plan:
            st.success(
                f"Scheduled {len(plan)} task(s) for {owner.name}, using {used} of "
                f"{owner.available_minutes} available minutes."
            )
            st.markdown("#### Today's Schedule")
            st.table(
                [
                    {
                        "Start": start,
                        "Pet": t.pet_name,
                        "Task": t.title,
                        "Minutes": t.duration_minutes,
                        "Priority": t.priority,
                        "Preferred": t.preferred_time or "—",
                    }
                    for start, t in plan
                ]
            )
        if scheduler.skipped:
            st.warning(
                "**Skipped, not enough time left:** "
                + ", ".join(
                    f"{t.title} for {t.pet_name} ({t.duration_minutes} min, {t.priority})"
                    for t in scheduler.skipped
                )
                + ". Add more available minutes to fit them in."
            )
        show_conflicts(scheduler.conflicts)
        with st.expander("Why this plan?"):
            st.text(scheduler.explain_plan())
