import asyncio
import uvicorn
import logging
import threading
from app.core.config import settings

# Configura logging
logging.basicConfig(
    level=logging.INFO if settings.enable_debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_bot():
    """Executa o bot em sua própria thread com seu próprio event loop"""
    # Cria um novo event loop para esta thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        logger.info("🤖 Iniciando bot da Twitch...")

        # Importa e cria o bot AQUI, dentro do loop correto
        from app.bot.bot import TwitchBot
        from app.bot.commands import register_commands

        bot = TwitchBot()

        # Registra os comandos
        register_commands(bot)

        # Inicia o bot
        loop.run_until_complete(bot.start())

    except Exception as e:
        logger.error(f"❌ Erro ao iniciar bot: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()


def run_api():
    """Executa a API FastAPI"""
    try:
        logger.info("🚀 Iniciando API FastAPI...")
        from app.api.main import app

        uvicorn.run(
            app,
            host=settings.api_host,
            port=settings.api_port,
            log_level="info" if settings.enable_debug else "warning"
        )
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar API: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Executa bot e API em paralelo"""
    logger.info("=" * 50)
    logger.info("🎮 Iniciando Twitch Bot Backend")
    logger.info("=" * 50)
    logger.info(f"📺 Canal: {settings.twitch_channel}")
    logger.info(f"⚡ Prefix: {settings.command_prefix}")
    logger.info(f"🌐 API: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"📚 Docs: http://{settings.api_host}:{settings.api_port}/docs")
    logger.info("=" * 50)

    # Inicia o bot em uma thread separada
    bot_thread = threading.Thread(target=run_bot, name="TwitchBot", daemon=True)
    bot_thread.start()

    # Roda a API na thread principal
    run_api()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 50)
        logger.info("👋 Encerrando aplicação...")
        logger.info("=" * 50)
    except Exception as e:
        logger.error(f"💥 Erro fatal: {e}")
        import traceback
        traceback.print_exc()