# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-02-10

### Changed
- **Major Code Refactoring**: Restructured codebase into modular components for better maintainability
  - Created `config.py` for centralized configuration management
  - Created `task_manager.py` with TaskManager class for all task operations
  - Created `datetime_parser.py` for natural language date/time parsing utilities
  - Created `ui_helpers.py` for keyboard generation and message formatting
  - Created `api_handlers.py` for external API integrations (Claude AI, stock prices)
  - Created `reminder_system.py` for reminder checking logic
  - Reduced `main.py` from 793 to ~350 lines (56% reduction)
- Enhanced code quality with type hints across all modules
- Centralized UI components for consistent formatting

### Added
- `test_refactored.py` test suite for module validation
- `REFACTORING.md` documentation for new code structure
- `main_backup.py` backup of original monolithic code
- `requests` package to dependencies

### Fixed
- Removed duplicate `validate_claude_datetime()` function from `api_handlers.py`
- Cleaned up redundant `main_refactored.py` file

### Technical Improvements
- Separated concerns: each module has single responsibility
- Improved testability: modules can be tested independently
- Better code reusability: functions can be imported across modules
- Enhanced developer experience with better IDE support through type hints
- Reduced code duplication by centralizing shared functionality

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
