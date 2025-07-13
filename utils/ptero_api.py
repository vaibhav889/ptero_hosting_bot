import aiohttp
import os
import json
from typing import Optional

with open("config.json") as f:
    CONFIG = json.load(f)

PANEL_URL = CONFIG["panel_url"]
API_KEY = CONFIG["api_key"]

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "Application/vnd.pterodactyl.v1+json"
}

class PteroAPI:
    def __init__(self):
        self.session = aiohttp.ClientSession(headers=HEADERS)

    async def close(self):
        await self.session.close()

    async def get_user(self, discord_email: str) -> Optional[dict]:
        async with self.session.get(f"{PANEL_URL}/api/application/users") as resp:
            data = await resp.json()
            for user in data.get("data", []):
                if user["attributes"]["email"] == discord_email:
                    return user["attributes"]
        return None

    async def create_user(self, username: str, email: str, first_name: str, last_name: str) -> Optional[dict]:
        payload = {
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name
        }
        async with self.session.post(f"{PANEL_URL}/api/application/users", json=payload) as resp:
            return await resp.json() if resp.status == 201 else None

    async def get_server(self, server_id: str) -> Optional[dict]:
        async with self.session.get(f"{PANEL_URL}/api/client/servers/{server_id}") as resp:
            return await resp.json() if resp.status == 200 else None

    async def list_user_servers(self, identifier: str) -> list:
        async with self.session.get(f"{PANEL_URL}/api/application/users/{identifier}/servers") as resp:
            data = await resp.json()
            return data.get("data", [])

    async def power_action(self, server_id: str, signal: str):
        async with self.session.post(
            f"{PANEL_URL}/api/client/servers/{server_id}/power",
            json={"signal": signal.lower()}
        ) as resp:
            return resp.status == 204

    async def send_command(self, server_id: str, command: str):
        async with self.session.post(
            f"{PANEL_URL}/api/client/servers/{server_id}/command",
            json={"command": command}
        ) as resp:
            return resp.status == 204

    async def create_backup(self, server_id: str, name: str = "Auto Backup"):
        async with self.session.post(
            f"{PANEL_URL}/api/client/servers/{server_id}/backups",
            json={"name": name, "is_locked": False}
        ) as resp:
            return await resp.json() if resp.status in (200, 201) else None

    async def create_server(self, user_id: int, name: str, egg: int, nest: int, limits: dict, env: dict, location: int):
        payload = {
            "name": name,
            "user": user_id,
            "egg": egg,
            "nest": nest,
            "docker_image": "ghcr.io/pterodactyl/yolks:java_17",
            "startup": "java -Xms128M -Xmx{{SERVER_MEMORY}}M -jar server.jar",
            "limits": limits,
            "feature_limits": {"databases": 1, "backups": 3},
            "environment": env,
            "allocation": {"default": location},
            "deploy": {
                "locations": [location],
                "dedicated_ip": False,
                "port_range": []
            },
            "start_on_completion": True
        }
        async with self.session.post(f"{PANEL_URL}/api/application/servers", json=payload) as resp:
            return await resp.json() if resp.status in (200, 201) else None

    async def delete_server(self, server_id: str):
        async with self.session.delete(f"{PANEL_URL}/api/application/servers/{server_id}") as resp:
            return resp.status == 204

    async def list_all_servers(self):
        async with self.session.get(f"{PANEL_URL}/api/application/servers") as resp:
            return await resp.json() if resp.status == 200 else None

    async def list_node_servers(self, node_id: int):
        async with self.session.get(f"{PANEL_URL}/api/application/nodes/{node_id}/servers") as resp:
            return await resp.json() if resp.status == 200 else None
