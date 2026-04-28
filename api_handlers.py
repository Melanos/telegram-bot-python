"""API handlers for external services."""
import time
import json
import requests
import yfinance as yf
from datetime import datetime
from config import EST
from typing import Dict, Any, List, Union
from config import ANTHROPIC_API_KEY, MIN_API_INTERVAL
import threading
import re
import json
import requests
import os

# Rate limiting
_last_api_call = 0


def fetch_news(tags: list[str], page_size: int = 5) -> list[dict]:
    """Fetch headlines from NewsAPI matching interest tags."""
    query = " OR ".join(tags[:5])  # NewsAPI supports OR queries
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": os.getenv("NEWS_API_KEY")
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    return data.get("articles", [])


def summarize_article(title: str, description: str) -> str:
    """Use Claude Haiku to summarize an article to 1-2 sentences."""
    prompt = (
        f"Summarize this news article in 1-2 sentences, plain and direct:\n\n"
        f"Title: {title}\nDescription: {description}"
    )
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()

def get_stock_price(symbol: str) -> str:
    """
    Fetch current stock price using yfinance.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        User-friendly string with stock price information
    """
    symbol = symbol.upper().strip()
    if not symbol:
        return "Please provide a stock symbol, e.g. /stock AAPL."

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        currency = info.get("currency", "USD")

        if price is None:
            return f"Could not find a current price for {symbol}. Check the symbol and try again."

        return f"{symbol} is trading at {float(price):.2f} {currency}."
    except Exception as e:
        return f"Sorry, I couldn't fetch the price for {symbol}: {e}"


def call_claude_api(user_message: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Call Claude API to process user message and extract task intentions.
    
    Args:
        user_message: The user's input message
        
    Returns:
        List of action dictionaries or error dictionary
    """
    global _last_api_call
    
    # Get current time to give Claude context
    now = datetime.now(EST)
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    system_prompt = (
        f"You are Igor's personal AI assistant on Telegram. Return valid JSON only.\n"
        f"Current time: {current_time_str}\n\n"
        
        "RESPONSE TYPES:\n\n"
        
        "1. TASK MANAGEMENT:\n"
        '• add_task:    {"type":"add_task","task":"description","due":"ISO datetime or null","reminder_minutes":60,"reply":"confirmation"}\n'
        '• list_tasks:  {"type":"list_tasks","reply":"sentence"}\n'
        '• remove_task: {"type":"remove_task","task":"description","reply":"confirmation"}\n\n'
        
        "2. HEALTH & FITNESS:\n"
        '• log_protein: {"type":"log_protein","amount":60,"food":"chicken breast","reply":"confirmation"}\n'
        '• log_workout: {"type":"log_workout","workout_type":"Push","notes":"chest and triceps","exercises":[{"name":"Bench Press","weight":245,"reps":6,"sets":1,"notes":"felt easy"}],"reply":"confirmation"}\n'
        '• health_query:{"type":"health_query","reply":"answer based on context"}\n\n'
        
        "3. GENERAL:\n"
        '• chat:        {"type":"chat","reply":"helpful response"}\n\n'

        "4. READING TRACKING:\n"
        '• log_book_start:    {"type":"log_book_start","title":"book name","author":"name or null","total_pages":null,"reply":"confirmation"}\n'
        '• log_book_progress: {"type":"log_book_progress","title":"book name","page":87,"reply":"confirmation"}\n'
        '• log_book_finished: {"type":"log_book_finished","title":"book name","reply":"confirmation"}\n'
        '• remove_book:       {"type":"remove_book","title":"book name","reply":"confirmation"}\n\n'

        "5. INTEREST PROFILE:\n"
        '• view_interests: {"type":"view_interests","reply":"sentence"}\n'
        '• add_interest:   {"type":"add_interest","tag":"tag string","reply":"confirmation"}\n'
        '• remove_interest:{"type":"remove_interest","tag":"tag string","reply":"confirmation"}\n\n'
        
        "INTENT DETECTION RULES:\n"
        "Tasks → add_task/list_tasks/remove_task\n"
        "Protein mentions (ate, had, consumed + food/grams) → log_protein\n"
        "Workout/exercise mentions (gym, workout, sets, reps, lifted, trained) → log_workout\n"
        "Health questions (how am I doing, stats, progress) → health_query\n"
        "Reading mentions (reading, started, on page, finished + book title) → log_book_start/log_book_progress/log_book_finished\n"
        "Remove/delete book mentions (remove, delete, stop tracking + book title) → remove_book\n"
        "Everything else → chat\n\n"
        "Interest/topic mentions (interested in, love, hobby, curious about) → add_interest\n"
        "Show my interests/topics/tags → view_interests\n"
        
        "HEALTH PARSING RULES:\n"
        "• 'I had 60g protein from eggs' → log_protein: amount=60, food='eggs'\n"
        "• 'ate chicken breast 50g protein' → log_protein: amount=50, food='chicken breast'\n"
        "• 'drank a protein shake 40g' → log_protein: amount=40, food='protein shake'\n"
        "• 'bench press 245 x6 felt easy' → log_workout: exercises=[{name:'Bench Press',weight:245,reps:6,sets:1,notes:'felt easy'}]\n"
        "• 'did push day, bench 245x6 and tricep pushdowns' → log_workout with multiple exercises\n"
        "• 'finished leg day' → log_workout: workout_type='Legs', no exercise details\n"
        "• 'how am I doing today' → health_query\n\n"
        
        "PROGRESSION DETECTION:\n"
        "If user mentions 'felt easy', 'too light', 'could do more' → add notes field with that phrase so we can suggest progression.\n\n"
        
        "DATETIME PARSING RULES:\n"
        "1. 'in X minutes/hours' → Calculate exact ISO datetime from current time\n"
        "2. 'at 10pm today' → Use today's date with that time\n"
        "3. 'tomorrow at 6pm' → Use tomorrow's date\n"
        "4. 'Friday 3pm' → Next Friday at 3pm\n"
        "5. No time mentioned → set 'due' to null\n\n"
        
        "REMINDER MINUTES:\n"
        "- 'remind me 30 min before' → reminder_minutes: 30\n"
        "- '2 hours before' → reminder_minutes: 120\n"
        "- No custom reminder → reminder_minutes: 60\n\n"
        
        "EXAMPLES:\n"
        '"I had 60g protein from eggs" → {"type":"log_protein","amount":60,"food":"eggs","reply":"Logged 60g protein from eggs! 🥚"}\n'
        '"bench press 245 x6 felt easy" → {"type":"log_workout","workout_type":"Push","notes":"bench felt easy","exercises":[{"name":"Bench Press","weight":245,"reps":6,"sets":1,"notes":"felt easy"}],"reply":"Logged bench press 245x6! 💪"}\n'
        '"finished push day" → {"type":"log_workout","workout_type":"Push","notes":"push day","exercises":[],"reply":"Push day logged! 💪"}\n'
        '"how am I doing today?" → {"type":"health_query","reply":"Let me check your stats!"}\n'
        '"remind me gym tomorrow at 6pm" → {"type":"add_task","task":"gym","due":"2026-02-19T18:00:00","reminder_minutes":60,"reply":"Got it!"}\n'
        '"I just started Atomic Habits" → {"type":"log_book_start","title":"Atomic Habits","author":null,"total_pages":null,"reply":"📚 Tracking Atomic Habits! Let me know your progress."}\n'
        '"I\'m on page 87 of Atomic Habits" → {"type":"log_book_progress","title":"Atomic Habits","page":87,"reply":"📖 Page 87 saved!"}\n'
        '"I finished Atomic Habits" → {"type":"log_book_finished","title":"Atomic Habits","reply":"✅ Finished Atomic Habits! What did you think?"}\n'
        '"Remove Atomic Habits from my reading list" → {"type":"remove_book","title":"Atomic Habits","reply":"🗑️ Removed Atomic Habits from your reading list!"}\n'
        '"Stop tracking Deep Work" → {"type":"remove_book","title":"Deep Work","reply":"🗑️ Removed Deep Work from your reading list!"}\n\n'
        '"show my interests" → {"type":"view_interests","reply":"Here are your interest tags!"}\n'
        '"I\'m really into ETF investing" → {"type":"add_interest","tag":"etf investing","reply":"Added ETF investing to your interests! 🏷️"}\n'
        '"remove gym from my interests" → {"type":"remove_interest","tag":"gym","reply":"Removed gym from your interests."}\n'
        
        "MULTIPLE INTENTS IN ONE MESSAGE:\n"
        "If a message contains multiple actions, return a JSON ARRAY with one object per action.\n"
        "Example: 'I had 60g protein from eggs, bench press 245x6, and a protein shake 40g'\n"
        "Returns:\n"
        '[\n'
        '  {"type":"log_protein","amount":60,"food":"eggs","reply":"Logged 60g from eggs! 🥚"},\n'
        '  {"type":"log_workout","workout_type":"Push","exercises":[{"name":"Bench Press","weight":245,"reps":6,"sets":1,"notes":""}],"reply":"Bench press logged! 💪"},\n'
        '  {"type":"log_protein","amount":40,"food":"protein shake","reply":"Logged 40g from shake! 🥤"}\n'
        ']\n\n'
        "Always return an ARRAY when there are 2+ actions. Single object only for truly single actions.\n\n"

        "Return JSON only. No extra text. Single object for single action."
    )

    
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    
    data = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    
    # Rate limit protection
    now = time.time()
    if now - _last_api_call < MIN_API_INTERVAL:
        time.sleep(MIN_API_INTERVAL - (now - _last_api_call))
    _last_api_call = time.time()
    
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        raw = result["content"][0]["text"]
        
        # Parse JSON from response
        parsed = _parse_claude_response(raw)
        return parsed
        
    except requests.exceptions.HTTPError as e:
        return {
            "error": "http",
            "status_code": resp.status_code,
            "message": resp.text[:200]
        }
    except Exception as e:
        return {
            "error": "general",
            "type": type(e).__name__,
            "message": str(e)
        }


def _parse_claude_response(raw: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Parse Claude's JSON response.
    
    Args:
        raw: Raw text response from Claude
        
    Returns:
        Parsed list of actions or error dictionary
    """
    try:
        json_str = raw.strip()
        
        # Remove markdown code blocks if present
        if json_str.startswith("```"):
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        
        # Try array first, then object
        array_start = json_str.find("[")
        array_end = json_str.rfind("]")
        obj_start = json_str.find("{")
        obj_end = json_str.rfind("}")
        
        # Determine which format to parse
        if array_start != -1 and array_end != -1 and (obj_start == -1 or array_start < obj_start):
            json_str = json_str[array_start:array_end + 1]
        elif obj_start != -1 and obj_end != -1:
            json_str = json_str[obj_start:obj_end + 1]
        else:
            raise ValueError("No valid JSON found in model output")
        
        parsed = json.loads(json_str)
        
        # Convert single object to array for uniform processing
        if isinstance(parsed, dict):
            parsed = [parsed]
        elif not isinstance(parsed, list):
            raise ValueError(f"Expected dict or list, got {type(parsed)}")
        
        return parsed
        
    except Exception as e:
        return {
            "error": "parse",
            "type": type(e).__name__,
            "message": str(e),
            "raw": raw[:500]
        }
# ── Interest Tag Extraction ───────────────────────────────────────────────────

def _extract_interest_tags(telegram_id: str, message_text: str) -> None:
    """
    Calls Claude Haiku to extract interest tags from a message.
    Runs in a background daemon thread — never blocks the bot response.
    """
    from database.db_manager import DatabaseManager
    db = DatabaseManager()

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    data = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 150,
        "system": (
            "Extract 3-7 short interest/topic tags from the user message.\n"
            "Rules: lowercase, 1-3 words max. Only extract if genuine interest is shown — ignore filler/chit-chat.\n"
            "Return ONLY a raw JSON array of strings like: [\"investing\", \"python\", \"gym\"]\n"
            "Return [] if nothing meaningful to extract."
        ),
        "messages": [{"role": "user", "content": message_text}]
    }

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=15
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")

        tags = json.loads(raw)
        clean = [t.lower().strip() for t in tags if isinstance(t, str) and t.strip()]
        if clean:
            added = db.upsert_interests(telegram_id, clean)
            if added:
                print(f"[Interests] +{added} new tag(s) for {telegram_id}: {clean}")
    except Exception as e:
        print(f"[Interests] Extraction failed: {e}")


def track_interests(telegram_id: str, message_text: str) -> None:
    """Non-blocking entry point. Call after every user message."""
    threading.Thread(
        target=_extract_interest_tags,
        args=(telegram_id, message_text),
        daemon=True
    ).start()

