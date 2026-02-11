"""Task management module for storing and retrieving tasks."""
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import TASKS_FILE, EST


class TaskManager:
    """Manages task storage and retrieval."""
    
    def __init__(self):
        """Initialize task manager and load tasks from disk."""
        self.tasks: List[Dict[str, Any]] = self._load_tasks()
    
    def _load_tasks(self) -> List[Dict[str, Any]]:
        """Load tasks from disk."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
            
            if os.path.exists(TASKS_FILE):
                with open(TASKS_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert due dates back to datetime objects
                    for task in data:
                        if task.get('due'):
                            task['due'] = datetime.fromisoformat(task['due']).replace(tzinfo=EST)
                    print(f"✅ Loaded {len(data)} tasks from {TASKS_FILE}")
                    return data
            else:
                print(f"ℹ️ No tasks file found at {TASKS_FILE}")
        except Exception as e:
            print(f"❌ Error loading tasks: {e}")
        return []
    
    def _save_tasks(self) -> None:
        """Save tasks to disk."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
            
            # Convert datetime objects to ISO strings for JSON
            data = []
            for task in self.tasks:
                task_copy = task.copy()
                if task_copy.get('due'):
                    task_copy['due'] = task_copy['due'].isoformat()
                data.append(task_copy)
            
            with open(TASKS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Saved {len(data)} tasks to {TASKS_FILE}")
        except Exception as e:
            print(f"❌ Error saving tasks: {e}")
    
    def add_task(self, task_text: str, due_time: Optional[datetime] = None, 
                 reminder_minutes: int = 60) -> Dict[str, Any]:
        """
        Add a new task.
        
        Args:
            task_text: Description of the task
            due_time: When the task is due (optional)
            reminder_minutes: Minutes before due time to send reminder
            
        Returns:
            The created task dictionary
        """
        task = {
            "task": task_text,
            "due": due_time,
            "reminder_minutes": reminder_minutes,
            "reminded": False,
        }
        self.tasks.append(task)
        self._save_tasks()
        return task
    
    def remove_task(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Remove a task by index.
        
        Args:
            index: Index of the task to remove
            
        Returns:
            The removed task dictionary, or None if index is invalid
        """
        if 0 <= index < len(self.tasks):
            removed = self.tasks.pop(index)
            self._save_tasks()
            return removed
        return None
    
    def find_task_by_text(self, search_text: str) -> Optional[int]:
        """
        Find a task by searching its text.
        
        Args:
            search_text: Text to search for in task descriptions
            
        Returns:
            Index of the found task, or None if not found
        """
        search_lower = search_text.lower()
        for i, task_obj in enumerate(self.tasks):
            existing = task_obj["task"]
            if search_lower in existing.lower() or existing.lower() in search_lower:
                return i
        return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks."""
        return self.tasks
    
    def get_task_count(self) -> int:
        """Get the total number of tasks."""
        return len(self.tasks)
    
    def mark_reminded(self, index: int) -> None:
        """Mark a task as reminded."""
        if 0 <= index < len(self.tasks):
            self.tasks[index]["reminded"] = True
            self._save_tasks()
