import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Get Railway's auto-generated DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==================== MODELS ====================

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    name = Column(String)
    timezone = Column(String, default="America/New_York")
    protein_target = Column(Integer, default=180)  # grams
    calorie_target = Column(Integer, default=2500)
    workout_split = Column(String)  # e.g., "Push/Pull/Legs"
    preferred_wake_time = Column(String)  # e.g., "07:00"
    preferred_workout_time = Column(String)  # e.g., "18:00"
    fitness_goals = Column(Text)
    dietary_restrictions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, index=True)
    session_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_message = Column(Text)
    bot_response = Column(Text)
    category = Column(String)  # e.g., "health", "learning", "general"
    extra_data = Column(JSON)  # Store extra context


class HealthTracking(Base):
    __tablename__ = "health_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    protein_consumed = Column(Float, default=0)
    calories_consumed = Column(Float, default=0)
    workout_completed = Column(Boolean, default=False)
    workout_type = Column(String)  # e.g., "Push", "Pull", "Legs"
    workout_duration = Column(Integer)  # minutes
    exercises = Column(JSON)  # List of exercises with sets/reps
    notes = Column(Text)


class Preference(Base):
    __tablename__ = "preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, index=True)
    category = Column(String)  # "food", "workout", "learning", "general"
    key = Column(String)
    value = Column(Text)
    confidence_score = Column(Float, default=1.0)  # How confident we are about this preference
    last_updated = Column(DateTime, default=datetime.utcnow)


class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, index=True)
    insight_type = Column(String)  # "pattern", "recommendation", "reminder"
    content = Column(Text)
    relevance_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_retrieved = Column(DateTime)


# ==================== DATABASE MANAGER ====================

class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """Create all tables if they don't exist"""
        Base.metadata.create_all(bind=self.engine)
        print("✅ Database tables created successfully!")
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    # ========== User Profile Operations ==========
    
    def create_or_update_user(self, telegram_id, **kwargs):
        """Create or update user profile"""
        session = self.get_session()
        try:
            user = session.query(UserProfile).filter(UserProfile.telegram_id == telegram_id).first()
            
            if user:
                # Update existing user
                for key, value in kwargs.items():
                    setattr(user, key, value)
                user.updated_at = datetime.utcnow()
            else:
                # Create new user
                user = UserProfile(telegram_id=telegram_id, **kwargs)
                session.add(user)
            
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()
    
    def get_user(self, telegram_id):
        """Get user profile"""
        session = self.get_session()
        try:
            return session.query(UserProfile).filter(UserProfile.telegram_id == telegram_id).first()
        finally:
            session.close()
    
    # ========== Conversation Operations ==========
    
    def add_conversation(self, telegram_id, user_message, bot_response, session_id=None, category=None, metadata=None):
        """Store a conversation interaction"""
        session = self.get_session()
        try:
            conversation = Conversation(
                telegram_id=telegram_id,
                session_id=session_id or f"session_{datetime.utcnow().strftime('%Y%m%d')}",
                user_message=user_message,
                bot_response=bot_response,
                category=category,
                extra_data=metadata or {}
            )
            session.add(conversation)
            session.commit()
            return conversation
        finally:
            session.close()
    
    def get_recent_conversations(self, telegram_id, limit=10):
        """Get recent conversation history"""
        session = self.get_session()
        try:
            return session.query(Conversation)\
                .filter(Conversation.telegram_id == telegram_id)\
                .order_by(Conversation.timestamp.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    # ========== Health Tracking Operations ==========
    
    def log_protein(self, telegram_id, amount, notes=None):
        """Log protein intake"""
        session = self.get_session()
        try:
            today = datetime.utcnow().date()
            tracking = session.query(HealthTracking)\
                .filter(HealthTracking.telegram_id == telegram_id)\
                .filter(HealthTracking.date >= today)\
                .first()
            
            if tracking:
                tracking.protein_consumed += amount
                if notes:
                    tracking.notes = f"{tracking.notes or ''}\n{notes}"
            else:
                tracking = HealthTracking(
                    telegram_id=telegram_id,
                    protein_consumed=amount,
                    notes=notes
                )
                session.add(tracking)
            
            session.commit()
            return tracking
        finally:
            session.close()
    
    def get_today_health(self, telegram_id):
        """Get today's health tracking data"""
        session = self.get_session()
        try:
            today = datetime.utcnow().date()
            return session.query(HealthTracking)\
                .filter(HealthTracking.telegram_id == telegram_id)\
                .filter(HealthTracking.date >= today)\
                .first()
        finally:
            session.close()
    
    # ========== Preference Operations ==========
    
    def add_preference(self, telegram_id, category, key, value, confidence_score=1.0):
        """Add or update a user preference"""
        session = self.get_session()
        try:
            pref = session.query(Preference)\
                .filter(Preference.telegram_id == telegram_id)\
                .filter(Preference.category == category)\
                .filter(Preference.key == key)\
                .first()
            
            if pref:
                pref.value = value
                pref.confidence_score = confidence_score
                pref.last_updated = datetime.utcnow()
            else:
                pref = Preference(
                    telegram_id=telegram_id,
                    category=category,
                    key=key,
                    value=value,
                    confidence_score=confidence_score
                )
                session.add(pref)
            
            session.commit()
            return pref
        finally:
            session.close()
    
    def get_preferences(self, telegram_id, category=None):
        """Get user preferences"""
        session = self.get_session()
        try:
            query = session.query(Preference).filter(Preference.telegram_id == telegram_id)
            if category:
                query = query.filter(Preference.category == category)
            return query.all()
        finally:
            session.close()


# ==================== INITIALIZE ====================

def init_database():
    """Initialize database and create tables"""
    db = DatabaseManager()
    db.create_tables()
    return db


if __name__ == "__main__":
    # Test database connection and create tables
    init_database()
    print("✅ Database initialized successfully!")
