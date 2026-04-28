"""UI helpers for creating keyboards and formatting messages."""
from datetime import datetime
from typing import List, Dict, Any
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import EST
import telebot
import os



def create_main_menu_keyboard():
    """Create the main menu keyboard with buttons."""
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Task buttons
    keyboard.add(
        telebot.types.KeyboardButton("📋 List tasks"),
        telebot.types.KeyboardButton("✅ Complete task")
    )
    
    # Health tracking buttons ⬇️ NEW
    keyboard.add(
        telebot.types.KeyboardButton("🥩 Log Protein"),
        telebot.types.KeyboardButton("💪 Log Workout")
    )
    
    keyboard.add(
        telebot.types.KeyboardButton("📊 My Stats"),
        telebot.types.KeyboardButton("📅 History")
    )
    
    # Stock alerts button
    keyboard.add(
        telebot.types.KeyboardButton("📚 Reading List"),
        telebot.types.KeyboardButton("🔔 My Alerts"),
    )

    ## News/Intersts
    keyboard.add(
    telebot.types.KeyboardButton("📰 News Digest"),
    telebot.types.KeyboardButton("🏷️ My Interests"),
    )
    
    return keyboard



def create_task_completion_keyboard(tasks: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with buttons for each task.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        InlineKeyboardMarkup with task completion buttons
    """
    markup = InlineKeyboardMarkup()
    for idx, task_obj in enumerate(tasks):
        task_text = task_obj["task"]
        due_time = task_obj.get("due")
        
        # Format button text
        if due_time:
            # Ensure timezone-aware
            if due_time.tzinfo is None:
                due_time = EST.localize(due_time)
            formatted = due_time.strftime("%b %d %I:%M %p")
            button_text = f"✅ {task_text} - {formatted}"
        else:
            button_text = f"✅ {task_text}"
        
        # Truncate long text
        if len(button_text) > 60:
            button_text = button_text[:57] + "..."
        
        # Add button with callback data
        btn = InlineKeyboardButton(button_text, callback_data=f"done_{idx}")
        markup.add(btn)
    
    return markup


def format_task_added_message(task_text: str, due_time: datetime = None, 
                               reminder_minutes: int = 60) -> str:
    """
    Format a message for when a task is added.
    
    Args:
        task_text: The task description
        due_time: When the task is due (optional)
        reminder_minutes: Minutes before due time for reminder
        
    Returns:
        Formatted message string
    """
    if due_time:
        # Ensure timezone-aware
        if due_time.tzinfo is None:
            due_time = EST.localize(due_time)
        formatted = due_time.strftime("%b %d at %I:%M %p")
        
        if reminder_minutes >= 60:
            hours = reminder_minutes // 60
            reminder_str = f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            reminder_str = f"{reminder_minutes} minutes"
        
        return (f"✅ {task_text}\n"
                f"📅 Due: {formatted}\n"
                f"⏰ Reminder: {reminder_str} before")
    else:
        return f"✅ {task_text}"


def format_reminder_message(task_text: str, due_time: datetime) -> str:
    """
    Format a reminder message.
    
    Args:
        task_text: The task description
        due_time: When the task is due
        
    Returns:
        Formatted reminder message
    """
    # Ensure timezone-aware
    if due_time.tzinfo is None:
        due_time = EST.localize(due_time)
    
    formatted_time = due_time.strftime("%I:%M %p")
    
    # Calculate time until due
    now = datetime.now(EST)
    minutes_until = int((due_time - now).total_seconds() / 60)
    
    if minutes_until >= 60:
        hours = minutes_until // 60
        time_str = f"in ~{hours} hour{'s' if hours > 1 else ''}"
    else:
        time_str = f"in ~{minutes_until} minutes"
    
    return f"⏰ Reminder: {task_text}\n📅 Due at {formatted_time} ({time_str})"


