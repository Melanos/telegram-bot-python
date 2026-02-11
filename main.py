"""Refactored Telegram bot with modular structure."""
import time
import signal
import sys
import telebot
from apscheduler.schedulers.background import BackgroundScheduler

# Import custom modules
from config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_ID, EST
from task_manager import TaskManager
from datetime_parser import calculate_smart_reminder, validate_claude_datetime
from ui_helpers import (
    create_main_menu_keyboard,
    create_task_completion_keyboard,
    format_task_added_message,
    format_reminder_message
)
from api_handlers import get_stock_price, call_claude_api
from reminder_system import check_reminders
from commands import register_commands
from stock_alerts import AlertManager, start_alert_monitoring


# Initialize bot
try:
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    register_commands(bot)
    
    print("🚀 Bot starting...")
    me = bot.get_me()
    print(f"✅ Connected as @{me.username}")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize bot. Error: {e}")
    print("The application will hang to prevent a restart loop.")
    while True:
        time.sleep(3600)
        
# Initialize task manager
task_manager = TaskManager()

# Initialize alert manager
alert_manager = AlertManager()
start_alert_monitoring(alert_manager, bot, check_interval=300)

# Reminder scheduler
scheduler = BackgroundScheduler()


def send_reminder(task_index: int, task_obj: dict):
    """Send a reminder for a task."""
    task_text = task_obj["task"]
    due_time = task_obj["due"]
    
    reminder_msg = format_reminder_message(task_text, due_time)
    
    try:
        bot.send_message(ALLOWED_USER_ID, reminder_msg)
        task_manager.mark_reminded(task_index)
    except Exception as e:
        print(f"Failed to send reminder: {e}")


def reminder_job():
    """Job for the scheduler to check reminders."""
    print(f"🔍 [{datetime.now(EST).strftime('%H:%M:%S')}] Checking reminders...")
    check_reminders(task_manager, send_reminder)


# Start the reminder scheduler
scheduler.add_job(reminder_job, 'interval', minutes=1)
scheduler.start()


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    print('🛑 Shutting down bot gracefully...')
    try:
        bot.stop_polling()
        scheduler.shutdown()
    except:
        pass
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ============================================================================
# BOT HANDLERS
# ============================================================================

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    """Handle /start and /hello commands."""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    keyboard = create_main_menu_keyboard()
    bot.reply_to(
        message,
        "Hello! I'm your personal Telegram bot 🤖\n\n"
        "I can handle reminders with custom times!\n\n"
        "Examples:\n"
        "• 'Remind me to go to gym tomorrow at 6pm'\n"
        "• 'Remind me 30 minutes before gym tomorrow at 6pm'\n"
        "• 'Remind me 2 hours before the meeting Friday 3pm'",
        reply_markup=keyboard
    )


@bot.message_handler(commands=['stock'])
def handle_stock(message):
    """Handle /stock command."""
    if message.from_user.id != ALLOWED_USER_ID:
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /stock SYMBOL, e.g. /stock AAPL")
        return

    symbol = parts[1]
    reply = get_stock_price(symbol)
    bot.reply_to(message, reply)


@bot.message_handler(commands=['addtask'])
def handle_add_task(message):
    """Handle /addtask command."""
    if message.from_user.id != ALLOWED_USER_ID:
        return

    text = message.text[len("/addtask"):].strip()
    if not text:
        bot.reply_to(message, "Usage: /addtask <task description>")
        return

    # Let Claude parse it
    result = call_claude_api(text)
    
    if isinstance(result, dict) and "error" in result:
        bot.reply_to(message, "Error processing task")
        return
    
    # Process first result
    if result and len(result) > 0:
        item = result[0]
        task_text = (item.get("task") or text).strip()
        due_str = item.get("due")
        due_time = validate_claude_datetime(due_str)
        reminder_minutes = item.get("reminder_minutes", 60)
        
        if reminder_minutes == 60 and due_time:
            reminder_minutes = calculate_smart_reminder(due_time)
        
        task_manager.add_task(task_text, due_time, reminder_minutes)
        
        formatted_msg = format_task_added_message(
            task_text,
            due_time,
            reminder_minutes
        )
        
        task_count = task_manager.get_task_count()
        bot.reply_to(message, f"Added task #{task_count}: {formatted_msg}")

    """Handle /addtask command."""
    if message.from_user.id != ALLOWED_USER_ID:
        return

    text = message.text[len("/addtask"):].strip()
    if not text:
        bot.reply_to(message, "Usage: /addtask <task description>")
        return

    # Parse reminder time first
    text, user_reminder = parse_reminder_time(text)

    # Then parse datetime
    cleaned_text, due_time = parse_datetime_from_text(text)

    # Smart reminder: use user's choice OR auto-calculate
    if user_reminder == 60 and due_time:
        reminder_minutes = calculate_smart_reminder(due_time)
        print(f"🧠 Smart reminder: {reminder_minutes} min before")
    else:
        reminder_minutes = user_reminder

    task_manager.add_task(cleaned_text or text, due_time, reminder_minutes)
    
    formatted_msg = format_task_added_message(
        cleaned_text or text,
        due_time,
        reminder_minutes
    )
    
    task_count = task_manager.get_task_count()
    bot.reply_to(message, f"Added task #{task_count}: {formatted_msg}")


@bot.message_handler(commands=['listtasks', 'tasks'])
def handle_list_tasks(message):
    """Handle /listtasks and /tasks commands."""
    if message.from_user.id != ALLOWED_USER_ID:
        return

    tasks = task_manager.get_all_tasks()
    if not tasks:
        bot.reply_to(message, "Your task list is empty ✅")
        return

    markup = create_task_completion_keyboard(tasks)
    bot.reply_to(message, "Tap a task to mark it complete:", reply_markup=markup)


@bot.message_handler(commands=['donetask'])
def handle_done_task(message):
    """Handle /donetask command."""
    if message.from_user.id != ALLOWED_USER_ID:
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /donetask <task_number>, e.g. /donetask 1")
        return

    try:
        idx = int(parts[1]) - 1
    except ValueError:
        bot.reply_to(message, "Task number must be a valid integer.")
        return

    done = task_manager.remove_task(idx)
    if done:
        bot.reply_to(message, f"Marked as done: {done['task']} ✅")
    else:
        bot.reply_to(message, "That task number does not exist.")


@bot.message_handler(commands=['menu'])
def cmd_menu(message):
    """Handle /menu command."""
    if message.from_user.id != ALLOWED_USER_ID:
        return

    keyboard = create_main_menu_keyboard()
    bot.reply_to(message, "Here's your menu:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('done_'))
def handle_task_completion(call):
    """Handle when user taps a task button to complete it."""
    if call.from_user.id != ALLOWED_USER_ID:
        bot.answer_callback_query(call.id, "Not authorized")
        return
    
    try:
        # Extract task index from callback data
        idx = int(call.data.split('_')[1])
        
        # Remove the task
        done_task = task_manager.remove_task(idx)
        if not done_task:
            bot.answer_callback_query(call.id, "Task no longer exists")
            return
        
        task_text = done_task['task']
        
        # Show confirmation popup
        bot.answer_callback_query(call.id, f"✅ Completed: {task_text}")
        
        # Update the message
        bot.edit_message_text(
            f"✅ Task completed: {task_text}",
            call.message.chat.id,
            call.message.id
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, "Error completing task")
        print(f"Error in callback: {e}")

@bot.message_handler(commands=['alert'])
def handle_add_alert(message):
    """
    Usage: /alert SYMBOL PRICE [above|below]
    Example: /alert IONQ 25 above
    """
    try:
        parts = message.text.split()
        
        if len(parts) < 3:
            bot.reply_to(
                message,
                "❌ Usage: /alert SYMBOL PRICE [above|below]\n"
                "Example: /alert IONQ 25 above"
            )
            return
        
        symbol = parts[1].upper()
        target_price = float(parts[2])
        condition = parts[3].lower() if len(parts) > 3 else "above"
        
        if condition not in ["above", "below"]:
            condition = "above"
        
        result = alert_manager.add_alert(
            user_id=message.from_user.id,
            symbol=symbol,
            target_price=target_price,
            condition=condition
        )
        
        bot.reply_to(message, result["message"])
        
    except ValueError:
        bot.reply_to(message, "❌ Invalid price. Use: /alert SYMBOL PRICE")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")


@bot.message_handler(commands=['alerts'])
def handle_list_alerts(message):
    """List all active alerts for the user."""
    user_alerts = alert_manager.get_user_alerts(message.from_user.id)
    
    if not user_alerts:
        bot.reply_to(message, "You have no active alerts.\n\nUse /alert SYMBOL PRICE to create one!")
        return
    
    response = "🔔 Your Active Alerts:\n\n"
    for i, alert in enumerate(user_alerts, 1):
        response += (
            f"{i}. {alert['symbol']} {alert['condition']} "
            f"${alert['target_price']:.2f}\n"
        )
    
    response += f"\n📊 Total: {len(user_alerts)} alert(s)"
    bot.reply_to(message, response)


@bot.message_handler(commands=['removealert'])
def handle_remove_alert(message):
    """
    Remove an alert.
    Usage: /removealert SYMBOL
    """
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Usage: /removealert SYMBOL\nExample: /removealert IONQ")
            return
        
        symbol = parts[1].upper()
        result = alert_manager.remove_alert(message.from_user.id, symbol)
        bot.reply_to(message, result["message"])
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")


@bot.message_handler(func=lambda msg: True)
def chat_ai(message):
    """Handle all other messages with AI."""
    if message.from_user.id != ALLOWED_USER_ID:
        return

    text_raw = message.text or ""
    text = text_raw.strip()

    # Handle menu button shortcuts
    if text == "✅ Complete task":
        tasks = task_manager.get_all_tasks()
        if not tasks:
            bot.reply_to(message, "You don't have any tasks to complete right now ✅")
        else:
            markup = create_task_completion_keyboard(tasks)
            bot.reply_to(message, "Tap to complete:", reply_markup=markup)
        return
    
    if text == "📋 List tasks":
        tasks = task_manager.get_all_tasks()
        if not tasks:
            bot.reply_to(message, "You don't have any tasks right now! 🎉")
        else:
            markup = create_task_completion_keyboard(tasks)
            bot.reply_to(message, "Tap a task to mark it complete:", reply_markup=markup)
            return
    if text == "🔔 My Alerts":
        handle_list_alerts(message)
        return

    # Call Claude API
    result = call_claude_api(text_raw)
    
    # Handle API errors
    if isinstance(result, dict) and "error" in result:
        if result["error"] == "http":
            error_msg = f"🔴 API Error ({result['status_code']}):\n{result['message']}"
        elif result["error"] == "parse":
            error_msg = f"🔴 JSON parse error:\n{result['type']}: {result['message']}\n\nRAW:\n{result.get('raw', '')}"
        else:
            error_msg = f"🔴 Claude API error:\n{result['type']}: {result['message']}"
        bot.reply_to(message, error_msg)
        return
    
    # Process actions
    reply_messages = []
    
    for item in result:
        reply_type = item.get("type")
        reply_text = (item.get("reply") or "").strip()
        
        if reply_type == "add_task":
            task_text = (item.get("task") or "").strip()
            if task_text:
                # Parse reminder time first
                task_text, user_reminder = parse_reminder_time(task_text)
                
                # Parse date/time from the task
                cleaned_text, due_time = parse_datetime_from_text(task_text)
                
                # Smart reminder: use user's choice OR auto-calculate
                if user_reminder == 60 and due_time:
                    reminder_minutes = calculate_smart_reminder(due_time)
                else:
                    reminder_minutes = user_reminder
                
                task_manager.add_task(cleaned_text or task_text, due_time, reminder_minutes)
                
                formatted_msg = format_task_added_message(
                    cleaned_text or task_text,
                    due_time,
                    reminder_minutes
                )
                reply_messages.append(formatted_msg)
            else:
                reply_messages.append(reply_text or "Got it 👍")
        
        elif reply_type == "list_tasks":
            tasks = task_manager.get_all_tasks()
            if not tasks:
                bot.reply_to(message, "You don't have any tasks right now! 🎉")
            else:
                markup = create_task_completion_keyboard(tasks)
                bot.reply_to(message, "Tap a task to mark it complete:", reply_markup=markup)
            return  # Return here to skip final reply
        
        elif reply_type == "remove_task":
            task_text = (item.get("task") or "").strip().lower()
            if not task_text or task_manager.get_task_count() == 0:
                reply_messages.append(reply_text or "I couldn't find a matching task to remove 🤔")
            else:
                task_idx = task_manager.find_task_by_text(task_text)
                if task_idx is not None:
                    removed = task_manager.remove_task(task_idx)
                    reply_messages.append(reply_text or f"✅ Marked as done: {removed['task']}")
                else:
                    reply_messages.append(reply_text or "I couldn't find a matching task to remove 🤔")
        
        else:  # "chat"
            reply_messages.append(reply_text or "Got it 👍")
    
    # Send combined reply
    if reply_messages:
        final_reply = "\n\n".join(reply_messages)
        bot.reply_to(message, final_reply)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        bot.remove_webhook()
        time.sleep(1)
    except:
        pass
    
    bot.delete_webhook(drop_pending_updates=True)
    print("🤖 Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
