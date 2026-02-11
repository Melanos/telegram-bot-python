"""API handlers for external services."""
import time
import json
import requests
import yfinance as yf
from datetime import datetime
from config import EST
from typing import Dict, Any, List, Union
from config import ANTHROPIC_API_KEY, MIN_API_INTERVAL


# Rate limiting
_last_api_call = 0


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
        f"You're Igor's Telegram task assistant. Return valid JSON.\n"
        f"Current time: {current_time_str}\n\n"
        "IMPORTANT: Parse ALL datetime info and return ISO format!\n\n"
        "For SINGLE task: Return one object\n"
        "For MULTIPLE tasks: Return array of objects\n\n"
        "Task Structure:\n"
        '• add_task: {"type":"add_task","task":"clean description","due":"ISO datetime or null","reminder_minutes":60,"reply":"confirmation"}\n'
        '• list_tasks: {"type":"list_tasks","reply":"sentence"}\n'
        '• remove_task: {"type":"remove_task","task":"description","reply":"confirmation"}\n'
        '• chat: {"type":"chat","reply":"answer"}\n\n'
        "DateTime Parsing Rules:\n"
        "1. 'in X minutes/hours' → Calculate exact ISO datetime from current time\n"
        "2. 'at 10pm today' → Use today's date with that time\n"
        "3. 'tomorrow at 6pm' → Use tomorrow's date with that time\n"
        "4. 'Friday 3pm' → Next Friday at 3pm\n"
        "5. No time mentioned → set 'due' to null\n\n"
        "Reminder Minutes:\n"
        "- User says 'remind me 30 minutes before' → reminder_minutes: 30\n"
        "- User says '2 hours before' → reminder_minutes: 120\n"
        "- No custom reminder → reminder_minutes: 60 (default)\n\n"
        "Examples:\n"
        '"remind me gym tomorrow at 6pm" → {"type":"add_task","task":"gym","due":"2026-02-11T18:00:00","reminder_minutes":60,"reply":"Got it!"}\n'
        '"pet harry in 5 minutes" → {"type":"add_task","task":"pet harry","due":"2026-02-10T22:30:00","reminder_minutes":60,"reply":"Added!"}\n'
        '"remind me 30 min before meeting at 3pm today" → {"type":"add_task","task":"meeting","due":"2026-02-10T15:00:00","reminder_minutes":30,"reply":"Set!"}\n'
        '"call mom" → {"type":"add_task","task":"call mom","due":null,"reminder_minutes":60,"reply":"Added!"}\n'
        '"I finished gym" → {"type":"remove_task","task":"gym","reply":"Nice work!"}\n\n'
        "Return JSON only, no extra text."
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
