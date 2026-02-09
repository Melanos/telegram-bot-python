import os
import time
from telebot import types
import json
import telebot
import requests
from dotenv import load_dotenv
from commands import register_commands
import yfinance as yf  # NEW

# Load environment variables
load_dotenv()

# Tokens from env
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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
            "Here’s your menu:",
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

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://im-ai.tech",
            "X-Title": "Igor Telegram Bot",
        }

        system_prompt = (
            "You are Igor's personal AI assistant on Telegram.\n"
            "You can also manage his to-do list. The tasks themselves are stored "
            "outside of you; you must use JSON types to tell the system what to do.\n\n"
            "You MUST respond with a single valid JSON object and nothing else.\n"
            "Allowed formats:\n"
            "1) To ADD a new task or reminder (e.g. \"remind me to go to the gym at 6 PM\"), respond:\n"
            '   {\"type\": \"add_task\", \"task\": \"<short task description>\", '
            '\"reply\": \"<friendly confirmation with emojis>\"}\n'
            "2) To LIST Igor's existing tasks (e.g. if he asks \"do I have any tasks?\" or "
            "\"what do I have scheduled?\"), respond:\n"
            '   {\"type\": \"list_tasks\", \"reply\": \"<short friendly sentence>\"}\n'
            "   (The system will actually fetch and format the tasks; you don't need to know them.)\n"
            "3) To MARK a task as completed / remove it (e.g. \"I already went to the gym\"), respond:\n"
            '   {\"type\": \"remove_task\", \"task\": \"<short description of the task to remove>\", '
            '\"reply\": \"<friendly confirmation with emojis>\"}\n'
            "4) For normal chat (questions, small talk, anything not about tasks), respond:\n"
            '   {\"type\": \"chat\", \"reply\": \"<normal friendly answer with emojis>\"}\n\n'
            "Do NOT include any thoughts, explanations, or extra keys. Only output the JSON object."
        )

        data = {
            "model": "tngtech/deepseek-r1t-chimera:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_raw},
            ],
        }

        # Call OpenRouter once
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )
            print("OpenRouter debug:", resp.status_code, resp.text)
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            # TEMP: show detailed error in Telegram
            error_msg = f"🔴 LLM HTTP error:\n{type(e).__name__}: {str(e)}"
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
