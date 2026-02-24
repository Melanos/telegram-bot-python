from telebot import TeleBot
from telebot.types import BotCommand

from telebot import TeleBot
from telebot.types import BotCommand


def register_commands(bot: TeleBot):
    """
    Register bot commands with Telegram.
    """
    commands = [
        # General
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show all commands"),
        BotCommand("menu", "Show menu keyboard"),

        # Tasks
        BotCommand("addtask", "Add a new task"),
        BotCommand("listtasks", "List all tasks"),
        BotCommand("donetask", "Complete a task (e.g., /donetask 1)"),

        # Health
        BotCommand("protein", "Log protein (e.g., /protein 50 chicken)"),
        BotCommand("workout", "Log workout (e.g., /workout Push - chest)"),
        BotCommand("stats", "Show today's progress"),
        BotCommand("history", "Show last 7 days"),
        BotCommand("weekly", "View 7-day summary and trends"),
        BotCommand("setgoal", "Set goals (e.g., /setgoal protein 180)"),
        BotCommand("resettoday", "Reset today's health data"),
        BotCommand("reading", "📚 View or add books you're reading"),

        # Stocks
        BotCommand("stock", "Check stock price (e.g., /stock AAPL)"),
        BotCommand("alert", "Set price alert (e.g., /alert IONQ 25 above)"),
        BotCommand("alerts", "View your active alerts"),
        BotCommand("removealert", "Remove an alert (e.g., /removealert IONQ)"),

        # Database
        BotCommand("dbstats", "Show database statistics"),
    ]
    
    bot.set_my_commands(commands)


