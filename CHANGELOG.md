# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-02-18

### Added
- **Week 2 Complete: AI Intent + Tool Calling for Health** 🧠
  - Natural language protein logging ("I had 60g protein from eggs")
  - Natural language workout logging ("Bench press 245 x6 felt easy")
  - Multi-exercise parsing in single messages
  - Progression detection with sentiment analysis ("felt easy" triggers suggestions)
  - "How am I doing today?" queries return real stats from database
  - AI-powered intent recognition for health tracking
  
- **Enhanced Health Intelligence** 🏋️
  - Workout progression tracking with weight/reps/notes per exercise
  - Smart progression suggestions based on performance patterns
  - Context-aware health queries with real-time stat retrieval
  - Multi-exercise session support in natural language
  
### Fixed
- **Timezone corrections** for `/history` and `/weekly` commands
  - Proper EST timezone handling for historical data display
  - Accurate date grouping for weekly summaries
  
### Changed
- **Updated `/help` command** with expanded natural language examples
  - Added "How am I doing today?" example
  - Clarified natural conversation capabilities
  - Improved formatting and categorization

---

## [2.0.0] - 2026-02-11

### Added
- **Database Infrastructure Migration** 🗄️
  - Migrated from PostgreSQL to SQLite for self-hosted deployment
  - Created 5-table relational schema: `users`, `conversations`, `health`, `preferences`, `insights`
  - Configured persistent volume storage for data durability
  - Implemented automatic schema initialization on first run
  
- **Health Tracking System** 🏋️
  - `/protein <grams> [notes]` - Log protein intake with optional meal notes
  - `/workout <type> <duration> [description]` - Log workouts (cardio, strength, flexibility)
  - `/stats` - Interactive daily progress dashboard with metrics
  - `/history` - 7-day tracking history with trends and insights
  - `/dbstats` - Database statistics and storage usage
  - Automatic health data persistence to SQLite
  
- **Enhanced User Interface** 📱
  - 4 new health tracking menu buttons (Protein Logger, Workout Logger, Daily Stats, 7-Day History)
  - Interactive data entry prompts with validation
  - Improved keyboard layout with categorized buttons
  - Enhanced `/help` command listing all health tracking capabilities
  
- **Database Integration** 🔗
  - Auto-user profile creation on first interaction
  - Comprehensive conversation logging for context
  - Persistent health metrics storage
  - Helper functions for common DB operations (create_user, log_conversation, get_user_stats)

### Changed
- **Cost Optimization**: $1.29/month → $0.15/month (~85% reduction)
  - SQLite eliminates cloud database fees
  - Persistent volume storage reduces API calls
  - Self-hosted approach provides scalability
  
- Updated requirements.txt with SQLite dependencies
- Enhanced error handling for database operations
- Improved logging with database operation tracking

### Technical Improvements
- **Multi-table Schema**: Normalized data structure for scalability
- **Transaction Safety**: Implemented proper commit/rollback for data consistency
- **Query Optimization**: Indexed frequently queried columns for performance
- **UTC→EST Conversion**: Fixed timezone display across all features
- **Data Validation**: Input validation for health metrics (weight, protein, etc.)
- **Conversation Context**: Chat history preserved for improved AI understanding

---

## [1.1.0] - 2026-02-10

### Added
- **Stock Price Alerts System**: Complete stock monitoring feature
  - `/alert SYMBOL PRICE [above|below]` - Set price alerts with directional triggers
  - `/alerts` - View all active alerts
  - `/removealert SYMBOL` - Remove specific alerts
  - Background monitoring every 5 minutes using APScheduler
  - Push notifications when price targets are hit
  - Persistent storage to `/app/data/alerts.json`
  - Created `stock_alerts.py` module for alert management
- **Enhanced Help System**: `/help` command with comprehensive documentation
- **Command Registration**: Updated bot commands (9 total commands with autocomplete)
- **Improved Stock Checker**: Enhanced error handling and formatting for `/stock` command
- **Menu Keyboard**: Added "📈 Check stock price" button for quick access
- `test_refactored.py` test suite for module validation
- `REFACTORING.md` documentation for new code structure
- `main_backup.py` backup of original monolithic code
- `requests` package to dependencies

### Changed
- **Major Code Refactoring**: Restructured codebase into modular components (793 → ~350 lines in main.py)
  - Created `config.py` for centralized configuration management
  - Created `task_manager.py` with TaskManager class for all task operations
  - Created `datetime_parser.py` for natural language date/time parsing utilities
  - Created `ui_helpers.py` for keyboard generation and message formatting
  - Created `api_handlers.py` for external API integrations (Claude AI, stock prices)
  - Created `reminder_system.py` for reminder checking logic
  - Created `stock_alerts.py` for stock price monitoring and alerts
- **Claude-Powered DateTime Parsing**: Switched from regex to AI-based datetime interpretation
  - Natural language parsing: "tomorrow at 6pm" → ISO datetime
  - Relative time support: "in 5 minutes" → exact timestamp
  - Smart defaults with automatic reminder calculation
  - Context-aware understanding of "today", "tomorrow", day names
  - Resolves previous bugs with "today" being parsed as "tomorrow"
- Enhanced code quality with type hints across all modules
- Centralized UI components for consistent formatting
- Updated welcome message with stock alerts information

### Fixed
- **Critical Bug Fixes** (10+ issues resolved):
  - Missing `validate_claude_datetime()` function imports
  - Import errors for `datetime`, `Optional`, and `DATA_DIR`
  - Wrong filename reference (`stock.py` → `stock_alerts.py`)
  - Missing timezone handling in reminder system
  - Double-response bug when listing tasks
  - Indentation issues causing incorrect behavior
  - Old parsing code conflicts after refactoring
  - Bot initialization order (bot now created before alert_manager)
  - Memory persistence issues (Railway volume configuration)
  - Command registration updates for new features
- Removed duplicate `validate_claude_datetime()` function from `api_handlers.py`
- Cleaned up redundant `main_refactored.py` file
- Confirmed ReadTimeoutError exceptions are normal (bot auto-recovers gracefully)

### Technical Improvements
- **Modular Architecture**: Separated concerns with single responsibility per module
- **Improved Testability**: Modules can be tested independently
- **Better Code Reusability**: Functions can be imported across modules
- **Enhanced Developer Experience**: Better IDE support through type hints
- **Reduced Code Duplication**: Centralized shared functionality
- **Persistent Data Storage**: All tasks and alerts survive bot restarts via Railway volumes
- **Automatic Data Saving**: Auto-save on every change to tasks or alerts
- **Enhanced Logging**: Better debug output for troubleshooting
- **Network Resilience**: Graceful handling of Telegram API timeout errors

## [1.0.0] - 2026-02-10

### Added
- **Task Management**: Add, list, and remove tasks via natural language commands
- **Multiple Tasks in One Message**: Parser handles "remind me to X and Y" creating 2 separate tasks
- **Persistent Storage**: Tasks saved to `/app/data/tasks.json` with Railway volume mounting
- **Menu Buttons**: Interactive "📋 List tasks" and "✅ Complete task" buttons
- **Inline Task Completion**: Tap task buttons to mark items complete
- **Stock Price Checker**: `/stock SYMBOL` command fetches current market prices
- **API Rate Limiting**: 2-second delay between Claude API calls to prevent rate limiting
- **Timezone Support**: EST timezone implemented (America/New_York)
- **Menu Button Optimization**: Direct code bypass prevents unnecessary API calls for menu interactions
- **Custom Reminder Times**: Support for "30 minutes before", "2 hours before" notifications
- **Graceful Shutdown**: Proper cleanup handlers on bot restart

### Fixed
- Task persistence after completion - completed tasks now saved immediately
- Desktop menu keyboard synchronization issues (documented workaround available)

### Technical Improvements
- Implemented background scheduler for reminder notifications
- Added timezone-aware datetime handling
- Optimized menu button response times
