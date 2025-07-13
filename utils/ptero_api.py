import aiohttp
import os

class PteroAPI:
    def __init__(self):
        self.PANEL_URL = os.getenv("PANEL_URL")
        self.API_KEY = os.getenv("API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def send_power_action(self, server_id, signal):
        url = f"{self.PANEL_URL}/api/client/servers/{server_id}/power"
        try:
            async with self.session.post(url, json={"signal": signal}) as resp:
                return resp.status == 204
        except Exception:
            return False

    async def send_command(self, server_id, command):
        url = f"{self.PANEL_URL}/api/client/servers/{server_id}/command"
        try:
            async with self.session.post(url, json={"command": command}) as resp:
                return resp.status == 204
        except Exception:
            return False

    async def get_server_status(self, server_id):
        url = f"{self.PANEL_URL}/api/client/servers/{server_id}/resources"
        try:
            async with self.session.get(url) as resp:
                return await resp.json() if resp.status == 200 else None
        except Exception:
            return None

    async def get_server_info(self, server_id):
        url = f"{self.PANEL_URL}/api/client/servers/{server_id}?include=allocations"
        try:
            async with self.session.get(url) as resp:
                return await resp.json() if resp.status == 200 else None
        except Exception:
            return None

    async def create_backup(self, server_id):
        url = f"{self.PANEL_URL}/api/client/servers/{server_id}/backups"
        try:
            async with self.session.post(url) as resp:
                return await resp.json() if resp.status == 201 else None
        except Exception:
            return None

    async def create_user(self, username, email, first, last):
        url = f"{self.PANEL_URL}/api/application/users"
        payload = {
            "username": username,
            "email": email,
            "first_name": first,
            "last_name": last
        }
        try:
            async with self.session.post(url, json=payload) as resp:
                return await resp.json() if resp.status == 201 else None
        except Exception:
            return None

    async def create_server(self, user_id, name, egg, nest, limits, env, location):
        url = f"{self.PANEL_URL}/api/application/servers"
        payload = {
            "name": name,
            "user": user_id,
            "egg": egg,
            "nest": nest,
            "docker_image": "ghcr.io/pterodactyl/yolks:java_17",
            "startup": "java -Xms128M -Xmx{{SERVER_MEMORY}}M -jar server.jar",
            "limits": limits,
            "environment": env,
            "feature_limits": {"databases": 0, "allocations": 1},
            "allocation": {"default": 1},
            "deploy": {
                "locations": [location],
                "dedicated_ip": False,
                "port_range": []
            }
        }
        try:
            async with self.session.post(url, json=payload) as resp:
                return await resp.json() if resp.status == 201 else None
        except Exception:
            return None

    async def delete_server(self, server_id):
        url = f"{self.PANEL_URL}/api/application/servers/{server_id}/force"
        try:
            async with self.session.delete(url) as resp:
                return resp.status == 204
        except Exception:
            return False

    async def list_node_servers(self, node_id):
        url = f"{self.PANEL_URL}/api/application/nodes/{node_id}/servers"
        try:
            async with self.session.get(url) as resp:
                return await resp.json() if resp.status == 200 else None
        except Exception:
            return None

    async def close(self):
        await self.session.close()
