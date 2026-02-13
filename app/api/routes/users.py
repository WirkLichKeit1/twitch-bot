from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.core.database import get_db
from app.models import User
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    twitch_id: str
    username: str
    display_name: str
    role: str
    is_subscriber: bool
    is_moderator: bool
    message_count: int
    command_count: int
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    total_users: int
    total_messages: int
    total_commands: int
    active_today: int


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Lista todos os usuários"""
    result = await db.execute(
        select(User)
        .order_by(User.last_seen.desc())
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    return users


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    """Retorna estatísticas gerais dos usuários"""
    # Total de usuários
    total_users = await db.scalar(select(func.count(User.id)))

    # Total de mensagens
    total_messages = await db.scalar(select(func.sum(User.message_count))) or 0

    # Total de comandos
    total_commands = await db.scalar(select(func.sum(User.command_count))) or 0

    # Usuários ativos hoje
    today = datetime.utcnow().date()
    active_result = await db.execute(
        select(func.count(User.id))
        .where(func.date(User.last_seen) == today)
    )
    active_today = active_result.scalar() or 0

    return {
        "total_users": total_users or 0,
        "total_messages": total_messages,
        "total_commands": total_commands,
        "active_today": active_today
    }


@router.get("/{username}", response_model=UserResponse)
async def get_user(username: str, db: AsyncSession = Depends(get_db)):
    """Busca um usuário específico"""
    result = await db.execute(
        select(User).where(User.username == username.lower())
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return user


@router.get("/top/chatters", response_model=List[UserResponse])
async def get_top_chatters(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Retorna os usuários mais ativos no chat"""
    result = await db.execute(
        select(User)
        .order_by(User.message_count.desc())
        .limit(limit)
    )
    users = result.scalars().all()
    return users