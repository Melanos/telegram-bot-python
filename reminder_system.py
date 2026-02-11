"""Reminder system for checking and sending task reminders."""
from datetime import datetime, timedelta
from typing import Callable
from config import EST


def check_reminders(task_manager, send_reminder_callback: Callable):
    """
    Check for upcoming tasks and send reminders.
    
    Args:
        task_manager: TaskManager instance
        send_reminder_callback: Function to call to send reminder (takes task_index, message)
    """
    now = datetime.now(EST)
    print(f"🔔 Checking reminders at {now}")
    
    for idx, task_obj in enumerate(task_manager.get_all_tasks()):
        due_time = task_obj.get("due")
        if not due_time or task_obj.get("reminded"):
            continue
        
        # Ensure due_time is timezone-aware
        if due_time.tzinfo is None:
            due_time = EST.localize(due_time)
        
        reminder_minutes = task_obj.get("reminder_minutes", 60)
        reminder_time = due_time - timedelta(minutes=reminder_minutes)
        
        time_diff_seconds = (now - reminder_time).total_seconds()
        
        print(f"  Task: {task_obj['task']}, due: {due_time}, reminder: {reminder_time}, diff: {time_diff_seconds}s")
        
        # Within 2-minute window
        if 0 <= time_diff_seconds <= 120:
            send_reminder_callback(idx, task_obj)
