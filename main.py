import os
import time
from telebot import types
import json
import telebot
import requests
from dotenv import load_dotenv
from commands import register_commands
import yfinance as yf

# Load environment variables
load_dotenv()

# Tokens from env
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # ← Changed variable name

# Limit User Access
ALLOWED_USER_ID = 5244589395

# In-memory task list (per bot run)
TASKS = []  # simple list of strings


def extract_final_answer(text: str) -> str:
    """
    Take the last non-empty paragraph from the model output.
    This hides the reasoning and keeps only the final reply.
    """
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not parts:
        return text.strip()
    return parts[-1]


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
        info = ticker.info  # full info dict
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

    @bot.message_handler(commands=['start', 'hello'])
    def send_welcome(message):
        """
        Handle '/start' and '/hello' commands.
        """
        if message.from_user.id != ALLOWED_USER_ID:
            return  # ignore everyone except you

        bot.reply_to(message, "Hello! I'm your personal Telegram bot 🤖")

    @bot.message_handler(commands=['stock'])
    def handle_stock(message):
        """
        Usage: /stock AAPL
        """
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
        """
        Usage: /addtask Buy groceries
        """
        if message.from_user.id != ALLOWED_USER_ID:
            return

        text = message.text[len("/addtask"):].strip()
        if not text:
            bot.reply_to(message, "Usage: /addtask <task description>")
            return

        TASKS.append(text)
        bot.reply_to(message, f"Added task #{len(TASKS)}: {text}")

    @bot.message_handler(commands=['listtasks'])
    def handle_list_tasks(message):
        """
        List all tasks.
        """
        if message.from_user.id != ALLOWED_USER_ID:
            return

        if not TASKS:
            bot.reply_to(message, "Your task list is empty ✅")
            return

        lines = [f"{idx+1}. {task}" for idx, task in enumerate(TASKS)]
        reply = "Here are your current tasks:\n" + "\n".join(lines)
        bot.reply_to(message, reply)

    @bot.message_handler(commands=['donetask'])
    def handle_done_task(message):
        """
        Usage: /donetask 1
        """
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
        bot.reply_to(message, f"Marked as done: {done} ✅")

    ## Adding explicit commands
    @bot.message_handler(commands=['tasks'])
    def cmd_tasks(message):
        if message.from_user.id != ALLOWED_USER_ID:
            return
        if not TASKS:
            bot.reply_to(message, "Your task list is empty ✅")
            return
        lines = [f"{idx+1}. {task}" for idx, task in enumerate(TASKS)]
        bot.reply_to(message, "Here are your current tasks:\n" + "\n".join(lines))

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

    @bot.message_handler(func=lambda msg: True)
    def chat_ai(message):
        """
        AI chat + task management via simple tool protocol.
        """
        if message.from_user.id != ALLOWED_USER_ID:
            return

        text_raw = message.text or ""
        text = text_raw.strip()

        # If user taps "Complete task", guide them to use /donetask or natural language
        if text == "✅ Complete task":
            if not TASKS:
                bot.reply_to(message, "You don't have any tasks to complete right now ✅")
            else:
                lines = [f"{idx+1}. {task}" for idx, task in enumerate(TASKS)]
                reply = (
                    "Which task did you complete?\n"
                    "You can either:\n"
                    "- Say something like \"I finished: <task text>\" 🤖, or\n"
                    "- Use /donetask <number>\n\n"
                    "Here are your tasks:\n" + "\n".join(lines)
                )
                bot.reply_to(message, reply)
            return

        # ✅ FIXED: Anthropic API call
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,  # ← Fixed variable reference
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        # ✅ OPTIMIZED: 60% shorter system prompt (~150 tokens → ~60 tokens)
        system_prompt = (
            "You're Igor's Telegram task assistant. Respond ONLY with valid JSON.\n\n"
            "Types:\n"
            '• add_task: {"type":"add_task","task":"description","reply":"confirmation with emoji"}\n'
            '• list_tasks: {"type":"list_tasks","reply":"friendly sentence"}\n'
            '• remove_task: {"type":"remove_task","task":"description to remove","reply":"confirmation"}\n'
            '• chat: {"type":"chat","reply":"normal answer with emoji"}\n\n'
            "Examples:\n"
            '"remind me gym 6pm" → add_task\n'
            '"I finished gym" → remove_task\n'
            '"what tasks?" → list_tasks\n'
            "No extra text, only JSON."
        )

        data = {
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 1024,  # ← Reduced from 2048 (tasks don't need long responses)
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": text_raw}
            ]
        }

        # Call Anthropic API
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=30,
            )
            resp.raise_for_status()
            
            # ✅ FIXED: Correct response parsing
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

        # Extract JSON only (strip any accidental reasoning)
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("No JSON object found in model output")

            json_str = raw[start:end + 1]
            parsed = json.loads(json_str)

            reply_type = parsed.get("type")
            reply_text = (parsed.get("reply") or "").strip()

            if reply_type == "add_task":
                task_text = (parsed.get("task") or "").strip()
                if task_text:
                    TASKS.append(task_text)
                    idx = len(TASKS)
                    final_reply = reply_text or f"Got it, I saved: {task_text} (task #{idx} ✅)"
                else:
                    final_reply = reply_text or "Got it 👍"

            elif reply_type == "list_tasks":
                if not TASKS:
                    final_reply = "You don't have any tasks right now! 🎉"
                else:
                    lines = [f"{idx+1}. {task}" for idx, task in enumerate(TASKS)]
                    final_reply = "Here are your current tasks:\n" + "\n".join(lines)

            elif reply_type == "remove_task":
                task_text = (parsed.get("task") or "").strip().lower()
                if not TASKS or not task_text:
                    final_reply = reply_text or "I couldn't find a matching task to remove 🤔"
                else:
                    removed = None
                    for i, existing in enumerate(TASKS):
                        if task_text in existing.lower() or existing.lower() in task_text:
                            removed = TASKS.pop(i)
                            break

                    if removed:
                        final_reply = reply_text or f"Marked as done and removed: {removed} ✅"
                    else:
                        final_reply = reply_text or "I couldn't find a matching task to remove 🤔"

            else:  # "chat" or anything else
                final_reply = reply_text or "Got it 👍"

        except Exception as e:
            # TEMP: show parse error + raw output in Telegram
            final_reply = f"🔴 JSON parse error:\n{type(e).__name__}: {str(e)}\n\nRAW (first 500 chars):\n{raw[:500]}"

        bot.reply_to(message, final_reply)

    # IMPORTANT: keep polling at the end
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling()

except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize bot with provided token. Error: {e}")
    print("The application will hang to prevent a restart loop. Please fix the TELEGRAM_BOT_TOKEN environment variable.")
    while True:
        time.sleep(3600)
