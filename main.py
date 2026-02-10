import os
import time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import telebot
import requests
from dotenv import load_dotenv
from commands import register_commands
import yfinance as yf
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from apscheduler.schedulers.background import BackgroundScheduler
import re
import json
import signal
import sys
from pathlib import Path
# Test persistence - Feb 9
# Load environment variables
load_dotenv()

# Loading tasks, if the Railway environment crashes
TASKS_FILE = "/app/data/tasks.json"

def load_tasks():
    """Load tasks from disk"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)  # ← Add this line
        
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f:
                data = json.load(f)
                # Convert due dates back to datetime objects
                for task in data:
                    if task.get('due'):
                        task['due'] = datetime.fromisoformat(task['due'])
                print(f"✅ Loaded {len(data)} tasks from {TASKS_FILE}")  # ← Add debug
                return data
        else:
            print(f"ℹ️ No tasks file found at {TASKS_FILE}")  # ← Add debug
    except Exception as e:
        print(f"❌ Error loading tasks: {e}")  # ← Add debug
    return []


def save_tasks():
    """Save tasks to disk"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)  # ← Add this line
        
        # Convert datetime objects to ISO strings for JSON
        data = []
        for task in TASKS:
            task_copy = task.copy()
            if task_copy.get('due'):
                task_copy['due'] = task_copy['due'].isoformat()
            data.append(task_copy)
        
        with open(TASKS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved {len(data)} tasks to {TASKS_FILE}")  # ← Add debug log
    except Exception as e:
        print(f"❌ Error saving tasks: {e}")  # ← Add debug log


TASKS = load_tasks()

def signal_handler(sig, frame):
    print('🛑 Shutting down bot gracefully...')
    try:
        bot.stop_polling()
        scheduler.shutdown()
    except:
        pass
    sys.exit(0)
# Load tasks on startup
TASKS = load_tasks()

# Tokens from env
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Limit User Access
ALLOWED_USER_ID = 5244589395

# Background scheduler for reminders
scheduler = BackgroundScheduler()


def parse_reminder_time(text: str):
    """
    Extract custom reminder time from text.
    Returns (cleaned_text, reminder_minutes)
    Examples:
    - "remind me 30 minutes before" → 30
    - "remind me 2 hours before" → 120
    - "remind me 1 day before" → 1440
    Default: 60 minutes (1 hour)
    """
    text_lower = text.lower()
    
    # Pattern: "X minutes/hours/days before"
    patterns = [
        (r'(\d+)\s*minutes?\s*before', 1),
        (r'(\d+)\s*hours?\s*before', 60),
        (r'(\d+)\s*days?\s*before', 1440),
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, text_lower)
        if match:
            value = int(match.group(1))
            reminder_minutes = value * multiplier
            # Remove the reminder instruction from text
            cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
            return cleaned, reminder_minutes
    
    # Default: 60 minutes
    return text, 60


def parse_datetime_from_text(text: str):
    """
    Extract datetime from natural language using dateutil.
    Returns (cleaned_text, datetime_object or None)
    """
    if not text:
        return text, None
    
    now = datetime.now()
    text_lower = text.lower().strip()
    
    print(f"🔍 parse_datetime INPUT: '{text}'")  # ← Add this
    print(f"🔍 Current time: {now}")  # ← Add this
    
    # ========== Handle relative time FIRST ==========
    relative_pattern = r'\bin\s+(\d+)\s+(minute|minutes|hour|hours|min|mins|hr|hrs)\b'
    match = re.search(relative_pattern, text_lower)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit in ['minute', 'minutes', 'min', 'mins']:
            due_time = now + timedelta(minutes=amount)
        else:  # hour/hours/hr/hrs
            due_time = now + timedelta(hours=amount)
        
        cleaned = re.sub(relative_pattern, '', text, flags=re.IGNORECASE).strip()
        print(f"✅ RELATIVE match: amount={amount}, unit={unit}, due_time={due_time}")  # ← Add this
        return cleaned, due_time
    
    # If no relative match, try dateutil
    print(f"⚠️ No relative match, trying dateutil parser...")  # ← Add this
    
    try:
        dt = date_parser.parse(text, fuzzy=True)
        print(f"📅 dateutil parsed: {dt}")  # ← Add this
        
        if dt < datetime.now():
            if dt.date() == datetime.now().date():
                dt = dt + timedelta(days=1)
                print(f"⏭️ Adjusted to tomorrow: {dt}")  # ← Add this
        
        cleaned = re.sub(r'\b(at|on|tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', '', text, flags=re.IGNORECASE)
        cleaned = re.sub(r'\d{1,2}:\d{2}\s*(am|pm)?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\d{1,2}\s*(am|pm)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned, dt
    except:
        print(f"❌ dateutil failed to parse")  # ← Add this
        return text, None

def check_reminders():
    """
    Background task that runs every minute to check for upcoming tasks.
    Sends reminder at the custom time specified by user.
    """
    now = datetime.now()
    
    for task_obj in TASKS:
        due_time = task_obj.get("due")
        if not due_time or task_obj.get("reminded"):
            continue
        
        reminder_minutes = task_obj.get("reminder_minutes", 60)
        
        # Calculate when to send reminder
        reminder_time = due_time - timedelta(minutes=reminder_minutes)
        
        # Check if we're within 1 minute of reminder time (for reliability)
        time_diff = abs((now - reminder_time).total_seconds())
        
        if time_diff <= 60:  # Within 1 minute window
            task_text = task_obj["task"]
            formatted_time = due_time.strftime("%I:%M %p")
            
            # Calculate human-readable time until due
            minutes_until = int((due_time - now).total_seconds() / 60)
            if minutes_until >= 60:
                hours = minutes_until // 60
                time_str = f"in ~{hours} hour{'s' if hours > 1 else ''}"
            else:
                time_str = f"in ~{minutes_until} minutes"
            
            reminder_msg = f"⏰ Reminder: {task_text}\n📅 Due at {formatted_time} ({time_str})"
            
            try:
                bot.send_message(ALLOWED_USER_ID, reminder_msg)
                task_obj["reminded"] = True  # Mark as reminded
            except Exception as e:
                print(f"Failed to send reminder: {e}")


def get_stock_price(symbol: str) -> str:
    """
    Fetch current stock price using yfinance.
    Returns a user-friendly string.
    """
    symbol = symbol.upper().strip()
    if not symbol:
        return "Please provide a stock symbol, e.g. /stock AAPL."

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        currency = info.get("currency", "USD")

        if price is None:
            return f"Could not find a current price for {symbol}. Check the symbol and try again."

        return f"{symbol} is trading at {float(price):.2f} {currency}."
    except Exception as e:
        return f"Sorry, I couldn't fetch the price for {symbol}: {e}"


try:
    bot = telebot.TeleBot(TOKEN)
    register_commands(bot)
    
    print("🚀 Bot starting...")
    me = bot.get_me()
    print(f"✅ Connected as @{me.username}")
    
    # Start the reminder scheduler
    scheduler.add_job(check_reminders, 'interval', minutes=1)
    scheduler.start()

    @bot.message_handler(commands=['start', 'hello'])
    def send_welcome(message):
        if message.from_user.id != ALLOWED_USER_ID:
            return
        
        # Create the menu keyboard
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_tasks = types.KeyboardButton("📋 List tasks")
        btn_complete = types.KeyboardButton("✅ Complete task")
        keyboard.add(btn_tasks, btn_complete)
        
        bot.reply_to(message, 
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
        if message.from_user.id != ALLOWED_USER_ID:
            return

        text = message.text[len("/addtask"):].strip()
        if not text:
            bot.reply_to(message, "Usage: /addtask <task description>")
            return

        # Parse reminder time first
        text, reminder_minutes = parse_reminder_time(text)
        
        # Then parse datetime
        cleaned_text, due_time = parse_datetime_from_text(text)
        
        TASKS.append({
            "task": cleaned_text or text,
            "due": due_time,
            "reminder_minutes": reminder_minutes,
            "reminded": False,
        })
        save_tasks() 
        
        if due_time:
            formatted = due_time.strftime("%b %d at %I:%M %p")
            if reminder_minutes >= 60:
                hours = reminder_minutes // 60
                reminder_str = f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                reminder_str = f"{reminder_minutes} minutes"
            bot.reply_to(message, 
                f"Added task #{len(TASKS)}: {cleaned_text}\n"
                f"📅 Due: {formatted}\n"
                f"⏰ Reminder: {reminder_str} before"
            )
        else:
            bot.reply_to(message, f"Added task #{len(TASKS)}: {text}")

    @bot.message_handler(commands=['listtasks'])
    def handle_list_tasks(message):
        if message.from_user.id != ALLOWED_USER_ID:
            return

        if not TASKS:
            bot.reply_to(message, "Your task list is empty ✅")
            return

        # Create inline buttons for each task
        markup = InlineKeyboardMarkup()
        for idx, task_obj in enumerate(TASKS):
            task_text = task_obj["task"]
            due_time = task_obj.get("due")
            
            # Format button text
            if due_time:
                formatted = due_time.strftime("%b %d %I:%M %p")
                button_text = f"✅ {task_text} - {formatted}"
            else:
                button_text = f"✅ {task_text}"
            
            # Add button with callback data
            btn = InlineKeyboardButton(button_text, callback_data=f"done_{idx}")
            markup.add(btn)
        
        bot.reply_to(message, "Tap a task to mark it complete:", reply_markup=markup)



    @bot.message_handler(commands=['donetask'])
    def handle_done_task(message):
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

        if idx < 0 or idx >= len(TASKS):
            bot.reply_to(message, "That task number does not exist.")
            return

        done = TASKS.pop(idx)
        bot.reply_to(message, f"Marked as done: {done['task']} ✅")

    @bot.message_handler(commands=['tasks'])
    def cmd_tasks(message):
        if message.from_user.id != ALLOWED_USER_ID:
            return
        
        print("DEBUG: Using NEW inline button version!")
        
        if not TASKS:
            bot.reply_to(message, "Your task list is empty ✅")
            return

        # Create inline buttons for each task
        markup = InlineKeyboardMarkup()
        for idx, task_obj in enumerate(TASKS):
            task_text = task_obj["task"]
            due_time = task_obj.get("due")
            
            if due_time:
                formatted = due_time.strftime("%b %d %I:%M %p")
                button_text = f"✅ {task_text} - {formatted}"
            else:
                button_text = f"✅ {task_text}"
            
            btn = InlineKeyboardButton(button_text, callback_data=f"done_{idx}")
            markup.add(btn)
        
        bot.reply_to(message, "Tap a task to mark it complete:", reply_markup=markup)


    @bot.message_handler(commands=['menu'])
    def cmd_menu(message):
        if message.from_user.id != ALLOWED_USER_ID:
            return

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_tasks = types.KeyboardButton("📋 List tasks")
        btn_add_task = types.KeyboardButton("➕ Add task")
        btn_done_task = types.KeyboardButton("✅ Complete task")
        btn_stock = types.KeyboardButton("📈 Check stock price")
        keyboard.add(btn_tasks, btn_add_task)
        keyboard.add(btn_done_task, btn_stock)

        bot.reply_to(
            message,
            "Here's your menu:",
            reply_markup=keyboard,
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('done_'))
    def handle_task_completion(call):
        """Handle when user taps a task button to complete it"""
        if call.from_user.id != ALLOWED_USER_ID:
            bot.answer_callback_query(call.id, "Not authorized")
            return
        
        try:
            # Extract task index from callback data
            idx = int(call.data.split('_')[1])
            
            # Check if task still exists
            if idx < 0 or idx >= len(TASKS):
                bot.answer_callback_query(call.id, "Task no longer exists")
                return
            
            # Remove the task
            done_task = TASKS.pop(idx)
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

    @bot.message_handler(func=lambda msg: True)
    def chat_ai(message):
        if message.from_user.id != ALLOWED_USER_ID:
            return

        text_raw = message.text or ""
        text = text_raw.strip()

        if text == "✅ Complete task":
            if not TASKS:
                bot.reply_to(message, "You don't have any tasks to complete right now ✅")
            else:
                # Create inline buttons for each task
                markup = InlineKeyboardMarkup()
                for idx, task_obj in enumerate(TASKS):
                    btn = InlineKeyboardButton(
                        f"✅ {task_obj['task']}", 
                        callback_data=f"done_{idx}"
                    )
                    markup.add(btn)
                bot.reply_to(message, "Tap to complete:", reply_markup=markup)
            return  # ← Important: return here

        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        system_prompt = (
            "You're Igor's Telegram task assistant. Return valid JSON.\n\n"
            "For SINGLE task: Return one object\n"
            "For MULTIPLE tasks: Return array of objects\n\n"
            "Types:\n"
            '• add_task: {"type":"add_task","task":"description","reply":"confirmation"}\n'
            '• list_tasks: {"type":"list_tasks","reply":"sentence"}\n'
            '• remove_task: {"type":"remove_task","task":"description","reply":"confirmation"}\n'
            '• chat: {"type":"chat","reply":"answer"}\n\n'
            "Examples:\n"
            '"remind me gym tomorrow 6pm" → single add_task object\n'
            '"remind me to X and Y" → array of 2 add_task objects\n'
            '"I finished gym" → single remove_task object\n'
            "Return JSON only, no extra text."
        )

        data = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": text_raw}
            ]
        }

        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            raw = result["content"][0]["text"]
        except requests.exceptions.HTTPError as e:
            error_msg = f"🔴 API Error ({resp.status_code}):\n{resp.text[:200]}"
            bot.reply_to(message, error_msg)
            return
        except Exception as e:
            error_msg = f"🔴 Claude API error:\n{type(e).__name__}: {str(e)}"
            bot.reply_to(message, error_msg)
            return

        try:
            # Try to find JSON array first, then object
            json_str = raw.strip()
            
            # Remove any markdown code blocks
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            
            # Try array first
            array_start = json_str.find("[")
            array_end = json_str.rfind("]")
            
            # Try object
            obj_start = json_str.find("{")
            obj_end = json_str.rfind("}")
            
            # Determine which format to parse
            if array_start != -1 and array_end != -1 and (obj_start == -1 or array_start < obj_start):
                json_str = json_str[array_start:array_end + 1]
            elif obj_start != -1 and obj_end != -1:
                json_str = json_str[obj_start:obj_end + 1]
            else:
                raise ValueError("No valid JSON found in model output")
            
            parsed = json.loads(json_str)
            
            # Convert single object to array for uniform processing
            if isinstance(parsed, dict):
                parsed = [parsed]
            elif not isinstance(parsed, list):
                raise ValueError(f"Expected dict or list, got {type(parsed)}")
            
            # Process all actions
            reply_messages = []
            
            for item in parsed:
                reply_type = item.get("type")
                reply_text = (item.get("reply") or "").strip()
                
                if reply_type == "add_task":
                    task_text = (item.get("task") or "").strip()
                    if task_text:
                        # Parse reminder time first
                        task_text, reminder_minutes = parse_reminder_time(task_text)
                        
                        # Parse date/time from the task
                        cleaned_text, due_time = parse_datetime_from_text(task_text)
                        
                        TASKS.append({
                            "task": cleaned_text or task_text,
                            "due": due_time,
                            "reminder_minutes": reminder_minutes,
                            "reminded": False
                        })
                        save_tasks()
                        
                        if due_time:
                            formatted = due_time.strftime("%b %d at %I:%M %p")
                            if reminder_minutes >= 60:
                                hours = reminder_minutes // 60
                                reminder_str = f"{hours} hour{'s' if hours > 1 else ''}"
                            else:
                                reminder_str = f"{reminder_minutes} minutes"
                            reply_messages.append(f"✅ {cleaned_text or task_text}\n📅 Due: {formatted}\n⏰ Reminder: {reminder_str} before")
                        else:
                            reply_messages.append(reply_text or f"✅ {task_text}")
                    else:
                        reply_messages.append(reply_text or "Got it 👍")
                
                elif reply_type == "list_tasks":
                    if not TASKS:
                        bot.reply_to(message, "You don't have any tasks right now! 🎉")
                    else:
                        markup = InlineKeyboardMarkup()
                        for idx, task_obj in enumerate(TASKS):
                            task_text = task_obj["task"]
                            due_time = task_obj.get("due")
                            
                            if due_time:
                                formatted = due_time.strftime("%b %d %I:%M %p")
                                button_text = f"✅ {task_text} - {formatted}"
                            else:
                                button_text = f"✅ {task_text}"
                            
                            btn = InlineKeyboardButton(button_text, callback_data=f"done_{idx}")
                            markup.add(btn)
                        
                        bot.reply_to(message, "Tap a task to mark it complete:", reply_markup=markup)
                    return  # Return here to skip final reply
                
                elif reply_type == "remove_task":
                    task_text = (item.get("task") or "").strip().lower()
                    if not TASKS or not task_text:
                        reply_messages.append(reply_text or "I couldn't find a matching task to remove 🤔")
                    else:
                        removed = None
                        for i, task_obj in enumerate(TASKS):
                            existing = task_obj["task"]
                            if task_text in existing.lower() or existing.lower() in task_text:
                                removed = TASKS.pop(i)
                                save_tasks()
                                break
                        
                        if removed:
                            reply_messages.append(reply_text or f"✅ Marked as done: {removed['task']}")
                        else:
                            reply_messages.append(reply_text or "I couldn't find a matching task to remove 🤔")
                
                else:  # "chat"
                    reply_messages.append(reply_text or "Got it 👍")
            
            # Send combined reply
            if reply_messages:
                final_reply = "\n\n".join(reply_messages)
                bot.reply_to(message, final_reply)
        
        except Exception as e:
            final_reply = f"🔴 JSON parse error:\n{type(e).__name__}: {str(e)}\n\nRAW (first 500 chars):\n{raw[:500]}"
            bot.reply_to(message, final_reply)


    # IMPORTANT: keep polling at the end
    try:
        bot.remove_webhook()
        time.sleep(1)  # Wait for Telegram to process
    except:
        pass
    

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    bot.delete_webhook(drop_pending_updates=True)
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize bot with provided token. Error: {e}")
    print("The application will hang to prevent a restart loop. Please fix the TELEGRAM_BOT_TOKEN environment variable.")
    while True:
        time.sleep(3600)
