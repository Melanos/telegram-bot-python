"""Refactored Telegram bot with modular structure."""
import time
import signal
import sys
import telebot
from telebot import types
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from database import init_database
from database.db_helpers import ensure_user_profile, log_conversation

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
from api_handlers import get_stock_price, call_claude_api, track_interests, fetch_news, summarize_article
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

# ⬇️ ADD DATABASE INITIALIZATION HERE
try:
    db = init_database()
    print("✅ Database connected and tables created!")
except Exception as e:
    print(f"⚠️ Database initialization failed: {e}")
    print("Bot will continue without database features.")
    db = None

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

scheduler.add_job(
    lambda: send_morning_brief(ALLOWED_USER_ID, str(ALLOWED_USER_ID)),
    CronTrigger(hour=8, minute=30, timezone=EST),
    id="morning_brief"
)

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

def process_protein_input(message):
    """Process protein input after button press."""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    text = message.text.strip()
    
    # Check if user clicked a menu button instead - pass it to chat_ai
    if text in ["📋 List tasks", "✅ Complete task", "🥩 Log Protein", "💪 Log Workout", 
                "📊 My Stats", "📅 History", "🔔 My Alerts"]:
        chat_ai(message)  # Let the main handler process it
        return
    
    try:
        # Simulate /protein command
        message.text = f"/protein {message.text}"
        handle_log_protein(message)
    except:
        bot.reply_to(message, "❌ Please use format: <amount> <food>\nExample: 50 chicken breast")


def process_workout_input(message):
    """Process workout input after button press."""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    text = message.text.strip()
    
    # Check if user clicked a menu button instead - pass it to chat_ai
    if text in ["📋 List tasks", "✅ Complete task", "🥩 Log Protein", "💪 Log Workout", 
                "📊 My Stats", "📅 History", "🔔 My Alerts"]:
        chat_ai(message)  # Let the main handler process it
        return
    
    try:
        # Simulate /workout command
        message.text = f"/workout {message.text}"
        handle_log_workout(message)
    except:
        bot.reply_to(message, "❌ Please describe your workout\nExample: Push - chest day")

def send_morning_brief(chat_id: int, telegram_id: str):
    try:
        now_est = datetime.now(EST)
        day_name = now_est.strftime("%A")
        lines = [f"🌅 *Good morning! Here's your {day_name} brief*\n"]

        # NEWS
        tags = db.get_interests(telegram_id)
        if tags:
            articles = fetch_news(tags, page_size=3)
            if articles:
                lines.append("📰 *Top Stories*")
                for a in articles:
                    lines.append(f"• [{a.get('title','')}]({a.get('url','')})")
                lines.append("")

        # TASKS DUE TODAY
        tasks = task_manager.get_all_tasks()
        today_tasks = [t for t in tasks if t.get("due") and
                       t["due"].date() == now_est.date()]
        if today_tasks:
            lines.append("📋 *Due Today*")
            for t in today_tasks:
                lines.append(f"• {t['task']} — {t['due'].strftime('%I:%M %p')}")
            lines.append("")

        # WORKOUT SUGGESTION
        try:
            from database.db_manager import HealthTracking
            session = db.get_session()
            recent = session.query(HealthTracking)\
                .filter(HealthTracking.telegram_id == telegram_id)\
                .order_by(HealthTracking.date.desc()).limit(3).all()
            session.close()
            if recent and recent[0].workout_type:
                rotation = {"Push": "Pull", "Pull": "Legs", "Legs": "Push"}
                last_type = recent[0].workout_type
                lines.append("💪 *Workout Suggestion*")
                lines.append(f"• Last: {last_type}")
                lines.append(f"• Today: *{rotation.get(last_type, 'Push')}* day")
                lines.append("")
        except Exception:
            pass

        # PROTEIN
        user = db.get_user(telegram_id)
        target = user.protein_target if user else 180
        health = db.get_today_health(telegram_id)
        logged = health.protein_consumed if health else 0
        lines.append(f"🥩 *Protein target: {target}g* — {logged}g logged so far")

        bot.send_message(chat_id, "\n".join(lines),
                         parse_mode="Markdown",
                         disable_web_page_preview=True)
    except Exception as e:
        print(f"[Morning Brief] Error: {e}")

# ============================================================================
# BOT HANDLERS
# ============================================================================

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    """Handle /start and /hello commands."""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    ensure_user_profile(db, message)
    
    keyboard = create_main_menu_keyboard()
    response = (
        "👋 Hello! I'm your personal AI assistant!\n\n"
        "I can help you with:\n"
        "✅ Task reminders with natural language\n"
        "📈 Stock price tracking and alerts\n\n"
        "Just chat naturally, or type `/help` to see all commands!"
    )
    bot.reply_to(message, response, reply_markup=keyboard)
    

    log_conversation(db, message, response)
    
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
        
        # Claude provides reminder_minutes in the response
        reminder_minutes = item.get("reminder_minutes", 60)
        
        # If Claude didn't specify a custom reminder AND we have a due time,
        # use smart reminder calculation
        if reminder_minutes == 60 and due_time:
            reminder_minutes = calculate_smart_reminder(due_time)
            print(f"🧠 Smart reminder: {reminder_minutes} min before")
        
        task_manager.add_task(task_text, due_time, reminder_minutes)
        
        formatted_msg = format_task_added_message(
            task_text,
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

@bot.message_handler(commands=['dbstats'])
def handle_db_stats(message):
    """Show database statistics."""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    if db is None:
        bot.reply_to(message, "❌ Database not connected")
        return
    
    try:
        session = db.get_session()
        
        # Import models and timezone
        from database.db_manager import UserProfile, Conversation, HealthTracking, EST

        
        # Count records in each table
        user_count = session.query(UserProfile).count()
        conversation_count = session.query(Conversation).count()
        health_count = session.query(HealthTracking).count()
        
        # Get your user info
        telegram_id = str(message.from_user.id)
        user = db.get_user(telegram_id)
        
        response = "📊 **Database Statistics**\n\n"
        response += f"👤 Users: {user_count}\n"
        response += f"💬 Conversations: {conversation_count}\n"
        response += f"🏋️ Health logs: {health_count}\n\n"
        
        if user:
            response += "**Your Profile:**\n"
            response += f"Name: {user.name}\n"
            response += f"Protein target: {user.protein_target}g\n"
            response += f"Calorie target: {user.calorie_target}\n"
            
            # Convert UTC to EST for display ⬇️
            created_utc = user.created_at.replace(tzinfo=pytz.UTC)
            created_est = created_utc.astimezone(EST)
            response += f"Created: {created_est.strftime('%Y-%m-%d %I:%M %p %Z')}\n"
        
        # Get recent conversations
        conversations = db.get_recent_conversations(telegram_id, limit=3)
        if conversations:
            response += f"\n**Recent Conversations:** {len(conversations)}\n"
        
        session.close()
        bot.reply_to(message, response, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error querying database: {e}")
        import traceback
        print(traceback.format_exc())

@bot.message_handler(commands=['help'])
def send_help(message):
    """Handle /help command."""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    help_text = (
        "🤖 *Your Personal AI Assistant*\n\n"
        
        "💬 *Natural Language (Just Talk!)*\n"
        "• 'I had 60g protein from eggs'\n"
        "• 'Bench press 245 x6 felt easy'\n"
        "• 'Finished push day'\n"
        "• 'Remind me to call mom tomorrow at 6pm'\n"
        "• 'How am I doing today?'\n\n"
        
        "📋 *Task Management:*\n"
        "• `/addtask <description>` - Add a task\n"
        "• `/listtasks` - Show all tasks\n"
        "• `/donetask <number>` - Complete a task\n\n"
        
        "🏋️ *Health Tracking:*\n"
        "• `/protein <amount> [food]` - Log protein\n"
        "  Example: `/protein 50 chicken breast`\n"
        "• `/workout <type> - <notes>` - Log workout\n"
        "  Example: `/workout Push - chest day`\n"
        "• `/stats` - Show today's progress\n"
        "• `/history` - Show last 7 days\n"
        "• `/weekly` - Show 7-day summary & trends\n"
        "• `/setgoal protein 180` - Set protein goal\n"
        "• `/setgoal calories 2500` - Set calorie goal\n"
        "• `/resettoday` - Reset today's data\n\n"
        
        "📈 *Stock Tracking:*\n"
        "• `/stock SYMBOL` - Check price\n"
        "  Example: `/stock AAPL`\n"
        "• `/alert SYMBOL PRICE [above|below]` - Set alert\n"
        "  Example: `/alert ETH-USD 2000 below`\n"
        "• `/alerts` - View active alerts\n"
        "• `/removealert SYMBOL` - Remove alert\n\n"
        
        "🗄️ *Database:*\n"
        "• `/dbstats` - Show database statistics\n\n"
        
        "⚙️ *Other:*\n"
        "• `/menu` - Show menu keyboard\n"
        "• `/help` - Show this message\n\n"
        
        "💡 *Tip:* Skip the commands — just talk naturally and I'll figure it out! 🧠"
    )
    
    keyboard = create_main_menu_keyboard()
    bot.reply_to(message, help_text, parse_mode="Markdown", reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def send_help(message):
    """Handle /help command."""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    help_text = (
        "🤖 *Your Personal AI Assistant*\n\n"
        
        "💬 *Natural Language (Just Talk!)*\n"
        "• 'I had 60g protein from eggs'\n"
        "• 'Bench press 245 x6 felt easy'\n"
        "• 'Finished push day'\n"
        "• 'Remind me to call mom tomorrow at 6pm'\n"
        "• 'How am I doing today?'\n"
        "• 'I just started Atomic Habits'\n"
        "• 'I'm on page 87 of Atomic Habits'\n"
        "• 'I finished Deep Work'\n\n"
        
        "📋 *Task Management:*\n"
        "• `/addtask <description>` - Add a task\n"
        "• `/listtasks` - Show all tasks\n"
        "• `/donetask <number>` - Complete a task\n\n"
        
        "🏋️ *Health Tracking:*\n"
        "• `/protein <amount> [food]` - Log protein\n"
        "  Example: `/protein 50 chicken breast`\n"
        "• `/workout <type> - <notes>` - Log workout\n"
        "  Example: `/workout Push - chest day`\n"
        "• `/stats` - Show today's progress\n"
        "• `/history` - Show last 7 days\n"
        "• `/weekly` - Show 7-day summary & trends\n"
        "• `/setgoal protein 180` - Set protein goal\n"
        "• `/setgoal calories 2500` - Set calorie goal\n"
        "• `/resettoday` - Reset today's data\n\n"

        "📚 *Reading Tracker:*\n"
        "• `/reading` - View your reading list\n"
        "• `/reading <title>` - Start tracking a book\n"
        "  Example: `/reading Atomic Habits`\n"
        "• Natural language works too:\n"
        "  'I just started Deep Work'\n"
        "  'I'm on page 120 of Atomic Habits'\n"
        "  'I finished The Lean Startup'\n\n"
        
        "📈 *Stock Tracking:*\n"
        "• `/stock SYMBOL` - Check price\n"
        "  Example: `/stock AAPL`\n"
        "• `/alert SYMBOL PRICE [above|below]` - Set alert\n"
        "  Example: `/alert ETH-USD 2000 below`\n"
        "• `/alerts` - View active alerts\n"
        "• `/removealert SYMBOL` - Remove alert\n\n"
        
        "🗄️ *Database:*\n"
        "• `/dbstats` - Show database statistics\n\n"
        
        "⚙️ *Other:*\n"
        "• `/menu` - Show menu keyboard\n"
        "• `/help` - Show this message\n\n"
        
        "💡 *Tip:* Skip the commands — just talk naturally and I'll figure it out! 🧠"
    )
    
    keyboard = create_main_menu_keyboard()
    bot.reply_to(message, help_text, parse_mode="Markdown", reply_markup=keyboard)


@bot.message_handler(commands=['workout'])
def handle_log_workout(message):
    """Log workout. Usage: /workout Push - chest and triceps"""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    try:
        text = message.text[len("/workout"):].strip()
        if not text:
            bot.reply_to(message, "Usage: /workout <workout type> - <description>\nExample: /workout Push - chest and triceps")
            return
        
        # Parse workout type and notes
        if " - " in text:
            workout_type, notes = text.split(" - ", 1)
        else:
            workout_type = text
            notes = None
        
        telegram_id = str(message.from_user.id)
        session = db.get_session()
        
        from database.db_manager import HealthTracking
        from datetime import datetime
        
        # Get or create today's tracking
        today = datetime.utcnow().date()
        tracking = session.query(HealthTracking)\
            .filter(HealthTracking.telegram_id == telegram_id)\
            .filter(HealthTracking.date >= today)\
            .first()
        
        if tracking:
            tracking.workout_completed = True
            tracking.workout_type = workout_type.strip()
            if notes:
                tracking.notes = f"{tracking.notes or ''}\n{notes}".strip()
        else:
            tracking = HealthTracking(
                telegram_id=telegram_id,
                workout_completed=True,
                workout_type=workout_type.strip(),
                notes=notes
            )
            session.add(tracking)
        
        session.commit()
        session.close()
        
        response = f"✅ Workout logged!\n\n💪 {workout_type}"
        if notes:
            response += f"\n📝 {notes}"
        
        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())


@bot.message_handler(commands=['stats'])
def handle_stats(message):
    """Show today's progress."""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    try:
        telegram_id = str(message.from_user.id)
        user = db.get_user(telegram_id)
        health = db.get_today_health(telegram_id)
        
        response = "📊 **Today's Progress**\n\n"
        
        # Protein
        if health and health.protein_consumed > 0:
            target = user.protein_target if user else 180
            percentage = int((health.protein_consumed / target) * 100)
            response += f"🥩 Protein: {health.protein_consumed}g / {target}g ({percentage}%)\n"
            
            if health.protein_consumed >= target:
                response += "   ✅ Goal reached!\n"
            else:
                remaining = target - health.protein_consumed
                response += f"   📍 {remaining}g remaining\n"
        else:
            response += "🥩 Protein: Not logged yet\n"
        
        # Workout
        if health and health.workout_completed:
            response += f"\n💪 Workout: ✅ {health.workout_type or 'Completed'}\n"
            if health.exercises:
                for ex in health.exercises:
                    line = f"   • {ex.get('name', 'Exercise')}"
                    if ex.get('weight'):
                        line += f" – {ex['weight']}lbs x{ex.get('reps', '?')}"
                    if ex.get('notes'):
                        line += f" ({ex['notes']})"
                    response += line + "\n"
        else:
            response += "\n💪 Workout: Not completed yet\n"

        # ✅ NEW — Reading section
        books = db.get_reading_stats(telegram_id)
        if books:
            currently_reading = [b for b in books if b.status == "reading"]
            finished = [b for b in books if b.status == "finished"]

            response += f"\n📚 Reading: {len(currently_reading)} active · {len(finished)} finished\n"
            for book in currently_reading:
                progress = ""
                if book.current_page and book.total_pages:
                    pct = int(book.current_page / book.total_pages * 100)
                    progress = f" — pg {book.current_page}/{book.total_pages} ({pct}%)"
                elif book.current_page:
                    progress = f" — pg {book.current_page}"
                response += f"   📖 {book.book_title}{progress}\n"
        else:
            response += "\n📚 Reading: Nothing tracked yet\n"

        bot.reply_to(message, response, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")


@bot.message_handler(commands=['history'])
def handle_history(message):
    """Show last 7 days of tracking."""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    try:
        telegram_id = str(message.from_user.id)
        session = db.get_session()
        
        from database.db_manager import HealthTracking
        from datetime import datetime, timedelta
        
        # Get last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        history = session.query(HealthTracking)\
            .filter(HealthTracking.telegram_id == telegram_id)\
            .filter(HealthTracking.date >= seven_days_ago)\
            .order_by(HealthTracking.date.desc())\
            .all()
        
        session.close()
        
        if not history:
            bot.reply_to(message, "No tracking history yet. Start logging with /protein or /workout!")
            return
        
        response = "📅 **Last 7 Days**\n\n"
        
        for day in history:
            import pytz
            # Convert UTC stored date to EST for display
            utc_date = day.date.replace(tzinfo=pytz.UTC)
            est_date = utc_date.astimezone(EST)
            date_str = est_date.strftime('%a, %b %d')
            response += f"**{date_str}**\n"
            
            if day.protein_consumed > 0:
                response += f"  🥩 {day.protein_consumed}g protein\n"
            
            if day.workout_completed:
                response += f"  💪 {day.workout_type or 'Workout'}\n"
            
            response += "\n"
        
        bot.reply_to(message, response, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['resettoday'])
def handle_reset_today(message):
    """Reset today's health tracking data."""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    try:
        telegram_id = str(message.from_user.id)
        session = db.get_session()
        
        from database.db_manager import HealthTracking
        from datetime import datetime
        
        # Delete today's tracking
        today = datetime.utcnow().date()
        deleted = session.query(HealthTracking)\
            .filter(HealthTracking.telegram_id == telegram_id)\
            .filter(HealthTracking.date >= today)\
            .delete()
        
        session.commit()
        session.close()
        
        if deleted > 0:
            bot.reply_to(message, f"✅ Reset today's data!\n\n🗑️ Deleted {deleted} record(s)")
        else:
            bot.reply_to(message, "ℹ️ No data to reset for today")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())

@bot.message_handler(commands=['setgoal'])
def set_goal_command(message):
    """Set custom protein or calorie goals"""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    try:
        telegram_id = str(message.from_user.id)
        args = message.text.split()[1:]  # Get arguments after /setgoal
        
        if len(args) < 2:
            bot.reply_to(message, 
                "❌ Usage: /setgoal <type> <amount>\n\n"
                "Examples:\n"
                "• /setgoal protein 180\n"
                "• /setgoal calories 2500")
            return
        
        goal_type = args[0].lower()
        amount = int(args[1])
        
        if goal_type not in ['protein', 'calories']:
            bot.reply_to(message, "❌ Goal type must be 'protein' or 'calories'")
            return
        
        # Get user from database
        user = db.get_user(telegram_id)
        if not user:
            bot.reply_to(message, "❌ User profile not found. Try /start first.")
            return
        
        session = db.get_session()
        
        if goal_type == 'protein':
            user.protein_target = amount
            bot.reply_to(message, f"✅ Daily protein goal updated to {amount}g! 🥩")
        else:
            user.calorie_target = amount
            bot.reply_to(message, f"✅ Daily calorie goal updated to {amount} kcal! 🔥")
        
        session.commit()
        session.close()
        
    except ValueError:
        bot.reply_to(message, "❌ Amount must be a number!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

@bot.message_handler(commands=['weekly'])
def weekly_stats_command(message):
    """Show weekly health tracking summary"""
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    try:
        telegram_id = str(message.from_user.id)
        session = db.get_session()
        
        from database.db_manager import HealthTracking
        from datetime import datetime, timedelta
        from collections import Counter
        
        # Get last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        weekly_data = session.query(HealthTracking)\
            .filter(HealthTracking.telegram_id == telegram_id)\
            .filter(HealthTracking.date >= seven_days_ago.date())\
            .order_by(HealthTracking.date.desc())\
            .all()
        
        if not weekly_data:
            bot.reply_to(message, "📊 No data for the past 7 days. Start logging with /protein and /workout!")
            session.close()
            return
        
        # Calculate stats
        total_days = len(set(record.date for record in weekly_data))
        total_protein = sum(record.protein_consumed or 0 for record in weekly_data)
        avg_protein = total_protein / total_days if total_days > 0 else 0
        
        # Workout stats
        workout_records = [r for r in weekly_data if r.workout_completed]
        workout_days = len(workout_records)
        workout_types = [r.workout_type for r in workout_records if r.workout_type]
        
        # Find best day
        best_day_record = max(weekly_data, key=lambda x: x.protein_consumed or 0)
        best_protein = best_day_record.protein_consumed or 0
        best_utc = best_day_record.date.replace(tzinfo=pytz.UTC)
        best_date = best_utc.astimezone(EST).strftime('%b %d')
        
        # Get user goal
        user = db.get_user(telegram_id)
        protein_goal = user.protein_target if user else 180
        achievement_rate = (avg_protein / protein_goal * 100) if protein_goal > 0 else 0
        
        # Build response
        start_date = (datetime.utcnow() - timedelta(days=6)).strftime('%b %d')
        end_date = datetime.utcnow().strftime('%b %d')
        
        response = f"📊 **Weekly Summary** ({start_date} - {end_date})\n\n"
        response += f"🥩 **Protein Tracking:**\n"
        response += f"• Average: {avg_protein:.0f}g/day\n"
        response += f"• Best day: {best_protein}g ({best_date})\n"
        response += f"• Days logged: {total_days}/7\n"
        response += f"• Target achievement: {achievement_rate:.0f}%\n\n"
        
        response += f"💪 **Workouts:**\n"
        response += f"• Total sessions: {workout_days}\n"
        if workout_types:
            type_counts = Counter(workout_types)
            response += f"• Types: {', '.join([f'{t} ({c})' for t, c in type_counts.most_common()])}\n"
        response += f"• Consistency: {(workout_days/7*100):.0f}%\n\n"
        
        # Motivational message
        if achievement_rate >= 90:
            response += "🔥 Outstanding work! Keep crushing it!"
        elif achievement_rate >= 70:
            response += "💪 Great progress! You're on track!"
        else:
            response += "📈 Room to improve! You got this!"
        
        bot.reply_to(message, response, parse_mode='Markdown')
        session.close()
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error generating weekly stats: {str(e)}")
        import traceback
        print(traceback.format_exc())

@bot.message_handler(commands=['reading'])
def handle_reading(message):
    if message.from_user.id != ALLOWED_USER_ID:
        return
    
    telegram_id = str(message.from_user.id)
    
    # Only parse args for actual /reading command, not button press
    if message.text and message.text.startswith('/reading'):
        args = message.text.split()[1:]  # e.g. /reading Atomic Habits → ["Atomic", "Habits"]
    else:
        args = []  # Button press — show list

    if args:
        title = " ".join(args)
        db.log_book_start(telegram_id, title)
        bot.reply_to(message, 
            f"📚 Now tracking: *{title}*\nSay 'I'm on page X of {title}' to update progress!",
            parse_mode="Markdown")
        return

    # Show reading list
    books = db.get_reading_stats(telegram_id)
    if not books:
        bot.reply_to(message,
            "📚 No books tracked yet!\n\n"
            "Try:\n"
            "• /reading Atomic Habits\n"
            "• 'I just started Deep Work'\n"
            "• 'I'm on page 87 of Atomic Habits'"
        )
        return

    msg = "📚 *Your Reading List*\n\n"
    for book in books:
        emoji = "📖" if book.status == "reading" else "✅" if book.status == "finished" else "⏸"
        progress = ""
        if book.current_page and book.total_pages:
            pct = int(book.current_page / book.total_pages * 100)
            progress = f" — pg {book.current_page}/{book.total_pages} ({pct}%)"
        elif book.current_page:
            progress = f" — pg {book.current_page}"
        author = f" _{book.author}_" if book.author else ""
        msg += f"{emoji} *{book.book_title}*{author}{progress}\n"

    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['news'])
def handle_news(message):
    if message.from_user.id != ALLOWED_USER_ID:
        return

    telegram_id = str(message.from_user.id)
    tags = db.get_interests(telegram_id)

    if not tags:
        bot.reply_to(message,
            "🏷️ No interests set yet!\n\n"
            "Add some first: `/interests investing`\n"
            "Or just chat — I'll auto-detect them.",
            parse_mode="Markdown")
        return

    bot.reply_to(message, f"📰 Fetching news for: {', '.join(tags[:5])}...")

    try:
        articles = fetch_news(tags)
        if not articles:
            bot.reply_to(message, "😕 No articles found. Try broadening your interests.")
            return

        for article in articles[:5]:
            title = article.get("title", "")
            description = article.get("description") or article.get("content") or ""
            url = article.get("url", "")
            source = article.get("source", {}).get("name", "")

            summary = summarize_article(title, description)

            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("👍 More like this", callback_data=f"news_more:{title[:40]}"),
                types.InlineKeyboardButton("👎 Less like this", callback_data=f"news_less:{title[:40]}")
            )

            text = (
                f"📰 *{title}*\n"
                f"_{source}_\n\n"
                f"{summary}\n\n"
                f"[Read more]({url})"
            )
            bot.send_message(message.chat.id, text,
                parse_mode="Markdown",
                reply_markup=markup,
                disable_web_page_preview=True)

    except Exception as e:
        bot.reply_to(message, f"❌ Error fetching news: {e}")

@bot.message_handler(commands=['brief'])
def handle_brief(message):
    if message.from_user.id != ALLOWED_USER_ID:
        return
    send_morning_brief(message.chat.id, str(message.from_user.id))

@bot.callback_query_handler(func=lambda c: c.data.startswith("rm_int:"))
def cb_remove_interest_tag(call):
    """Remove a single interest tag when tapped."""
    if call.from_user.id != ALLOWED_USER_ID:
        bot.answer_callback_query(call.id, "Not authorized")
        return

    tag = call.data.split(":", 1)[1]
    telegram_id = str(call.from_user.id)
    db.remove_interest(telegram_id, tag)
    bot.answer_callback_query(call.id, f"🗑️ Removed: {tag}")

    # Refresh the interests menu in-place
    tags = db.get_interests(telegram_id)
    if not tags:
        bot.edit_message_text(
            "🏷️ *Your Interest Profile*\n\nNo tags left! Just chat and I'll auto-detect them.",
            call.message.chat.id,
            call.message.id,
            parse_mode="Markdown"
        )
    else:
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(*[types.InlineKeyboardButton(f"❌ {t}", callback_data=f"rm_int:{t}") for t in tags])
        markup.add(
            types.InlineKeyboardButton("🗑️ Clear All", callback_data="int_clear"),
            types.InlineKeyboardButton("✅ Done", callback_data="int_done")
        )
        tag_display = " · ".join(f"`{t}`" for t in tags)
        bot.edit_message_text(
            f"🏷️ *Your Interest Profile* — {len(tags)} tags\n{tag_display}\n\nTap a tag to remove it",
            call.message.chat.id,
            call.message.id,
            parse_mode="Markdown",
            reply_markup=markup
        )


@bot.callback_query_handler(func=lambda c: c.data == "int_clear")
def cb_clear_all_interests(call):
    """Clear all interest tags."""
    if call.from_user.id != ALLOWED_USER_ID:
        bot.answer_callback_query(call.id, "Not authorized")
        return

    telegram_id = str(call.from_user.id)
    tags = db.get_interests(telegram_id)
    for tag in tags:
        db.remove_interest(telegram_id, tag)

    bot.answer_callback_query(call.id, "🗑️ All interests cleared!")
    bot.edit_message_text(
        "🏷️ *Your Interest Profile*\n\nAll tags cleared! Just chat and I'll auto-detect your interests.",
        call.message.chat.id,
        call.message.id,
        parse_mode="Markdown"
    )


@bot.callback_query_handler(func=lambda c: c.data == "int_done")
def cb_interests_done(call):
    """Dismiss the interests menu."""
    bot.answer_callback_query(call.id, "✅ Saved!")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)

@bot.callback_query_handler(func=lambda c: c.data.startswith("news_more:") or c.data.startswith("news_less:"))
def cb_news_feedback(call):
    action, topic = call.data.split(":", 1)
    telegram_id = str(call.from_user.id)

    if action == "news_more":
        db.add_interest(telegram_id, topic[:30])
        bot.answer_callback_query(call.id, "👍 Got it — more like this!")
    else:
        db.remove_interest(telegram_id, topic[:30])
        bot.answer_callback_query(call.id, "👎 Got it — less like this!")

def handle_ai_workout_log(message, item):
    """Handle AI-detected workout log from natural language."""
    try:
        telegram_id = str(message.from_user.id)
        workout_type = item.get("workout_type", "General")
        notes = item.get("notes", "")
        exercises = item.get("exercises", [])
        reply = item.get("reply", "Workout logged! 💪")

        session = db.get_session()
        from database.db_manager import HealthTracking
        from datetime import datetime

        today = datetime.utcnow().date()
        tracking = session.query(HealthTracking)\
            .filter(HealthTracking.telegram_id == telegram_id)\
            .filter(HealthTracking.date >= today)\
            .first()

        if tracking:
            tracking.workout_completed = True
            tracking.workout_type = workout_type
            if notes:
                tracking.notes = f"{tracking.notes or ''}\n{notes}".strip()
            if exercises:
                existing = tracking.exercises or []
                existing.extend(exercises)
                tracking.exercises = existing
        else:
            tracking = HealthTracking(
                telegram_id=telegram_id,
                workout_completed=True,
                workout_type=workout_type,
                notes=notes,
                exercises=exercises if exercises else []
            )
            session.add(tracking)

        session.commit()

        # Build detailed response
        response = reply
        if exercises:
            response += "\n\n📋 **Logged exercises:**"
            for ex in exercises:
                line = f"\n• {ex.get('name', 'Exercise')}"
                if ex.get('weight'):
                    line += f" – {ex['weight']}lbs x{ex.get('reps', '?')}"
                if ex.get('notes'):
                    line += f" _(_{ex['notes']}_)_"
                response += line

            # Progression check
            easy_notes = [e for e in exercises if e.get('notes') and 
                         any(word in e['notes'].lower() for word in ['easy', 'light', 'could do more', 'too light'])]
            if easy_notes:
                response += "\n\n💡 **Progression tip:** One or more exercises felt easy. Consider increasing weight next session (+5 lbs upper / +10 lbs lower)."

        session.close()
        bot.reply_to(message, response, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Error logging workout: {e}")
        import traceback
        print(traceback.format_exc())

def handle_ai_protein_log(message, item):
    """Handle AI-detected protein log from natural language."""
    try:
        telegram_id = str(message.from_user.id)
        amount = float(item.get("amount", 0))
        food = item.get("food", "")
        reply = item.get("reply", "")

        if amount <= 0:
            bot.reply_to(message, "❌ Couldn't detect protein amount. Try: 'I had 60g protein from eggs'")
            return

        result = db.log_protein(telegram_id, amount, food)
        total_protein = result['protein_consumed']

        user = db.get_user(telegram_id)
        target = user.protein_target if user else 180
        percentage = int((total_protein / target) * 100)

        response = f"✅ Logged {amount}g protein"
        if food:
            response += f" from {food}"
        response += f"\n\n📊 Today: {total_protein}g / {target}g ({percentage}%)"

        if total_protein >= target:
            response += "\n🎉 Daily goal reached!"
        else:
            remaining = target - total_protein
            response += f"\n📍 {remaining}g remaining"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Error logging protein: {e}")
        import traceback
        print(traceback.format_exc())

def send_interests_menu(chat_id: int, telegram_id: str):
    """Build and send the interest profile menu."""
    tags = db.get_interests(telegram_id)

    if not tags:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "💡 Just chat — I'll detect your interests!",
            callback_data="interest_noop"
        ))
        bot.send_message(
            chat_id,
            "🏷️ *Your Interest Profile*\n\n"
            "No tags yet! Just chat naturally and I'll auto-detect your interests.\n\n"
            "Or add one manually: `/interests investing`",
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(*[
        types.InlineKeyboardButton(f"❌ {tag}", callback_data=f"rm_int:{tag}")
        for tag in tags
    ])
    markup.add(
        types.InlineKeyboardButton("🗑 Clear All", callback_data="int_clear"),
        types.InlineKeyboardButton("✅ Done", callback_data="int_done")
    )
    tag_display = " • ".join(f"`{t}`" for t in tags)
    bot.send_message(
        chat_id,
        f"🏷️ *Your Interest Profile* — {len(tags)} tags\n\n{tag_display}\n\n_Tap a tag to remove it_",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: True)
def chat_ai(message):
    """Handle all other messages with AI."""
    if message.from_user.id != ALLOWED_USER_ID:
        return

    ensure_user_profile(db, message)

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
    
    # ⬇️ ADD THESE NEW HANDLERS
    if text == "🥩 Log Protein":
        msg = bot.reply_to(message, "How much protein? (e.g., 50 chicken breast)")
        bot.register_next_step_handler(msg, process_protein_input)
        return
    
    
    if text == "💪 Log Workout":
        msg = bot.reply_to(message, "What workout? (e.g., Push - chest day)")
        bot.register_next_step_handler(msg, process_workout_input)
        return
    
    if text == "📊 My Stats":
        handle_stats(message)
        return
    
    if text == "📅 History":
        handle_history(message)
        return
    
    if text == "📚 Reading List":
        handle_reading(message)
        return

    if text == "🏷️ My Interests":
        send_interests_menu(message.chat.id, str(message.from_user.id))
        return

    if text == "📰 News Digest":
        handle_news(message)
        return
    

    # Natural language stats triggers
    if any(phrase in text.lower() for phrase in [
        "how am i doing", "my stats", "my progress", 
        "how's my protein", "did i hit my goal"
    ]):
        handle_stats(message)
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
                # Get datetime from Claude (already parsed!)
                due_str = item.get("due")
                due_time = validate_claude_datetime(due_str)
                
                # Get custom reminder time from Claude
                reminder_minutes = item.get("reminder_minutes", 60)
                
                # If default reminder and we have a due time, calculate smart reminder
                if reminder_minutes == 60 and due_time:
                    reminder_minutes = calculate_smart_reminder(due_time)
                
                task_manager.add_task(task_text, due_time, reminder_minutes)
                
                formatted_msg = format_task_added_message(
                    task_text,
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
        
        elif reply_type == "log_protein":
            handle_ai_protein_log(message, item)
        
        elif reply_type == "log_book_start":
            title = (item.get("title") or "").strip()
            author = item.get("author")
            total_pages = item.get("total_pages")
            if title:
                db.log_book_start(str(message.from_user.id), title, author, total_pages)
                reply_messages.append(reply_text or f"📚 Now tracking *{title}*!")
            else:
                reply_messages.append("📚 What book are you reading?")

        elif reply_type == "log_book_progress":
            title = (item.get("title") or "").strip()
            page = item.get("page")
            if title and page:
                db.log_book_progress(str(message.from_user.id), title, int(page))
                reply_messages.append(reply_text or f"📖 Page {page} saved for *{title}*!")
            else:
                reply_messages.append("📖 Which book and what page?")

        elif reply_type == "log_book_finished":
            title = (item.get("title") or "").strip()
            if title:
                db.log_book_finished(str(message.from_user.id), title)
                reply_messages.append(reply_text or f"✅ Finished *{title}*! What did you think?")
            else:
                reply_messages.append("Which book did you finish?")

        elif reply_type == "remove_book":
            title = (item.get("title") or "").strip()
            if title:
                db.remove_book(str(message.from_user.id), title)
                reply_messages.append(reply_text or f"🗑️ Removed *{title}* from your reading list!")
            else:
                reply_messages.append("Which book do you want to remove?")
        
        elif reply_type == "view_interests":
            send_interests_menu(message.chat.id, str(message.from_user.id))
            return

        elif reply_type == "add_interest":
            tag = (item.get("tag") or "").lower().strip()
            if tag:
                added = db.add_interest(str(message.from_user.id), tag)
                text_reply = f"✅ Added *{tag}* to your interests! 🏷️" if added else f"ℹ️ *{tag}* already in your interests."
                reply_messages.append(text_reply)

        elif reply_type == "remove_interest":
            tag = (item.get("tag") or "").lower().strip()
            if tag:
                removed = db.remove_interest(str(message.from_user.id), tag)
                text_reply = f"🗑 Removed *{tag}* from your interests." if removed else f"ℹ️ *{tag}* wasn't in your interests."
                reply_messages.append(text_reply)

        elif reply_type == "log_workout":
            handle_ai_workout_log(message, item)
            

        elif reply_type == "health_query":
            # Route to existing /stats handler
            handle_stats(message)
            return
        
        else:  # "chat"
            reply_messages.append(reply_text or "Got it 👍")
    
    # Send combined reply
    if reply_messages:
        final_reply = "\n\n".join(reply_messages)
        bot.reply_to(message, final_reply)
        log_conversation(db, message, final_reply)

    # Background interest extraction — never blocks response
    track_interests(str(message.from_user.id), text_raw)

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
