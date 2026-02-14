import aiohttp
from typing import Optional, Dict, Any, List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class TwitchAPIService:
    """Serviço para interagir com a Twitch API"""

    BASE_URL = "https://api.twitch.tv/helix"

    def __init__(self):
        self.client_id = settings.twitch_client_id
        self.client_secret = settings.twitch_client_secret
        self._app_token: Optional[str] = None

    async def get_app_access_token(self) -> str:
        """Obtém App Access Token via Client Credentials"""
        if self._app_token:
            return self._app_token

        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                data = await response.json()
                self._app_token = data.get("access_token")
                logger.info("✅ App Access Token obtido com sucesso")
                return self._app_token

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None, use_streamer_token: bool = False) -> Dict[str, Any]:
        """Faz requisição à API da Twitch

        Args:
            endpoint: Endpoint da API
            params: Parâmetros da query
            use_streamer_token: True para usar token do streamer (operações admin), False para app token
        """
        if use_streamer_token:
            # Usa token do streamer (para operações que precisam de permissões do dono)
            token = settings.twitch_streamer_token.replace("oauth:", "")
            logger.debug(f"Usando token do streamer para {endpoint}")
        else:
            # Usa app token (para consultas públicas)
            token = await self.get_app_access_token()
            logger.debug(f"Usando app token para {endpoint}")

        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}"
        }

        url = f"{self.BASE_URL}/{endpoint}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Erro na API Twitch ({endpoint}): {response.status} - {text}")
                return await response.json()

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Busca informações de um usuário (usa app token)"""
        data = await self._make_request("users", params={"login": username})
        users = data.get("data", [])
        return users[0] if users else None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca informações de um usuário pelo ID (usa app token)"""
        data = await self._make_request("users", params={"id": user_id})
        users = data.get("data", [])
        return users[0] if users else None

    async def get_channel_info(self, broadcaster_id: str) -> Optional[Dict[str, Any]]:
        """Busca informações do canal (usa app token)"""
        data = await self._make_request("channels", params={"broadcaster_id": broadcaster_id})
        channels = data.get("data", [])
        if channels:
            logger.info(f"Canal encontrado: {channels[0].get('broadcaster_name')}")
        return channels[0] if channels else None

    async def get_stream(self, user_login: str) -> Optional[Dict[str, Any]]:
        """Verifica se o canal está ao vivo (usa app token)"""
        data = await self._make_request("streams", params={"user_login": user_login})
        streams = data.get("data", [])
        return streams[0] if streams else None

    async def get_follower_info(self, broadcaster_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Verifica se um usuário segue o canal (USA TOKEN DO STREAMER)"""
        params = {
            "broadcaster_id": broadcaster_id,
            "user_id": user_id
        }
        data = await self._make_request("channels/followers", params=params, use_streamer_token=True)
        followers = data.get("data", [])
        return followers[0] if followers else None

    async def get_subscriber_info(self, broadcaster_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Verifica se usuário é subscriber (USA TOKEN DO STREAMER)"""
        try:
            params = {
                "broadcaster_id": broadcaster_id,
                "user_id": user_id
            }
            data = await self._make_request("subscriptions", params=params, use_streamer_token=True)
            subs = data.get("data", [])
            return subs[0] if subs else None
        except Exception as e:
            logger.error(f"Erro ao buscar subscription: {e}")
            return None

    async def update_channel_info(self, broadcaster_id: str, **kwargs) -> bool:
        """Atualiza informações do canal (USA TOKEN DO STREAMER)"""
        token = settings.twitch_streamer_token.replace("oauth:", "")

        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.BASE_URL}/channels"
        params = {"broadcaster_id": broadcaster_id}

        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, params=params, json=kwargs) as response:
                if response.status == 204:
                    logger.info(f"✅ Canal atualizado: {kwargs}")
                    return True
                else:
                    text = await response.text()
                    logger.error(f"❌ Erro ao atualizar canal: {response.status} - {text}")
                    return False

    async def search_categories(self, query: str) -> List[Dict[str, Any]]:
        """Busca categorias/jogos pelo nome (usa app token)"""
        data = await self._make_request("search/categories", params={"query": query})
        return data.get("data", [])


twitch_api = TwitchAPIService()