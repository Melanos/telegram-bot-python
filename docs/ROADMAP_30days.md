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

## Week 3 – Voice Input + Reading & News ✅ COMPLETE!

### 7. Voice Input v1
- [ ] Handle Telegram voice messages (detect audio/voice message type).
- [ ] Download audio file and send to Groq Whisper for transcription.
- [ ] Route transcribed text through existing `chat_ai` natural-language pipeline.
- [ ] Support: voice tasks, gym logs, protein logs.
- **Status**: Parked — full design ready, estimated 15-min drop-in for Week 4.

### 8. Reading Tracker ✅
- [x] Added `reading` table (book title, author, start date, current page, total pages optional).
- [x] Implemented natural language intents: start, progress, finished, remove.
- [x] `/reading` command + "📚 Reading List" button shortcut.
- [x] Stats section in `/stats` showing active books with progress % and recently finished.

### 9. Interest Profile ✅
- [x] `interests` table with per-user tag storage.
- [x] Claude Haiku-powered tag extraction from messages, books, and news activity.
- [x] `/interests` command with add / remove / clear inline buttons and live refresh.

### 10. Personalized News Digest ✅
- [x] Per-tag fetching from quality sources: Reuters, Bloomberg, The Verge, Wired.
- [x] Relevancy sorting and story deduplication across tags.
- [x] `/news` command returning 3–5 stories with title, summary, and link.
- [x] 👍 / 👎 feedback buttons that update interest weights in real time.

### Morning Brief (Bonus) ✅
- [x] `/brief` command for on-demand personal briefing.
- [x] Scheduled delivery at **8:30 AM** via APScheduler.
- [x] Sections: tasks due today, news headlines, workout suggestion, reading progress, protein target.

---

## Week 4 – High Impact Features & Intelligence Upgrades

### 🔥 High Priority

| # | Feature | Notes |
|---|---------|-------|
| #7 | Voice Input | Groq Whisper — ~15-min drop-in |
| #11 | Finance Tracker | Log investments, ETF positions, P&L |
| #12 | Weekly Sunday Recap | Auto-sent at 7 PM Sunday |
| #13 | ⚖️ VeSync Scale Integration | pyvesync → weight sync, +5 lb nag, daily auto-check at 8 AM |

#### 7. Voice Input v1 (Drop-In)
- [ ] Handle Telegram voice messages.
- [ ] Download audio and send to **Groq Whisper** for transcription (~15-min integration).
- [ ] Route transcribed text through existing `chat_ai` pipeline.
- [ ] Support: voice tasks, gym logs, protein logs.

#### 11. Finance Tracker
- [ ] Log investment purchases: "Bought 5 shares of VTI at $230."
- [ ] Track ETF/stock positions with cost basis.
- [ ] `/portfolio` command — current holdings, total invested, unrealized P&L.
- [ ] Brief integration — show daily % change for tracked tickers each morning.

#### 12. Weekly Sunday Recap
- [ ] APScheduler job at **7:00 PM Sunday**.
- [ ] Sections: workout consistency (days trained, muscle groups hit), average daily protein vs goal, books finished or progressed, top 3 news topics of the week.
- [ ] Warn if a muscle group (e.g., legs) was skipped all week.

#### 13. ⚖️ VeSync Scale Integration
- [ ] Connect via `pyvesync` library to pull latest weigh-in automatically.
- [ ] Daily weight auto-check at **8:00 AM** (before morning brief).
- [ ] Nag message if weight is +5 lb above baseline: "You're 5 lb up — worth checking in."
- [ ] Weight shown in `/brief` — latest weigh-in + trend (up/down vs last 7 days).
- [ ] Weight shown in `/stats` — current weight + delta from baseline.

### 🧠 Intelligence Upgrades

#### Smarter Workout Rotation
- [ ] Detect actual Push / Pull / Legs gaps from workout history.
- [ ] Proactively warn if legs haven’t been trained in 5+ days.
- [ ] Suggest next session type based on last logged session.

#### Protein Trend Alerts
- [ ] Track consecutive days below protein goal.
- [ ] Proactive nudge: "You’ve missed your goal 3 days in a row — consider an extra shake today."

#### News Deduplication
- [ ] Collapse same story appearing from multiple sources into a single card.
- [ ] Show source count ("3 sources covering this").

### 🛠️ Quality of Life

#### /brief Personalization
- [ ] `/brief config` — toggle which sections appear (e.g., skip news on weekends).
- [ ] Per-section enable/disable stored in preferences table.

#### Stock Summary in Brief
- [ ] Show tracked tickers with daily % change in the morning brief automatically.

#### Reading Goal
- [ ] Set a "finish by" date per book.
- [ ] Brief shows days remaining + pages/day needed to hit the deadline.

#### Weight in /brief & /stats
- [ ] Latest weigh-in + 7-day trend in morning brief.
- [ ] `/stats` shows current weight + delta from baseline.

---

## Week 5+ – Bigger Swings

### Telegram Web Dashboard
- [ ] Visual charts for protein history, workout frequency, reading pace, and weight trend.
- [ ] Hosted as a simple web page linked from the bot.

### Claude Memory
- [ ] Weekly summarization of patterns (gym, protein, news topics, books, weight).
- [ ] Inject summary into Claude system prompt for persistent context across sessions.

### Expense Logging
- [ ] Natural language: "Spent $45 on groceries." → categorized entry.
- [ ] Monthly spend summary by category.
- [ ] `/expenses` command with category breakdown.

---

## Stretch Goals
- [ ] More advanced voice UX (e.g., "hands-free mode" sequences).
- [ ] More advanced pattern recognition and long-term trend insights across health, learning, and productivity.
