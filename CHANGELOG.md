# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
