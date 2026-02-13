from twitchio.ext import commands
from app.services.twitch_api import twitch_api
from app.models import UserRole
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def register_commands(bot):
    """Registra todos os comandos no bot"""

    @bot.command(name='perfil')
    async def perfil_command(ctx: commands.Context):
        """Mostra informações do perfil do usuário"""
        user = await bot.get_user_from_db(str(ctx.author.id))

        if not user:
            await ctx.send(f"@{ctx.author.name}, não encontrei suas informações!")
            return

        # Calcula tempo seguindo
        tempo_seguindo = "Não está seguindo"
        if user.followed_at:
            delta = datetime.utcnow() - user.followed_at
            dias = delta.days
            tempo_seguindo = f"{dias} dias"

        # Calcula tempo de inscrição
        tempo_sub = "Não é inscrito"
        if user.subscribed_at:
            delta = datetime.utcnow() - user.subscribed_at
            meses = delta.days // 30
            tempo_sub = f"{meses} meses (Tier {user.subscription_tier or '1'})"

        # Status
        status = []
        if user.is_broadcaster:
            status.append("🎙️ Broadcaster")
        if user.is_moderator:
            status.append("🛡️ Moderador")
        if user.is_subscriber:
            status.append("⭐ Inscrito")
        if user.is_vip:
            status.append("💎 VIP")

        status_str = " | ".join(status) if status else "👤 Viewer"

        await ctx.send(
            f"@{ctx.author.name} | {status_str} | "
            f"Seguindo: {tempo_seguindo} | "
            f"Sub: {tempo_sub} | "
            f"Mensagens: {user.message_count} | "
            f"Comandos: {user.command_count}"
        )


    @bot.command(name='titulo')
    async def titulo_command(ctx: commands.Context):
        """Mostra o título atual da live"""
        if not bot.broadcaster_id:
            await ctx.send("Erro ao buscar informações do canal!")
            return

        channel_info = await twitch_api.get_channel_info(bot.broadcaster_id)

        if channel_info:
            titulo = channel_info.get('title', 'Sem título')
            await ctx.send(f"📺 Título atual: {titulo}")
        else:
            await ctx.send("Não foi possível buscar o título!")


    @bot.command(name='jogo')
    async def jogo_command(ctx: commands.Context):
        """Mostra o jogo/categoria atual"""
        if not bot.broadcaster_id:
            await ctx.send("Erro ao buscar informações do canal!")
            return

        channel_info = await twitch_api.get_channel_info(bot.broadcaster_id)

        if channel_info:
            jogo = channel_info.get('game_name', 'Nenhum jogo definido')
            await ctx.send(f"🎮 Jogando: {jogo}")
        else:
            await ctx.send("Não foi possível buscar o jogo!")


    @bot.command(name='settitulo')
    async def set_titulo_command(ctx: commands.Context, *, novo_titulo: str):
        """[MOD] Altera o título da live"""
        # Verifica se é mod ou broadcaster
        if not (ctx.author.is_mod or ctx.author.name.lower() == bot._initial_channels[0].lower()):
            await ctx.send(f"@{ctx.author.name}, você precisa ser moderador para usar este comando!")
            return

        if not bot.broadcaster_id:
            await ctx.send("Erro ao identificar o canal!")
            return

        success = await twitch_api.update_channel_info(
            bot.broadcaster_id,
            title=novo_titulo
        )

        if success:
            await ctx.send(f"✅ Título alterado para: {novo_titulo}")
            logger.info(f"Título alterado por {ctx.author.name}: {novo_titulo}")
        else:
            await ctx.send("❌ Erro ao alterar o título!")


    @bot.command(name='setjogo')
    async def set_jogo_command(ctx: commands.Context, *, nome_jogo: str):
        """[MOD] Altera o jogo/categoria da live"""
        # Verifica se é mod ou broadcaster
        if not (ctx.author.is_mod or ctx.author.name.lower() == bot._initial_channels[0].lower()):
            await ctx.send(f"@{ctx.author.name}, você precisa ser moderador para usar este comando!")
            return

        if not bot.broadcaster_id:
            await ctx.send("Erro ao identificar o canal!")
            return

        # Nota: A API da Twitch requer o game_id, não o nome
        # Para implementação completa, seria necessário buscar o game_id primeiro
        await ctx.send(f"⚠️ Para alterar o jogo, use o painel da Twitch por enquanto. Feature em desenvolvimento!")


    @bot.command(name='comandos')
    async def comandos_command(ctx: commands.Context):
        """Lista todos os comandos disponíveis"""
        comandos_basicos = [
            "!perfil - Mostra suas informações",
            "!titulo - Título atual da live",
            "!jogo - Jogo/categoria atual",
            "!comandos - Lista de comandos"
        ]

        comandos_mod = [
            "!settitulo <texto> - Altera o título",
            "!setjogo <nome> - Altera o jogo"
        ]

        msg = "📋 Comandos disponíveis: " + " | ".join(comandos_basicos)

        if ctx.author.is_mod or ctx.author.name.lower() == bot._initial_channels[0].lower():
            msg += " | MOD: " + " | ".join(comandos_mod)

        await ctx.send(msg)


    @bot.command(name='uptime')
    async def uptime_command(ctx: commands.Context):
        """Mostra há quanto tempo a live está online"""
        stream = await twitch_api.get_stream(bot._initial_channels[0])

        if not stream:
            await ctx.send("📴 O canal não está ao vivo no momento!")
            return

        started_at = datetime.fromisoformat(stream['started_at'].replace('Z', '+00:00'))
        uptime = datetime.utcnow().replace(tzinfo=started_at.tzinfo) - started_at

        horas = uptime.seconds // 3600
        minutos = (uptime.seconds % 3600) // 60

        await ctx.send(f"🔴 Live online há: {horas}h {minutos}min | Viewers: {stream.get('viewer_count', 0)}")


    logger.info("✅ Comandos built-in registrados!")