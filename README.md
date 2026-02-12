## Telegram Python Bot

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/a0ln90?referralCode=CREDITS&utm_medium=integration&utm_source=template&utm_campaign=generic)

## Overview

A feature-rich Telegram bot with task management, stock alerts, and health tracking capabilities. Built with Python, powered by Claude AI for natural language understanding, and backed by SQLite for persistent local storage.

## Key Features

### 📋 Task Management
- Natural language task creation ("Remind me to...") powered by Claude AI
- Smart reminder calculation based on due times
- Persistent storage with auto-save
- Interactive task completion buttons

### 🏋️ Health Tracking
- **Protein Logger** - `/protein` - Log daily protein intake with meal notes
- **Workout Logger** - `/workout` - Track exercises and duration
- **Daily Stats** - `/stats` - View daily health metrics dashboard
- **History** - `/history` - 7-day tracking with trends and insights
- **Database Stats** - `/dbstats` - Storage and usage information

### 📈 Stock Market
- Real-time stock price checking with `/stock SYMBOL`
- Price alert system (`/alert`, `/alerts`, `/removealert`)
- Background monitoring every 5 minutes
- Directional triggers (above/below price targets)

### 🤖 AI-Powered Intelligence
- Claude AI for natural language understanding
- Intent recognition (task creation, task completion, general chat)
- Context-aware conversations with chat history
- Smart timeline parsing ("tomorrow", "in 5 minutes", etc.)

### 🗄️ Database Infrastructure
- SQLite for self-hosted deployment (85% cost reduction vs PostgreSQL)
- Persistent volume storage for Railway deployments
- 5-table relational schema for data integrity
- Automatic user profile creation and conversation logging

## Setup

```bash
pip install uv
uv sync
```

## Develop

To run the bot locally:

```bash
uv run python -B main.py
```

Make sure to set up your `.env` file with required credentials:

```bash
TELEGRAM_BOT_TOKEN=your_token_here
ANTHROPIC_API_KEY=your_claude_api_key
```

## Deploy

Initialize your project:

```bash
railway init
```

To deploy the bot on Railway:

```bash
railway up
```

Remember to set the `TELEGRAM_BOT_TOKEN` and `ANTHROPIC_API_KEY` environment variables in your Railway project settings.

## Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `/start` | `/start` | Welcome message and menu |
| `/help` | `/help` | Show all available commands |
| `/addtask` | `/addtask <description>` | Add a new task |
| `/listtasks` | `/listtasks` | View all active tasks |
| `/donetask` | `/donetask <number>` | Mark task as complete |
| `/stock` | `/stock SYMBOL` | Check stock price |
| `/alert` | `/alert SYMBOL PRICE [above/below]` | Set price alert |
| `/alerts` | `/alerts` | View active alerts |
| `/removealert` | `/removealert SYMBOL` | Remove price alert |
| `/protein` | `/protein <grams> [notes]` | Log protein intake |
| `/workout` | `/workout <type> <minutes>` | Log workout session |
| `/stats` | `/stats` | View daily health metrics |
| `/history` | `/history` | View 7-day tracking history |
| `/dbstats` | `/dbstats` | Database statistics |
| `/menu` | `/menu` | Show menu buttons |

## Test

Open Telegram, start a chat with your bot, and try:
- `/start` - See the welcome message
- `"Remind me to call John tomorrow at 2pm"` - Create a task naturally
- `/stock AAPL` - Check stock prices
- `/protein 150 eggs for breakfast` - Log protein intake

## Learn More

- [Telebot Documentation](https://pypi.org/project/pyTelegramBotAPI/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Railway Documentation](https://docs.railway.app/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Telegram Python Bot Repository](https://github.com/aeither/telegram-bot-python/)
- [Railway Marketplace](https://railway.app/template/a0ln90)
