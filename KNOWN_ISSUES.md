# Known Issues

This document tracks current bugs and issues in the project.

## 🔴 High Priority

### Claude Strips Time Information from Tasks
**Status**: Fix Ready - Needs Deployment  
**Issue**: When users send "remind me in 5 minutes to X", Claude returns only `task="X"` without preserving the time component.

**Impact**: Tasks are created without timestamps, making reminders non-functional.

**Root Cause**: System prompt doesn't explicitly instruct Claude to preserve all temporal information.

**Solution**: Update system prompt to include:
```
CRITICAL: You MUST preserve ALL time and date information from the user's input.
Examples:
- "remind me in 5 minutes to X" → task="X", due_time="in 5 minutes"
- "tomorrow at 3pm buy milk" → task="buy milk", due_time="tomorrow at 3pm"
```

**Next Steps**: Deploy updated prompt and test with various time formats.

---

### Reminders Not Firing
**Status**: Fix Ready - Needs Testing  
**Issue**: Background scheduler is not sending reminder notifications at the scheduled times.

**Impact**: Users receive no alerts before task due times, defeating the core purpose of the reminder system.

**Possible Causes**:
1. Timezone mismatch in `check_reminders()` function
2. Scheduler thread not running properly
3. Missing debug logs make diagnosis difficult

**Solution**:
- Add timezone-awareness to all datetime comparisons
- Implement comprehensive debug logging:
  ```python
  logger.debug(f"Checking reminders at {datetime.now(EST)}")
  logger.debug(f"Task due: {task['due']}, Remind: {task['remind_time']}")
  ```
- Verify scheduler initialization on Railway deployment

**Next Steps**: Deploy fixes and monitor logs during live testing.

---

## 🟡 Medium Priority

### Tasks Without Timestamps Display Incorrectly
**Status**: Partial Fix Deployed  
**Issue**: Legacy or broken tasks show as "✅ task name" without date information.

**Impact**: Confusing user experience; unclear when tasks are due.

**Solution**: Filter out tasks with `due=None` during load:
```python
tasks = [t for t in load_tasks(user_id) if t.get('due') is not None]
```

**Next Steps**: Monitor for recurrence; add validation on task creation.

---

### AI Misinterprets Similar Commands
**Status**: Needs Prompt Engineering  
**Issue**: Ambiguous commands like "say good night" (create task) vs "I said good night" (complete task) trigger wrong actions.

**Impact**: Users must rephrase commands or manually correct mistakes.

**Examples**:
- "say good night" → Should create task, sometimes marks complete
- "remind me to say hi" → Should create task, not greet

**Solution**: Improve system prompt with explicit examples:
```
TASK CREATION examples: "remind me to...", "add task...", "don't forget to..."
TASK COMPLETION examples: "I completed...", "done with...", "finished..."
```

**Next Steps**: A/B test improved prompts with real user commands.

---

### Relative Time Parsing Edge Cases
**Status**: Needs Testing  
**Issue**: Some time formats like "in X mins" may not match regex patterns.

**Impact**: Falls through to `dateutil.parser` which may fail or misinterpret.

**Solution**: Expand regex patterns in time parser:
```python
r'in (\d+) mins?' → r'in (\d+) (min|mins|minute|minutes)'
```

**Next Steps**: Collect failing examples from logs and update patterns.

---

## 🟢 Low Priority

### Desktop Menu Keyboard Not Syncing
**Status**: Documented Workaround  
**Issue**: Menu buttons don't appear in Telegram desktop app on first load.

**Impact**: Minor UX inconvenience; users must manually trigger `/menu` command.

**Workaround**: Send `/menu` command to display buttons.

**Root Cause**: Telegram API limitation with persistent keyboards on desktop clients.

**Solution**: No fix available due to API constraints. Workaround documented in user instructions.

---

## Reporting New Issues

Please report issues using the GitHub issue tracker with:
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Screenshots** (if applicable)
- **Environment** (Desktop/Mobile, Telegram version)

Use labels: `bug`, `high-priority`, `medium-priority`, `low-priority`
