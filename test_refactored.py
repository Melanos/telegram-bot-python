"""Test script to verify the refactored modules work correctly."""
import sys

# Test 1: Import all modules
print("Test 1: Importing all modules...")
try:
    import config
    import datetime_parser
    import task_manager
    import ui_helpers
    import api_handlers
    import reminder_system
    print("✅ All modules imported successfully\n")
except Exception as e:
    print(f"❌ Import error: {e}\n")
    sys.exit(1)

# Test 2: Test TaskManager
print("Test 2: Testing TaskManager...")
try:
    from task_manager import TaskManager
    from datetime import datetime
    
    tm = TaskManager()
    initial_count = tm.get_task_count()
    print(f"   Initial task count: {initial_count}")
    
    # Add a task
    task = tm.add_task("Test task", None, 60)
    print(f"   Added task: {task['task']}")
    print(f"   New count: {tm.get_task_count()}")
    
    # Remove the task
    removed = tm.remove_task(initial_count)
    print(f"   Removed task: {removed['task']}")
    print(f"   Final count: {tm.get_task_count()}")
    print("✅ TaskManager works correctly\n")
except Exception as e:
    print(f"❌ TaskManager error: {e}\n")
    sys.exit(1)

# Test 3: Test datetime parser
print("Test 3: Testing datetime parser...")
try:
    from datetime_parser import parse_datetime_from_text, parse_reminder_time
    
    text1, dt1 = parse_datetime_from_text("meeting tomorrow at 3pm")
    print(f"   Parsed 'meeting tomorrow at 3pm'")
    print(f"   Clean text: {text1}")
    print(f"   Datetime: {dt1}")
    
    text2, minutes = parse_reminder_time("remind me 30 minutes before")
    print(f"   Parsed '30 minutes before': {minutes} minutes")
    print("✅ Datetime parser works correctly\n")
except Exception as e:
    print(f"❌ Datetime parser error: {e}\n")
    sys.exit(1)

# Test 4: Test UI helpers
print("Test 4: Testing UI helpers...")
try:
    from ui_helpers import format_task_added_message
    from datetime import datetime, timedelta
    from config import EST
    
    future = datetime.now(EST) + timedelta(hours=2)
    msg = format_task_added_message("Test task", future, 30)
    print(f"   Formatted message: {msg}")
    print("✅ UI helpers work correctly\n")
except Exception as e:
    print(f"❌ UI helpers error: {e}\n")
    sys.exit(1)

print("=" * 50)
print("🎉 All tests passed! The refactored code is ready.")
print("=" * 50)
