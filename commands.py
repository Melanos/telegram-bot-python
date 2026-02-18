from telebot import TeleBot
from telebot.types import BotCommand

from telebot import TeleBot
from telebot.types import BotCommand


def register_commands(bot: TeleBot):
    """
    Register bot commands with Telegram.
    """
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show all commands"),
        BotCommand("menu", "Show menu keyboard"),
        BotCommand("addtask", "Add a new task"),
        BotCommand("listtasks", "List all tasks"),
        BotCommand("stock", "Check stock price (e.g., /stock AAPL)"),
        BotCommand("alert", "Set price alert (e.g., /alert IONQ 25 above)"),
        BotCommand("alerts", "View your active alerts"),
        BotCommand("removealert", "Remove an alert (e.g., /removealert IONQ)"),
        BotCommand("setgoal", "Set protein/calorie goals"),  # NEW
        BotCommand("weekly", "View 7-day health summary"),    # NEW
    ]
    
    bot.set_my_commands(commands)

