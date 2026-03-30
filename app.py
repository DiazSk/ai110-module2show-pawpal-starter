from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

_PRIORITY_EMOJI = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to **PawPal+** — a pet care scheduling assistant. Add your pets and their tasks,
then generate a sorted daily schedule with conflict detection.
"""
)

# ---------- Session state ----------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------- Owner & pet inputs ----------
st.subheader("Owner & Pet")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# ---------- Task inputs ----------
st.markdown("### Add a Task")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    task_time = st.text_input("Time (HH:MM)", value="09:00")
with col3:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)

col4, col5 = st.columns(2)
with col4:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col5:
    frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

if st.button("Add task"):
    # Create or reuse Owner
    if st.session_state.owner is None or st.session_state.owner.name != owner_name:
        st.session_state.owner = Owner(owner_name)

    owner: Owner = st.session_state.owner

    # Find or create the pet
    existing_pet = next((p for p in owner.pets if p.name == pet_name), None)
    if existing_pet is None:
        existing_pet = Pet(pet_name, species)
        owner.add_pet(existing_pet)

    # Create and add the task
    task = Task(
        title=task_title,
        time=task_time,
        duration_minutes=int(duration),
        priority=priority,
        frequency=frequency,
        due_date=date.today(),
    )
    existing_pet.add_task(task)

    # Refresh the scheduler
    st.session_state.scheduler = Scheduler(owner)
    st.success(f"Added '{task_title}' to {pet_name}.")

# ---------- Current tasks table ----------
if st.session_state.owner is not None:
    all_tasks = st.session_state.owner.get_all_tasks()
    if all_tasks:
        st.write("**Current tasks (all pets):**")
        rows = [
            {
                "Pet": pn,
                "Task": t.title,
                "Time": t.time,
                "Duration (min)": t.duration_minutes,
                "Priority": _PRIORITY_EMOJI.get(t.priority, t.priority),
                "Frequency": t.frequency,
                "Done": "✅" if t.completed else "⬜",
            }
            for pn, t in all_tasks
        ]
        st.table(rows)
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------- Generate schedule ----------
st.subheader("Generate Schedule")
st.caption("Produces a sorted daily schedule for all pets and highlights any time conflicts.")

if st.button("Generate schedule"):
    if st.session_state.scheduler is None:
        st.info("Add at least one task first.")
    else:
        scheduler: Scheduler = st.session_state.scheduler

        # Today's sorted schedule (priority-first, then time)
        schedule = scheduler.get_todays_schedule()
        st.markdown("#### Today's Schedule")
        st.caption("Sorted by priority (🔴 High → 🟡 Medium → 🟢 Low), then by time within each tier.")
        if schedule:
            rows = [
                {
                    "Priority": _PRIORITY_EMOJI.get(t.priority, t.priority),
                    "Time": t.time,
                    "Pet": pn,
                    "Task": t.title,
                    "Duration (min)": t.duration_minutes,
                    "Frequency": t.frequency,
                }
                for pn, t in schedule
            ]
            st.dataframe(rows, use_container_width=True)
        else:
            st.info("No incomplete tasks scheduled for today.")

        # Conflict warnings
        st.markdown("#### Conflict Check")
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            for msg in conflicts:
                st.warning(msg)
        else:
            st.success("No conflicts detected — your schedule is clear!")
