"""PawPal+ logic layer: Task, Pet, Owner, and Scheduler classes."""

from __future__ import annotations

import copy
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class Task:
    """A single pet care activity."""

    title: str
    time: str  # "HH:MM" format, e.g. "08:30"
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"
    frequency: str = "once"  # "once" | "daily" | "weekly"
    completed: bool = False
    due_date: Optional[date] = None

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete and return the next occurrence for recurring tasks."""
        self.completed = True
        if self.frequency == "daily":
            next_task = copy.copy(self)
            next_task.completed = False
            next_task.due_date = date.today() + timedelta(days=1)
            return next_task
        elif self.frequency == "weekly":
            next_task = copy.copy(self)
            next_task.completed = False
            next_task.due_date = date.today() + timedelta(days=7)
            return next_task
        return None


@dataclass
class Pet:
    """A pet belonging to an owner."""

    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove the first task matching title (case-insensitive). Returns True if found."""
        for i, task in enumerate(self.tasks):
            if task.title.lower() == title.lower():
                self.tasks.pop(i)
                return True
        return False


class Owner:
    """An owner who manages one or more pets."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[tuple[str, Task]]:
        """Return a flat list of (pet_name, task) tuples across all pets."""
        result = []
        for pet in self.pets:
            for task in pet.tasks:
                result.append((pet.name, task))
        return result


_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    """Service object that provides scheduling algorithms over an Owner's pets and tasks."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def sort_by_time(self) -> List[tuple[str, Task]]:
        """Return all tasks sorted chronologically by time (HH:MM lexicographic order)."""
        return sorted(self.owner.get_all_tasks(), key=lambda pair: pair[1].time)

    def sort_by_priority_then_time(self) -> List[tuple[str, Task]]:
        """Return all tasks sorted by priority (high → medium → low) then by time."""
        return sorted(
            self.owner.get_all_tasks(),
            key=lambda pair: (_PRIORITY_ORDER.get(pair[1].priority, 9), pair[1].time),
        )

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[tuple[str, Task]]:
        """Return tasks filtered by pet name and/or completion status."""
        result = self.owner.get_all_tasks()
        if pet_name is not None:
            result = [(n, t) for n, t in result if n == pet_name]
        if completed is not None:
            result = [(n, t) for n, t in result if t.completed == completed]
        return result

    def get_todays_schedule(self) -> List[tuple[str, Task]]:
        """Return today's incomplete tasks sorted by priority then time."""
        today = date.today()
        all_sorted = self.sort_by_priority_then_time()
        return [
            (name, task)
            for name, task in all_sorted
            if not task.completed
            and (task.due_date is None or task.due_date == today)
        ]

    def detect_conflicts(self) -> List[str]:
        """Return warning strings for incomplete tasks scheduled at the same time."""
        time_map: dict[str, list[str]] = defaultdict(list)
        for pet_name, task in self.owner.get_all_tasks():
            if not task.completed:
                time_map[task.time].append(f"{pet_name}: {task.title}")
        warnings = []
        for time_str, entries in time_map.items():
            if len(entries) > 1:
                conflicts_str = " vs. ".join(entries)
                warnings.append(f"Conflict at {time_str}: {conflicts_str}")
        return warnings

    def mark_task_complete(self, pet_name: str, task_title: str) -> bool:
        """Mark a task complete; adds next occurrence to the pet if recurring. Returns True if found."""
        for pet in self.owner.pets:
            if pet.name != pet_name:
                continue
            for task in pet.tasks:
                if task.title.lower() == task_title.lower():
                    next_task = task.mark_complete()
                    if next_task is not None:
                        pet.add_task(next_task)
                    return True
        return False
