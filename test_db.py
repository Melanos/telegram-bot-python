from database.db_manager import init_database

# Initialize database
db = init_database()

# Test creating a user
user = db.create_or_update_user(
    telegram_id="YOUR_TELEGRAM_ID",
    name="Your Name",
    protein_target=180,
    workout_split="Push/Pull/Legs"
)
print(f"✅ User created: {user.name}")

# Test logging protein
tracking = db.log_protein(
    telegram_id="YOUR_TELEGRAM_ID",
    amount=50,
    notes="Chicken breast and protein shake"
)
print(f"✅ Protein logged: {tracking.protein_consumed}g")

# Test conversation storage
conversation = db.add_conversation(
    telegram_id="YOUR_TELEGRAM_ID",
    user_message="What should I eat for dinner?",
    bot_response="Here are some high-protein dinner ideas...",
    category="health"
)
print(f"✅ Conversation stored: ID {conversation.id}")
