"""
Script para popular o banco de dados com comandos built-in
Execute: python -m app.utils.seed_commands
"""
import asyncio
from app.core.database import AsyncSessionLocal, init_db
from app.models import Command, CommandType, UserRole
from sqlalchemy import select


async def seed_builtin_commands():
    """Adiciona comandos built-in ao banco de dados"""

    builtin_commands = [
        {
            "name": "perfil",
            "description": "Mostra informações do usuário",
            "command_type": CommandType.BUILTIN,
            "min_role": UserRole.VIEWER,
            "global_cooldown": 5,
            "user_cooldown": 30
        },
        {
            "name": "titulo",
            "description": "Mostra o título atual da live",
            "command_type": CommandType.BUILTIN,
            "min_role": UserRole.VIEWER,
            "global_cooldown": 10,
            "user_cooldown": 20
        },
        {
            "name": "jogo",
            "description": "Mostra o jogo/categoria atual",
            "command_type": CommandType.BUILTIN,
            "min_role": UserRole.VIEWER,
            "global_cooldown": 10,
            "user_cooldown": 20
        },
        {
            "name": "settitulo",
            "description": "[MOD] Altera o título da live",
            "command_type": CommandType.BUILTIN,
            "min_role": UserRole.MODERATOR,
            "global_cooldown": 0,
            "user_cooldown": 0
        },
        {
            "name": "setjogo",
            "description": "[MOD] Altera o jogo/categoria",
            "command_type": CommandType.BUILTIN,
            "min_role": UserRole.MODERATOR,
            "global_cooldown": 0,
            "user_cooldown": 0
        },
        {
            "name": "comandos",
            "description": "Lista todos os comandos disponíveis",
            "command_type": CommandType.BUILTIN,
            "min_role": UserRole.VIEWER,
            "global_cooldown": 15,
            "user_cooldown": 30
        },
        {
            "name": "uptime",
            "description": "Mostra há quanto tempo a live está online",
            "command_type": CommandType.BUILTIN,
            "min_role": UserRole.VIEWER,
            "global_cooldown": 10,
            "user_cooldown": 20
        }
    ]

    # Inicializa banco
    await init_db()

    async with AsyncSessionLocal() as session:
        for cmd_data in builtin_commands:
            # Verifica se já existe
            result = await session.execute(
                select(Command).where(Command.name == cmd_data["name"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                command = Command(**cmd_data)
                session.add(command)
                print(f"✅ Comando adicionado: !{cmd_data['name']}")
            else:
                print(f"⏭️  Comando já existe: !{cmd_data['name']}")

        await session.commit()

    print("\n✨ Seed de comandos concluído!")


if __name__ == "__main__":
    asyncio.run(seed_builtin_commands())