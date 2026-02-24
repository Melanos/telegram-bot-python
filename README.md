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
- **Natural Language Understanding** - Talk naturally without rigid commands
  - "I had 60g protein from eggs" → Logs protein
  - "Bench press 245 x6 felt easy" → Logs workout + progression tracking
  - "How am I doing today?" → Returns real stats from database
  - "Remind me to call mom tomorrow at 6pm" → Creates task
- **Tool Calling with Claude AI** - Intent recognition and automatic action execution
- **Multi-Exercise Parsing** - Log multiple exercises in one message
- **Progression Intelligence** - Detects when to increase weight based on performance
- **Context-Aware Conversations** - Remembers chat history for better understanding
- **Smart Timeline Parsing** - Understands "tomorrow", "in 5 minutes", day names, etc.

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
- `"I had 60g protein from eggs"` - Log protein naturally
- `"Bench press 245 x6 felt easy"` - Log workout with progression tracking
- `"How am I doing today?"` - Get your real stats
- `"Remind me to call John tomorrow at 2pm"` - Create a task naturally
- `/stock AAPL` - Check stock prices
- `/history` - View 7-day health trends

## Documentation

For detailed documentation, see the [`docs/`](docs/) folder:
- [📝 Changelog](docs/CHANGELOG.md) - Version history and release notes
- [✨ Features](docs/FEATURES.md) - Complete feature documentation
- [🗺️ Roadmap](docs/ROADMAP.md) - Future plans and development timeline
- [📅 30-Day Roadmap](docs/ROADMAP_30days.md) - Sprint planning
- [🐛 Known Issues](docs/KNOWN_ISSUES.md) - Current limitations and workarounds
- [🤝 Contributing](docs/CONTRIBUTING.md) - Contribution guidelines
- [🔧 Refactoring Notes](docs/REFACTORING.md) - Code restructuring documentation

## Learn More

- [Telebot Documentation](https://pypi.org/project/pyTelegramBotAPI/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Railway Documentation](https://docs.railway.app/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Telegram Python Bot Repository](https://github.com/aeither/telegram-bot-python/)
- [Railway Marketplace](https://railway.app/template/a0ln90)
