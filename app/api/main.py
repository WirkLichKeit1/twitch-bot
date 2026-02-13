from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.routes import users, commands
import logging

logger = logging.getLogger(__name__)

# Cria a aplicação FastAPI
app = FastAPI(
    title="Twitch Bot API",
    description="API para controle e monitoramento do bot da Twitch",
    version="1.0.0"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rotas
app.include_router(users.router)
app.include_router(commands.router)


@app.on_event("startup")
async def startup_event():
    """Executado quando a API inicia"""
    logger.info("Iniciando API...")
    await init_db()
    logger.info("Banco de dados inicializado!")


@app.on_event("shutdown")
async def shutdown_event():
    """Executado quando a API é desligada"""
    logger.info("Encerrando API...")


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "Twitch Bot API",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy"}