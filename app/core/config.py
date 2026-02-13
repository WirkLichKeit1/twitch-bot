from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    twitch_bot_username: str
    twitch_bot_token: str
    twitch_channel: str

    twitch_client_id: str
    twitch_client_secret: str

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str

    database_url: str = "sqlite+aiosqlite:///./twitch_bot.db"

    allowed_origins: str = "https://localhost:3000"

    command_prefix: str = "!"
    enable_debug: bool = False

    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()