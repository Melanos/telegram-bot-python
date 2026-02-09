import os
import time
import telebot
import requests
from dotenv import load_dotenv
from commands import register_commands

# Load environment variables
load_dotenv()

# Tokens from env
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Limit User Access
ALLOWED_USER_ID = 5244589395

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

        bot.reply_to(message, "Hello! I'm your personal Telegram bot.")

    @bot.message_handler(func=lambda msg: True)
    def chat_ai(message):
        """
        Send all incoming messages to OpenRouter and reply with the AI response.
        """
        if message.from_user.id != ALLOWED_USER_ID:
            return  # ignore everyone except you

        user_text = message.text

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://im-ai.tech",  # any URL you control
            "X-Title": "Igor Telegram Bot",
        }

        data = {
            "model": "tngtech/deepseek-r1t-chimera:free",
            # If that ever errors, alternative to try:
            # "model": "openrouter/deepseek/deepseek-r1-0528:free",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Igor's personal AI assistant on Telegram. "
                        "Be concise, friendly, and practical."
                    ),
                },
                {
                    "role": "user",
                    "content": user_text,
                },
            ],
        }

        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )
            # This will show the *real* error body in Railway logs
            print("OpenRouter debug:", resp.status_code, resp.text)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print("OpenRouter error:", e)
            reply = "Sorry, something went wrong talking to the AI."

        bot.reply_to(message, reply)

    # Remove webhook to avoid conflicts with polling
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling()

except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize bot with provided token. Error: {e}")
    print("The application will hang to prevent a restart loop. Please fix the TELEGRAM_BOT_TOKEN environment variable.")
    while True:
        time.sleep(3600)
