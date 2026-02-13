from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_db
from app.models import Command, CommandType, UserRole
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/commands", tags=["commands"])


class CommandCreate(BaseModel):
    name: str
    response: str
    description: Optional[str] = None
    min_role: UserRole = UserRole.VIEWER
    global_cooldown: int = 5
    user_cooldown: int = 10


class CommandUpdate(BaseModel):
    response: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    min_role: Optional[UserRole] = None
    global_cooldown: Optional[int] = None
    user_cooldown: Optional[int] = None


class CommandResponse(BaseModel):
    id: int
    name: str
    response: Optional[str]
    command_type: str
    is_enabled: bool
    min_role: str
    global_cooldown: int
    user_cooldown: int
    usage_count: int
    description: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CommandResponse])
async def get_commands(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Lista todos os comandos"""
    query = select(Command)

    if enabled_only:
        query = query.where(Command.is_enabled == True)

    result = await db.execute(query.order_by(Command.name))
    commands = result.scalars().all()
    return commands


@router.post("/", response_model=CommandResponse, status_code=201)
async def create_command(
    command: CommandCreate,
    db: AsyncSession = Depends(get_db)
):
    """Cria um novo comando customizado"""
    # Verifica se já existe
    existing = await db.execute(
        select(Command).where(Command.name == command.name.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Comando já existe")

    # Cria o comando
    new_command = Command(
        name=command.name.lower(),
        response=command.response,
        description=command.description,
        command_type=CommandType.CUSTOM,
        min_role=command.min_role,
        global_cooldown=command.global_cooldown,
        user_cooldown=command.user_cooldown
    )

    db.add(new_command)
    await db.commit()
    await db.refresh(new_command)

    return new_command


@router.get("/{command_name}", response_model=CommandResponse)
async def get_command(command_name: str, db: AsyncSession = Depends(get_db)):
    """Busca um comando específico"""
    result = await db.execute(
        select(Command).where(Command.name == command_name.lower())
    )
    command = result.scalar_one_or_none()

    if not command:
        raise HTTPException(status_code=404, detail="Comando não encontrado")

    return command


@router.patch("/{command_name}", response_model=CommandResponse)
async def update_command(
    command_name: str,
    updates: CommandUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Atualiza um comando existente"""
    result = await db.execute(
        select(Command).where(Command.name == command_name.lower())
    )
    command = result.scalar_one_or_none()

    if not command:
        raise HTTPException(status_code=404, detail="Comando não encontrado")

    # Não permite editar comandos built-in
    if command.command_type == CommandType.BUILTIN:
        raise HTTPException(status_code=403, detail="Não é possível editar comandos nativos")

    # Atualiza campos
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(command, field, value)

    command.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(command)

    return command


@router.delete("/{command_name}")
async def delete_command(command_name: str, db: AsyncSession = Depends(get_db)):
    """Deleta um comando customizado"""
    result = await db.execute(
        select(Command).where(Command.name == command_name.lower())
    )
    command = result.scalar_one_or_none()

    if not command:
        raise HTTPException(status_code=404, detail="Comando não encontrado")

    # Não permite deletar comandos built-in
    if command.command_type == CommandType.BUILTIN:
        raise HTTPException(status_code=403, detail="Não é possível deletar comandos nativos")

    await db.delete(command)
    await db.commit()

    return {"message": f"Comando {command_name} deletado com sucesso"}