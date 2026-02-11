"""Configuration settings for the Telegram bot."""
import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot tokens
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# User access control
ALLOWED_USER_ID = 5244589395

# API rate limiting
MIN_API_INTERVAL = 2  # seconds between API calls

# Timezone
EST = pytz.timezone('America/New_York')

# File paths
TASKS_FILE = "/app/data/tasks.json"

# Reminder settings
DEFAULT_REMINDER_MINUTES = 60
