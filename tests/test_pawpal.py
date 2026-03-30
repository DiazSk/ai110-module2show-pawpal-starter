"""Automated tests for PawPal+ core logic."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


# ---------- Helpers ----------

def make_task(title="Walk", time="09:00", duration=20, priority="high", frequency="once") -> Task:
    return Task(title=title, time=time, duration_minutes=duration, priority=priority,
                frequency=frequency, due_date=date.today())


def make_scheduler_with_tasks(*pet_task_pairs) -> Scheduler:
    """Build an Owner/Scheduler from (pet_name, species, [Task, ...]) tuples."""
    owner = Owner("Test Owner")
    for pet_name, species, tasks in pet_task_pairs:
        pet = Pet(pet_name, species)
        for task in tasks:
            pet.add_task(task)
        owner.add_pet(pet)
    return Scheduler(owner)


# ---------- Tests ----------

def test_mark_complete_changes_status():
    task = make_task(frequency="once")
    assert task.completed is False
    result = task.mark_complete()
    assert task.completed is True
    assert result is None  # "once" tasks produce no next occurrence


def test_add_task_increases_count():
    pet = Pet("Mochi", "cat")
    assert len(pet.tasks) == 0
    pet.add_task(make_task("Breakfast", "08:00"))
    assert len(pet.tasks) == 1
    pet.add_task(make_task("Grooming", "11:00"))
    assert len(pet.tasks) == 2


def test_sort_by_time_chronological():
    tasks = [
        make_task("Dinner", "14:00"),
        make_task("Breakfast", "08:00"),
        make_task("Lunch", "11:30"),
    ]
    scheduler = make_scheduler_with_tasks(("Mochi", "cat", tasks))
    sorted_tasks = scheduler.sort_by_time()
    times = [task.time for _, task in sorted_tasks]
    assert times == ["08:00", "11:30", "14:00"]


def test_recurrence_creates_next_task():
    task = Task("Feeding", "08:00", 10, "high", frequency="daily", due_date=date.today())
    next_task = task.mark_complete()
    assert task.completed is True
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.title == "Feeding"


def test_conflict_detection():
    t1 = make_task("Walk", "09:00")
    t2 = make_task("Feeding", "09:00")   # same time — conflict
    t3 = make_task("Grooming", "10:00")  # different time — no conflict
    scheduler = make_scheduler_with_tasks(
        ("Mochi", "cat", [t1]),
        ("Buddy", "dog", [t2, t3]),
    )
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "09:00" in conflicts[0]
