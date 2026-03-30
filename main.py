"""CLI demo script for PawPal+. Run: python main.py"""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    # --- Build the object graph ---
    owner = Owner("Jordan")

    mochi = Pet("Mochi", "cat")
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", frequency="daily", due_date=date.today()))
    mochi.add_task(Task("Grooming", "11:30", 15, "medium", due_date=date.today()))
    mochi.add_task(Task("Playtime", "14:00", 20, "low", due_date=date.today()))

    buddy = Pet("Buddy", "dog")
    buddy.add_task(Task("Morning walk", "08:00", 30, "high", due_date=date.today()))  # conflict with Mochi breakfast
    buddy.add_task(Task("Lunch feeding", "12:30", 10, "high", frequency="daily", due_date=date.today()))
    buddy.add_task(Task("Evening walk", "17:00", 30, "medium", due_date=date.today()))

    owner.add_pet(mochi)
    owner.add_pet(buddy)

    scheduler = Scheduler(owner)

    # --- Today's schedule (sorted) ---
    print("=" * 50)
    print(f"Today's Schedule for {owner.name}")
    print("=" * 50)
    schedule = scheduler.get_todays_schedule()
    if schedule:
        for pet_name, task in schedule:
            print(
                f"  {task.time}  [{task.priority.upper():6}]  {pet_name}: {task.title}"
                f"  ({task.duration_minutes} min, {task.frequency})"
            )
    else:
        print("  No tasks scheduled for today.")

    # --- Conflict detection ---
    print()
    print("Conflict Warnings:")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  ⚠️  {warning}")
    else:
        print("  No conflicts detected.")

    # --- Mark a recurring task complete and show next occurrence ---
    print()
    print("Marking Mochi's Breakfast complete...")
    scheduler.mark_task_complete("Mochi", "Breakfast")
    mochi_tasks = [(n, t) for n, t in owner.get_all_tasks() if n == "Mochi"]
    print("Mochi's updated tasks:")
    for _, task in mochi_tasks:
        status = "done" if task.completed else f"due {task.due_date}"
        print(f"  {task.title} — {status}")


if __name__ == "__main__":
    main()
