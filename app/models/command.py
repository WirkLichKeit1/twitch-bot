from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from datetime import datetime
from app.core.database import Base
from app.models.user import UserRole
import enum

class CommandType(str, enum.Enum):
    BUILTIN = "builtin"
    CUSTOM = "custom"

class Command(Base):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    response = Column(String, nullable=True)  # Para comandos customizados

    # Tipo e configuração
    command_type = Column(SQLEnum(CommandType), default=CommandType.CUSTOM)
    is_enabled = Column(Boolean, default=True)

    # Permissões
    min_role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)

    # Cooldown (em segundos)
    global_cooldown = Column(Integer, default=5)
    user_cooldown = Column(Integer, default=10)

    # Stats
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)

    # Metadata
    description = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Command !{self.name} ({self.command_type})>"