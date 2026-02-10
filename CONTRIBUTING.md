# Contributing Guide

Thank you for considering contributing to this Telegram Bot project! This document provides guidelines and information for contributors.

## 📋 Table of Contents
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Issue Labels](#issue-labels)
- [Milestones](#milestones)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)

## Getting Started

### Prerequisites
- Python 3.11+
- Telegram Bot Token
- Anthropic Claude API Key
- Railway account (for deployment)

### Local Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables:
   ```bash
   TELEGRAM_BOT_TOKEN=your_token_here
   ANTHROPIC_API_KEY=your_key_here
   ```
4. Run locally: `python main.py`

## Development Workflow

### Creating Issues

#### Bug Reports
```markdown
**Description**: Clear, concise description of the bug

**Steps to Reproduce**:
1. Step one
2. Step two
3. Step three

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happens

**Environment**:
- OS: [e.g., iOS, Android, Desktop]
- Telegram Version: [e.g., 9.0]

**Screenshots**: If applicable
```

#### Feature Requests
```markdown
**Feature Description**: Clear description of the proposed feature

**Use Case**: Why is this feature needed?

**Proposed Solution**: How should it work?

**Alternatives Considered**: Other approaches you've thought about

**Additional Context**: mockups, examples, references
```

## Issue Labels

### Priority Labels
- 🔴 `high-priority` - Critical bugs or essential features
- 🟡 `medium-priority` - Important but not blocking
- 🟢 `low-priority` - Nice to have improvements

### Type Labels
- `bug` - Something isn't working correctly
- `enhancement` - New feature or improvement
- `documentation` - Documentation improvements
- `good-first-issue` - Easy to implement, good for newcomers
- `help-wanted` - Complex features needing discussion

### Status Labels
- `in-progress` - Currently being worked on
- `needs-testing` - Implemented but requires testing
- `blocked` - Waiting on dependencies or decisions

## Milestones

### v1.0 - Core Task Management ✅
**Status**: Completed  
**Features**: Basic task creation, listing, completion, persistent storage

### v1.1 - Stock Alerts 📈
**Target**: Next release  
**Features**: Price alert system, background monitoring

### v1.1.5 - Code Refactoring 🔧
**Target**: Before v1.2  
**Purpose**: Restructure codebase into modular architecture  
**Details**: See [ROADMAP.md](ROADMAP.md#version-115---code-refactoring-) for complete refactoring plan

### v1.2 - Voice Assistant 🎤
**Target**: TBD  
**Features**: Voice input processing, speech-to-text integration

### v2.0 - Smart Features 🧠
**Target**: TBD  
**Features**: Recurring tasks, task editing, smart follow-ups, categories, priorities

## Pull Request Process

### Before Submitting
1. ✅ Test your changes locally
2. ✅ Update documentation if needed
3. ✅ Add comments for complex logic
4. ✅ Ensure no debug print statements remain
5. ✅ Update CHANGELOG.md with your changes

### PR Template
```markdown
## Description
Brief description of changes

## Related Issue
Fixes #[issue number]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring

## Testing Done
Describe testing performed

## Screenshots
If applicable

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

### Review Process
1. Maintainer reviews code
2. Automated checks must pass
3. At least one approval required
4. Squash and merge to main branch

## Code Style

### Python Guidelines
- Follow PEP 8 conventions
- Use type hints where applicable
- Maximum line length: 100 characters
- Use descriptive variable names

### Example
```python
def parse_relative_time(time_str: str, base_time: datetime) -> Optional[datetime]:
    """
    Parse relative time expressions into absolute datetime.
    
    Args:
        time_str: Natural language time string (e.g., "in 5 minutes")
        base_time: Reference datetime for relative calculations
        
    Returns:
        Absolute datetime or None if parsing fails
    """
    # Implementation...
    pass
```

### Comments
- Use docstrings for functions and classes
- Add inline comments for complex logic
- Avoid obvious comments

### Commit Messages
Format: `type(scope): description`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(tasks): add recurring task support
fix(reminders): correct timezone handling in scheduler
docs(readme): update installation instructions
```

## Questions?

Feel free to open an issue labeled `question` or reach out to the maintainers.

Thank you for contributing! 🚀
