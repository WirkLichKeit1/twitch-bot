import aiohttp
from typing import Optional, Dict, Any
from app.core.config import settings

class TwicthAPIService:
    BASE_URL = "https://api.twitch.tv/helix"

    def __init__(self):
        self.client_id = settings.twitch_client_id
        self.client_secret = settings.twitch_client_secret
        self._access_token: Optional[str] = None

    async def get_access_token(self) -> str:
        if self._access_token:
            return self._access_token

        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                data = await response.json()
                self._access_token = data.get("access_token")
                return self._access_token

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        token = await self.get_access_token()

        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}"
        }

        url = f"{self.BASE_URL}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                return await response.json()
    
    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        data = await self._make_request("users", params={"login": username})
        users = data.get("data", [])
        return users[0] if users else None

    async def get_channel_info(self, broadcaster_id: str) -> Optional[Dict[str, Any]]:
        data = await self._make_request("channel", params={"broadcaster_id": broadcaster_id})
        channels = data.get("data", [])
        return channels[0] if channels else None

    async def get_stream(self, user_login: str) -> Optional[Dict[str, Any]]:
        data = await self._make_request("streams", params={"user_login": user_login})
        streams = data.get("data", [])
        return streams[0] if streams else None

    async def get_followers(self, broadcaster_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        params = {
            "broadcaster_id": broadcaster_id,
            "user_id": user_id
        }
        data = await self._make_request("channels/followers", params=params)
        followers = data.get("data", [])
        return followers[0] if followers else None

    async def update_channel_info(self, broadcaster_id: str, **kwargs) -> bool:
        token = await self.get_access_token()
        
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.BASE_URL}/channels"
        params = {"broadcaster_id": broadcaster_id}
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, params=params, json=kwargs) as response:
                return response.status == 204

twitch_api = TwicthAPIService()