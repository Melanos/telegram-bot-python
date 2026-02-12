"""Helper functions for database operations in the Telegram bot."""

def ensure_user_profile(db, message):
    """
    Create or update user profile from Telegram message.
    
    Args:
        db: DatabaseManager instance
        message: Telegram message object
    
    Returns:
        User object or None if database is unavailable
    """
    if db is None:
        return None
    
    try:
        telegram_id = str(message.from_user.id)
        user_name = message.from_user.first_name or "User"
        
        # Get or create user
        user = db.get_user(telegram_id)
        if not user:
            user = db.create_or_update_user(
                telegram_id=telegram_id,
                name=user_name
            )
            print(f"✅ New user registered: {user.name} (ID: {telegram_id})")
        
        return user
    except Exception as e:
        print(f"⚠️ Error ensuring user profile: {e}")
        return None


def log_conversation(db, message, bot_response, category="general"):
    """
    Log conversation to database.
    
    Args:
        db: DatabaseManager instance
        message: Telegram message object
        bot_response: Bot's response text
        category: Conversation category (default: "general")
    """
    if db is None:
        return
    
    try:
        telegram_id = str(message.from_user.id)
        db.add_conversation(
            telegram_id=telegram_id,
            user_message=message.text or "",
            bot_response=bot_response,
            category=category
        )
    except Exception as e:
        print(f"⚠️ Error logging conversation: {e}")


def log_health_data(db, telegram_id, protein=None, calories=None, workout=None):
    """
    Log health tracking data.
    
    Args:
        db: DatabaseManager instance
        telegram_id: User's Telegram ID (string)
        protein: Protein amount in grams (optional)
        calories: Calorie amount (optional)
        workout: Workout type/notes (optional)
    """
    if db is None:
        return
    
    try:
        if protein:
            db.log_protein(telegram_id, protein)
            print(f"📊 Logged {protein}g protein for user {telegram_id}")
        
        # Add calorie and workout logging later in Phase 2
        
    except Exception as e:
        print(f"⚠️ Error logging health data: {e}")
