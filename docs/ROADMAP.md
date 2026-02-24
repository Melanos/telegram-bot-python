# Product Roadmap

This document outlines the planned features and improvements for the Telegram Bot project.

## 🗺️ Development Timeline

```
v1.0 ✅              → v1.1 📈          → v1.1.5 🔧        → v1.2 🎤          → v2.0+ 🚀
Core Tasks           Stock Alerts       Code Refactor      Voice Assistant    Advanced Features
(COMPLETED)          (Next Sprint)      (Infrastructure)   (High Priority)    (Future)
```

---

## Version 1.1 - Stock Alerts 📈
**Status**: Planned | **Priority**: High | **ETA**: Next release

### Features
- [ ] Set price alerts with `/alert SYMBOL PRICE`
- [ ] Background price checker (5-minute intervals)
- [ ] Alert notifications when target price is reached
- [ ] List active alerts via `/alerts` command
- [ ] Remove alerts with `/removealert SYMBOL`
- [ ] Persistent alert storage to JSON file

**Estimated Implementation Time**: 30-45 minutes

---

## Version 1.1.5 - Code Refactoring 🔧
**Status**: Planned | **Priority**: High | **Trigger**: After Stock Alerts, before Voice Assistant

### Objective
Restructure codebase into modular architecture to support rapid feature development and maintainability.

### Proposed Structure
```
telegram-bot-python/
├── main.py                 # Entry point (~50 lines)
├── config.py              # Environment variables, constants
├── handlers/
│   ├── __init__.py
│   ├── task_handler.py    # Task commands & operations
│   ├── stock_handler.py   # Stock price & alerts
│   ├── voice_handler.py   # Voice message processing
│   └── menu_handler.py    # Button callbacks
├── services/
│   ├── __init__.py
│   ├── ai_service.py      # Claude API interactions
│   ├── stock_service.py   # Stock API calls
│   ├── reminder_service.py # Background scheduler
│   └── storage_service.py # File I/O operations
├── utils/
│   ├── __init__.py
│   ├── time_parser.py     # Time/date parsing logic
│   ├── formatters.py      # Message formatting
│   └── validators.py      # Input validation
└── models/
    ├── __init__.py
    └── task.py            # Task dataclass/model
```

### Migration Plan
1. **Phase 1**: Extract utilities (time_parser.py, formatters.py)
2. **Phase 2**: Separate services (ai_service.py, storage_service.py)
3. **Phase 3**: Split handlers by feature
4. **Phase 4**: Create models and dataclasses
5. **Phase 5**: Update imports and test on Railway

### Benefits
- ✅ **Easier Debugging**: Isolated modules for targeted fixes
- ✅ **Parallel Development**: Work on multiple features simultaneously
- ✅ **Better Testing**: Unit test individual modules
- ✅ **Code Reusability**: Shared utilities across features
- ✅ **Cleaner Git History**: Changes scoped to specific files
- ✅ **Faster Onboarding**: Clear project structure for contributors

### Success Criteria
- [ ] All tests pass after refactoring
- [ ] No change in user-facing functionality
- [ ] Railway deployment successful
- [ ] Code coverage maintained or improved
- [ ] Documentation updated with new structure

**Estimated Implementation Time**: 90-120 minutes

**Rationale**: At ~800-1000 lines of code (after Stock Alerts), this is the optimal time to refactor before complexity becomes unmanageable.

---

## Version 1.2 - Voice Assistant 🎤
**Status**: Planned | **Priority**: High | **Dependencies**: OpenAI Whisper API

### Features
- [ ] Voice message handler for audio input
- [ ] Speech-to-text transcription using OpenAI Whisper API
- [ ] Process voice commands through existing AI handler
- [ ] Support voice commands for:
  - Task creation: "Remind me to call lawyer tomorrow at 2pm"
  - Stock queries: "What's IONQ stock price?"
  - General tasks: "Add buy protein powder to tasks"

**Estimated Implementation Time**: 60 minutes

---

## Version 2.0 - Smart Features 🧠
**Status**: Planned | **Priority**: Medium

### Features
- [ ] **Recurring Tasks**: "Every Monday at 6pm" scheduling
- [ ] **Task Editing**: Modify time/description after creation
- [ ] **Smart Follow-ups**: Bot proactively asks about overdue tasks
- [ ] **Auto-Reschedule**: "Not yet" response moves task to tomorrow
- [ ] **Task Categories**: Work, personal, fitness classifications
- [ ] **Task Priority**: High/medium/low urgency levels

**Estimated Implementation Time**: 45-60 minutes

---

## Version 2.1 - Health & Fitness 💪
**Status**: ✅ Partially Completed | **Priority**: Medium

### Features
- [ ] High-protein meal suggestions (personalized)
- [x] Workout logging: "Logged chest day" ✅
- [x] Weekly workout statistics (`/weekly`) ✅
- [x] Custom goal setting (`/setgoal`) ✅
- [ ] Macro tracking with quick food logging
- [ ] Gym streak counter for consistency tracking

### Completed (Feb 17, 2026)
- ✅ `/setgoal` - Customize protein & calorie targets
- ✅ `/weekly` - 7-day summary with trends & motivation
- ✅ Goal-based progress calculations in stats

**Estimated Implementation Time**: 45 minutes (25 minutes completed)

---

## Version 2.2 - Investment Features 💰
**Status**: Planned | **Priority**: Medium

### Features
- [ ] Portfolio tracking: `/portfolio add SYMBOL SHARES PRICE`
- [ ] Current portfolio value with gains/losses
- [ ] Daily portfolio performance summary
- [ ] Integration with stock alerts for unified view

**Estimated Implementation Time**: 45 minutes

---

## Version 2.3 - Learning & Business 📚
**Status**: ✅ Partially Completed | **Priority**: Low

### Features
- [ ] Personalized learning content feed
- [ ] Business ideas tracker with review system
- [ ] Market research helper for competitor analysis
- [x] Reading list tracker for articles/books ✅ (Completed Feb 23, 2026)

### Completed (Feb 23, 2026)
- ✅ Book tracking with natural language input
- ✅ Progress tracking with page numbers and percentages
- ✅ Book completion marking with timestamps
- ✅ Fuzzy match book removal
- ✅ Reading stats integration in `/stats` command
- ✅ SQLite database persistence
- ✅ AI-powered intent detection for reading operations

**Estimated Implementation Time**: 60 minutes (15 minutes completed)

---

## Version 3.0 - Calendar & Email Integration 📅
**Status**: Planned | **Priority**: Low | **Dependencies**: Google API credentials

### Features
- [ ] Google Calendar two-way sync
- [ ] Upcoming events calendar view in Telegram
- [ ] Daily email digest (tasks, stocks, workouts)
- [ ] Weekly review report with completed tasks and statistics

**Estimated Implementation Time**: 90 minutes

---

## Version 3.1 - Advanced AI Features 🤖
**Status**: Planned | **Priority**: Low

### Features
- [ ] Conversation memory for context retention
- [ ] Smart context understanding: "How's that stock?" recognizes IONQ
- [ ] Learning user preferences and patterns
- [ ] Proactive suggestions: "Time to go to gym?"

**Estimated Implementation Time**: 120 minutes

---

## Technical Debt & Quality Improvements

### Code Quality
- [ ] Remove debug logging after bug fixes
- [ ] Implement comprehensive error handling with user-friendly messages
- [ ] **Code Refactoring** - See [Version 1.1.5](#version-115---code-refactoring-) for detailed plan
- [ ] Add unit tests for critical functions
- [ ] Complete documentation with docstrings
- [ ] Security audit for API key storage and user validation

### Testing Infrastructure
- [ ] Set up pytest framework
- [ ] Unit tests for time parsing functions
- [ ] Integration tests for Claude AI responses
- [ ] Mock testing for external APIs (stock, Telegram)
- [ ] CI/CD pipeline with automated testing

### Performance Optimization
- [x] Database migration from JSON to SQLite ✅
- [ ] Caching layer for stock prices (reduce API calls)
- [ ] Async/await implementation for concurrent requests
- [ ] Memory profiling and optimization

### Development Workflow ✅ Completed (Feb 17, 2026)
- [x] Local development environment setup
- [x] Virtual environment with `uv` package manager
- [x] Local SQLite database configuration
- [x] Railway pause/resume workflow
- [x] 10x faster development cycle achieved

**Impact**: Reduced development iteration time from ~5 minutes (Railway deploy) to ~30 seconds (local testing)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this roadmap.
