import asyncio
import uvicorn
import logging
import threading
from app.core.config import settings
from app.api.main import app

# Configura logging
logging.basicConfig(
    level=logging.INFO if settings.enable_debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_bot_in_thread():
    """Executa o bot em seu próprio event loop em uma thread separada"""
    # Importa o bot DENTRO da thread para criar no loop correto
    from app.bot.bot import bot

    try:
        logger.info("Iniciando bot da Twitch...")
        # Cria um novo event loop para esta thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Roda o bot neste loop
        loop.run_until_complete(bot.start())
    except Exception as e:
        logger.error(f"Erro ao iniciar bot: {e}")
        import traceback
        traceback.print_exc()


async def run_api():
    """Executa a API FastAPI"""
    try:
        logger.info("Iniciando API FastAPI...")
        config = uvicorn.Config(
            app,
            host=settings.api_host,
            port=settings.api_port,
            log_level="info" if settings.enable_debug else "warning"
        )
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        logger.error(f"Erro ao iniciar API: {e}")


async def main():
    """Executa bot e API simultaneamente"""
    logger.info("=== Iniciando Twitch Bot Backend ===")
    logger.info(f"Canal: {settings.twitch_channel}")
    logger.info(f"Prefix: {settings.command_prefix}")
    logger.info(f"API: http://{settings.api_host}:{settings.api_port}")

    # Inicia o bot em uma thread separada
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()

    # Roda a API no loop principal
    await run_api()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n=== Encerrando aplicação ===")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")