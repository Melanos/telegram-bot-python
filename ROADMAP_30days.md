# 30-Day Roadmap – Personal AI Assistant

Goal: Build a personal AI assistant that helps with health, learning, content, schedule, inbox, and voice – fully personal, no employer context.

---

## Week 1 – Core Stability & Briefings

### 1. Stabilize Health + Tasks Foundation
- [ ] Polish `/setgoal`, `/weekly`, `/stats`, `/history`, `/resettoday` flows (edge cases, nicer messages).
- [ ] Ensure SQLite separation (local vs production) + backups + confirmed `.gitignore` for data/env/venv.
- [ ] Add consistent formatting for all health responses (titles, emojis, clear sections).

### 2. Morning Briefing v1
- [ ] Add `/setbriefing <time>` to configure a single daily briefing time (e.g., `07:30`).
- [ ] Implement APScheduler job that sends:
  - [ ] Today’s tasks (from task manager).
  - [ ] Daily protein goal and yesterday’s result.
  - [ ] Simple motivational line.
- [ ] Add `/briefing off` to disable daily briefing.

### 3. Quality-of-Life Upgrades
- [ ] Update `/help` with clear categories (Tasks, Health, Stocks, Briefings, Misc).
- [ ] Standardize error messages (usage hints, friendly tone).
- [ ] Ensure all commands respect `ALLOWED_USER_ID` consistently.

---

## Week 2 – Natural Language Health & Gym Intelligence ✅ COMPLETE!

### 4. AI Intent + Tool Calling for Health ✅
- [x] Define intents and tool schema for:
  - [x] Protein logging (amount, food, optional time).
  - [x] Workout logging (type, notes, exercise details like weight/reps).
  - [x] Progress queries ("How am I doing today?").
- [x] Extend Claude system prompt with function definitions (e.g., `log_protein`, `log_workout`).
- [x] Update `chat_ai` pipeline to:
  - [x] Call Claude with tool schema.
  - [x] Execute returned tool calls to log health data.
  - [x] Return a concise confirmation + summary message.

### 5. Workout Progression Intelligence ✅
- [x] Extend DB to store per-exercise history (exercise name, weight, reps, notes, date).
- [x] Implement simple progression logic:
  - [x] Detect repeated sessions at same weight with sufficient reps or comments like "felt easy".
  - [x] Suggest weight increases (e.g., +5 lb upper body, +10 lb lower body) when criteria met.
- [x] Add responses such as:
  - [x] "You benched 245 x6 for 3 weeks; next time try 250–255 for 5–6 reps."

### 6. Natural Conversation UX for Gym & Protein ✅
- [x] Handle free-form messages like:
  - [x] "Bench press 245 x6 felt easy today."
  - [x] "Did pull day with heavy rows and curls."
  - [x] "Had 60g protein from tuna and rice."
- [x] Confirm logs with short summaries:
  - [x] "Logged: Bench press – 245 x6, note: 'felt easy'."
  - [x] "Logged: 60g protein (tuna and rice)."

### 7. Quality-of-Life Fixes ✅
- [x] Fixed timezone display for `/history` and `/weekly` commands
- [x] Updated `/help` command with natural language examples

---

## Week 3 – Voice Input + Reading & News

### 7. Voice Input v1 (High Priority)
- [ ] Handle Telegram voice messages (detect audio/voice message type).
- [ ] Download audio file and send to a speech-to-text service (e.g., Whisper API or similar).
- [ ] Route transcribed text through existing `chat_ai` natural-language pipeline.
- [ ] Optimize for common use cases:
  - [ ] Voice tasks (“Remind me to pay the bill tomorrow at 9pm.”).
  - [ ] Voice gym logs (“Bench 245 for 6, felt easy.”).
  - [ ] Voice protein logs (“60 grams protein from a shake.”).

### 8. Reading Tracker
- [ ] Add `reading` table (book title, author, start date, current page, total pages optional).
- [ ] Implement:
  - [ ] `/reading start <book>` and natural “I’m starting <book>.” intent.
  - [ ] `/reading progress <page>` and natural “I’m at page <n> now.” intent.
- [ ] Add simple stats:
  - [ ] Average pages/day over last 7 days.
  - [ ] Estimated completion date at current pace.

### 9. Interest Profile
- [ ] Maintain an `interests` or `preferences` structure (e.g., tags like `AI`, `ML`, `finance`, `lifting`, `tech hardware`, `books`).
- [ ] Update interests based on:
  - [ ] Explicit statements (“I’m into X/Y/Z.”).
  - [ ] Topics of books, articles, and news clicked or requested.
- [ ] Add command `/interests` to view and lightly edit current interest tags.

### 10. Personalized News Digest v1
- [ ] Integrate a news API or curated RSS feeds.
- [ ] Implement `/news`:
  - [ ] Fetch 3–5 stories relevant to current interests.
  - [ ] Return title + 1–2 sentence summary + link.
- [ ] Add lightweight feedback:
  - [ ] “More like this” / “Less like this” buttons to tune interests.

---

## Week 4 – Calendar, Inbox Foundations & Proactive Brain

### 11. Personal Calendar Integration
- [ ] Choose provider: Google Calendar or personal Outlook.
- [ ] Implement auth for a personal account (local dev first).
- [ ] Add intents/commands:
  - [ ] “Schedule <event> on <date> at <time>.” → creates calendar event.
  - [ ] `/today` → today’s events + tasks + protein goal.
- [ ] Upgrade Morning Briefing to v2:
  - [ ] Include today’s events in the daily briefing.

### 12. Personal Email Summary (No Auto-Send)
- [ ] Connect a personal email inbox via API (e.g., Gmail).
- [ ] Implement:
  - [ ] `/inbox` or “Anything important in my email?” → top N emails summarized by simple priority rules.
- [ ] Draft replies (manual send only for now):
  - [ ] “Draft a reply to [subject/sender] saying <message>.” → returns suggested text.

### 13. Proactive Nudges v1
- [ ] Time- and pattern-based reminders:
  - [ ] Gym: “You usually train around 6 PM; it’s 5:40—plan today’s session?”
  - [ ] Reading: “You haven’t read your current book in 3 days; want a 10-page session tonight?”
  - [ ] Protein: “So far today: Xg/Yg protein; consider another meal/shake.”
- [ ] Add simple controls:
  - [ ] `/nudges on`, `/nudges off`.
  - [ ] Configurable quiet hours (e.g., no nudges 22:00–07:00).

### 14. Weekly Life Review
- [ ] Extend `/weekly` into multi-domain summary:
  - [ ] Fitness: workouts, average protein, consistency.
  - [ ] Reading: pages read and streak.
  - [ ] Tasks: tasks created vs completed.
- [ ] Optionally schedule a weekly summary (e.g., Sunday evening).

---

## Stretch Goals (If Time Allows)
- [ ] More advanced voice UX (e.g., “hands-free mode” sequences).
- [ ] Simple expense logging and high-level financial summary.
- [ ] More advanced pattern recognition and long-term trend insights across health, learning, and productivity.
