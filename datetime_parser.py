"""Utilities for parsing datetime and reminder information from text."""
import re
from datetime import datetime, timedelta
from typing import Tuple, Optional
from dateutil import parser as date_parser
from config import EST


def parse_reminder_time(text: str) -> Tuple[str, int]:
    """
    Extract custom reminder time from text.
    
    Args:
        text: Input text that may contain reminder instructions
        
    Returns:
        tuple: (cleaned_text, reminder_minutes)
    """
    text_lower = text.lower()
    
    # Pattern: "X minutes/hours/days before" (and variations)
    patterns = [
        (r'(\d+)\s*minutes?\s*before.*?(?:it|meeting|task|appointment)', 1),
        (r'(\d+)\s*minutes?\s*before', 1),
        (r'(\d+)\s*minutes?\s*prior', 1),
        (r'(\d+)\s*hours?\s*before', 60),
        (r'(\d+)\s*days?\s*before', 1440),
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, text_lower)
        if match:
            value = int(match.group(1))
            reminder_minutes = value * multiplier
            # Remove the entire reminder instruction
            cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
            # Clean up extra words
            cleaned = re.sub(r'\s*(it happens|the meeting|the task)\s*', '', cleaned, flags=re.IGNORECASE).strip()
            return cleaned, reminder_minutes
    
    # Default: 60 minutes
    return text, 60


def calculate_smart_reminder(due_time: datetime) -> int:
    """
    Automatically calculate optimal reminder time based on task duration.
    
    Args:
        due_time: When the task is due
        
    Returns:
        int: Minutes before due time to send reminder
    """
    if not due_time:
        return 60
    
    now = datetime.now(EST)
    minutes_until_due = (due_time - now).total_seconds() / 60
    
    if minutes_until_due < 5:
        return max(1, int(minutes_until_due * 0.5))
    elif minutes_until_due < 15:
        return 2
    elif minutes_until_due < 60:
        return 5
    elif minutes_until_due < 180:
        return 15
    else:
        return 60


def parse_datetime_from_text(text: str) -> Tuple[str, Optional[datetime]]:
    """
    Extract datetime from natural language using dateutil.
    
    Args:
        text: Input text containing date/time information
        
    Returns:
        tuple: (cleaned_text, datetime_object or None)
    """
    if not text:
        return text, None
    
    now = datetime.now(EST)
    text_lower = text.lower().strip()
    
    print(f"🔍 parse_datetime INPUT: '{text}'")
    print(f"🔍 Current time: {now}")
    
    # Handle relative time FIRST
    relative_pattern = r'\bin\s+(\d+)\s+(minute|minutes|hour|hours|min|mins|hr|hrs)\b'
    match = re.search(relative_pattern, text_lower)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit in ['minute', 'minutes', 'min', 'mins']:
            due_time = now + timedelta(minutes=amount)
        else:
            due_time = now + timedelta(hours=amount)
        
        cleaned = re.sub(relative_pattern, '', text, flags=re.IGNORECASE).strip()
        print(f"✅ RELATIVE match: amount={amount}, unit={unit}, due_time={due_time}")
        return cleaned, due_time
    
    # If no relative match, try dateutil
    print(f"⚠️ No relative match, trying dateutil parser...")
    
    try:
        # Check if "today" is explicitly mentioned
        has_today = bool(re.search(r'\btoday\b', text_lower))
        
        dt = date_parser.parse(text, fuzzy=True)
        print(f"📅 dateutil parsed: {dt}")
        
        # Make timezone-aware if naive
        if dt.tzinfo is None:
            dt = EST.localize(dt)
            print(f"🌍 Localized to EST: {dt}")
        
        # FIX: If user said "today", force it to be today
        now_aware = datetime.now(EST)
        if has_today and dt.date() != now_aware.date():
            print(f"⚠️ User said 'today' but dateutil gave {dt.date()}, forcing to today")
            dt = dt.replace(year=now_aware.year, month=now_aware.month, day=now_aware.day)
            print(f"✅ Corrected to: {dt}")
        
        # If parsed time is in the past and it's the same date, assume tomorrow
        if dt < now_aware:
            if dt.date() == now_aware.date():
                dt = dt + timedelta(days=1)
                print(f"⏭️ Time passed today, adjusted to tomorrow: {dt}")
        
        cleaned = re.sub(r'\b(at|on|tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', '', text, flags=re.IGNORECASE)
        cleaned = re.sub(r'\d{1,2}:\d{2}\s*(am|pm)?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\d{1,2}\s*(am|pm)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned, dt
    except Exception as e:
        print(f"❌ dateutil failed to parse: {e}")
        return text, None
