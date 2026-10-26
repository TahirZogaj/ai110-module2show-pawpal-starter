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

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.table(
        [
            {
                "Pet": t.pet_name,
                "Task": t.title,
                "Minutes": t.duration_minutes,
                "Priority": t.priority,
                "Preferred time": t.preferred_time or "-",
                "Repeats": t.frequency,
                "Due": t.due_date.isoformat(),
                "Done": "✅" if t.completed else "",
            }
            for t in all_tasks
        ]
    )
elif owner.pets:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption(
    "Plans every pet's pending tasks by priority, then preferred time, "
    "then shortest first, until the available time runs out."
)

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()
    if not plan and not scheduler.skipped:
        st.info("No pending tasks to schedule.")
    else:
        if plan:
            st.markdown("#### Today's Schedule")
            st.table(
                [
                    {
                        "Start": start,
                        "Pet": t.pet_name,
                        "Task": t.title,
                        "Minutes": t.duration_minutes,
                        "Priority": t.priority,
                    }
                    for start, t in plan
                ]
            )
        for warning in scheduler.conflicts:
            st.warning(warning)
        if scheduler.skipped:
            st.warning(
                "Skipped (not enough time left): "
                + ", ".join(f"{t.title} for {t.pet_name}" for t in scheduler.skipped)
            )
        with st.expander("Why this plan?"):
            st.text(scheduler.explain_plan())
