from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SqlEnum
from datetime import datetime
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    VIEWER = "viewer"
    SUBSCRIBER = "subscriber"
    VIP = "vip"
    MODERATOR = "moderator"
    BROADCASTER = "broadcaster"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    twitch_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True, nullable=False)
    display_name = Column(String)

    role = Column(SqlEnum(UserRole), default=UserRole.VIEWER)
    is_subscriber = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)
    is_vip = Column(Boolean, default=False)
    is_broadcaster = Column(Boolean, default=False)

    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_count = Column(Integer, default=0)
    command_count = Column(Integer, default=0)
    watch_hours = Column(Integer, default=0)  # Horas assistidas (aproximado)

    subscribed_at = Column(DateTime, nullable=True)
    subscription_tier = Column(String, nullable=True)

    followed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"