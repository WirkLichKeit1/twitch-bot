from twitchio.ext import commands
from typing import Optional, Dict, Callable
from datetime import datetime, timedelta
from app.core.config import settings
from app.services.twitch_api import twitch_api
from app.models import User, UserRole, Command, CommandType
from app.core.database import AsyncSessionLocal
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


class TwitchBot(commands.Bot):
    """Bot principal da Twitch com sistema de comandos"""

    def __init__(self):
        super().__init__(
            token=settings.twitch_bot_token,
            prefix=settings.command_prefix,
            initial_channels=[settings.twitch_channel]
        )

        self.global_cooldowns: Dict[str, datetime] = {}
        self.user_cooldowns: Dict[str, Dict[str, datetime]] = {}
        self.broadcaster_id: Optional[str] = None
        self.custom_command_handlers: Dict[str, Callable] = {}

    async def event_ready(self):
        """Evento quando o bot conecta"""
        logger.info(f'Bot conectado como | {self.nick}')
        logger.info(f'User ID: {self.user_id}')

        user_data = await twitch_api.get_user(settings.twitch_channel)
        if user_data:
            self.broadcaster_id = user_data['id']
            logger.info(f'Broadcaster ID: {self.broadcaster_id}')

    async def event_message(self, message):
        """Evento quando uma mensagem é enviada no chat"""
        if message.echo:
            return

        await self.update_user_stats(message)
        await self.handle_commands(message)

    async def update_user_stats(self, message):
        """Atualiza estatísticas do usuário no banco"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.twitch_id == str(message.author.id))
            )
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    twitch_id=str(message.author.id),
                    username=message.author.name,
                    display_name=message.author.display_name or message.author.name,
                    is_subscriber=message.author.is_subscriber,
                    is_moderator=message.author.is_mod,
                    is_broadcaster=message.author.name.lower() == settings.twitch_channel.lower()
                )

                if user.is_broadcaster:
                    user.role = UserRole.BROADCASTER
                elif user.is_moderator:
                    user.role = UserRole.MODERATOR
                elif message.author.is_subscriber:
                    user.role = UserRole.SUBSCRIBER
                else:
                    user.role = UserRole.VIEWER

                if self.broadcaster_id:
                    try:
                        follower_info = await twitch_api.get_follower_info(
                            self.broadcaster_id,
                            str(message.author.id)
                        )
                        if follower_info:
                            user.followed_at = datetime.fromisoformat(
                                follower_info.get('followed_at').replace('Z', '+00:00')
                            ).replace(tzinfo=None)

                        if message.author.is_subscriber:
                            sub_info = await twitch_api.get_subscriber_info(
                                self.broadcaster_id,
                                str(message.author.id)
                            )
                            if sub_info:
                                user.subscription_tier = sub_info.get('tier', '1000')
                    except Exception as e:
                        logger.warning(f"Erro ao buscar dados da API: {e}")

                session.add(user)
            else:
                user.last_seen = datetime.utcnow()
                user.message_count += 1
                user.is_subscriber = message.author.is_subscriber
                user.is_moderator = message.author.is_mod

            await session.commit()

    async def get_user_from_db(self, twitch_id: str) -> Optional[User]:
        """Busca usuário no banco de dados"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.twitch_id == twitch_id)
            )
            return result.scalar_one_or_none()

    async def get_command_from_db(self, command_name: str) -> Optional[Command]:
        """Busca comando no banco de dados"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Command).where(
                    Command.name == command_name.lower(),
                    Command.is_enabled == True
                )
            )
            return result.scalar_one_or_none()

    def check_cooldown(self, command_name: str, user_id: str, global_cd: int, user_cd: int) -> bool:
        """Verifica se o comando está em cooldown"""
        now = datetime.utcnow()

        if command_name in self.global_cooldowns:
            if now < self.global_cooldowns[command_name]:
                return False

        if user_id in self.user_cooldowns:
            if command_name in self.user_cooldowns[user_id]:
                if now < self.user_cooldowns[user_id][command_name]:
                    return False

        self.global_cooldowns[command_name] = now + timedelta(seconds=global_cd)

        if user_id not in self.user_cooldowns:
            self.user_cooldowns[user_id] = {}
        self.user_cooldowns[user_id][command_name] = now + timedelta(seconds=user_cd)

        return True

    def register_command_handler(self, command_name: str, handler: Callable):
        """Registra um handler customizado para um comando"""
        self.custom_command_handlers[command_name] = handler