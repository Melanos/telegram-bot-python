import os
import time
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

    @bot.message_handler(func=lambda msg: True)
    def chat_ai(message):
        """
        AI chat + implicit tasks (using wording, not JSON).
        For now, just respond like a normal assistant and hide the thinking.
        """
        if message.from_user.id != ALLOWED_USER_ID:
            return

        user_text = message.text

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://im-ai.tech",
            "X-Title": "Igor Telegram Bot",
        }

        data = {
            "model": "tngtech/deepseek-r1t-chimera:free",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Igor's personal AI assistant on Telegram. "
                        "Be concise, friendly, and practical. Emojis are allowed. "
                        "Think internally, but only output your final answer."
                    ),
                },
                {"role": "user", "content": user_text},
            ],
        }

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
            reply = extract_final_answer(raw)
        except Exception as e:
            print("OpenRouter error:", e)
            reply = "Sorry, something went wrong talking to the AI."

        bot.reply_to(message, reply)

    # IMPORTANT: keep polling at the end
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling()

except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize bot with provided token. Error: {e}")
    print("The application will hang to prevent a restart loop. Please fix the TELEGRAM_BOT_TOKEN environment variable.")
    while True:
        time.sleep(3600)
