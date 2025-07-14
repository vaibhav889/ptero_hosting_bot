import aiohttp
import os
import json

PANEL_URL = os.getenv("PANEL_URL")
CLIENT_API_KEY = os.getenv("CLIENT_API_KEY")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {CLIENT_API_KEY}"
}

ADMIN_HEADERS = HEADERS.copy()
ADMIN_HEADERS["Authorization"] = f"Bearer {ADMIN_API_KEY}"

class PteroAPI:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def create_account(self, email, password, username):
        payload = {
            "username": username,
            "email": email,
            "first_name": "User",
            "last_name": "Bot",
            "password": password
        }
        async with self.session.post(f"{PANEL_URL}/api/application/users", headers=ADMIN_HEADERS, json=payload) as r:
            if r.status == 201:
                return await r.json()
            return None

    async def send_power_action(self, server_id, signal):
        async with self.session.post(f"{PANEL_URL}/api/client/servers/{server_id}/power", headers=HEADERS, json={"signal": signal}) as r:
            return r.status == 204

    async def get_server_status(self, server_id):
        async with self.session.get(f"{PANEL_URL}/api/client/servers/{server_id}/resources", headers=HEADERS) as r:
            if r.status == 200:
                return await r.json()
            return None

    async def get_server_info(self, server_id):
        async with self.session.get(f"{PANEL_URL}/api/client/servers/{server_id}", headers=HEADERS) as r:
            return await r.json() if r.status == 200 else None

    async def send_command(self, server_id, command):
        async with self.session.post(f"{PANEL_URL}/api/client/servers/{server_id}/command", headers=HEADERS, json={"command": command}) as r:
            return r.status == 204

    async def get_logs(self, server_id):
        async with self.session.get(f"{PANEL_URL}/api/client/servers/{server_id}/logs", headers=HEADERS) as r:
            if r.status == 200:
                data = await r.json()
                return data.get("data", "")
            return None

    async def rename_server(self, server_id, name):
        async with self.session.patch(f"{PANEL_URL}/api/application/servers/{server_id}/details", headers=ADMIN_HEADERS,
                                      json={"name": name, "external_id": None}) as r:
            return r.status == 200

    async def wipe_server(self, server_id):
        async with self.session.post(f"{PANEL_URL}/api/client/servers/{server_id}/files/delete", headers=HEADERS,
                                     json={"root": "/", "files": ["*"]}) as r:
            return r.status == 204

    async def create_backup(self, server_id):
        async with self.session.post(f"{PANEL_URL}/api/client/servers/{server_id}/backups", headers=HEADERS) as r:
            return await r.json() if r.status == 201 else None

    async def list_backups(self, server_id):
        async with self.session.get(f"{PANEL_URL}/api/client/servers/{server_id}/backups", headers=HEADERS) as r:
            if r.status == 200:
                data = await r.json()
                return [{"name": b["attributes"]["name"], "url": b["attributes"]["uuid"]} for b in data["data"]]
            return None

    async def create_server(self, user_id, ram, disk, cpu):
        payload = {
            "name": "NewServer",
            "user": user_id,
            "egg": 1,
            "docker_image": "ghcr.io/pterodactyl/yolks:java_17",
            "startup": "java -Xms128M -Xmx{{SERVER_MEMORY}}M -jar server.jar nogui",
            "limits": {"memory": ram, "swap": 0, "disk": disk, "io": 500, "cpu": cpu},
            "environment": {
                "DL_PATH": "https://server.jar.url",
                "SERVER_JARFILE": "server.jar",
                "BUILD_NUMBER": "latest"
            },
            "feature_limits": {"databases": 1, "backups": 2, "allocations": 1},
            "allocation": {"default": 1},
            "deploy": {"locations": [1], "dedicated_ip": False, "port_range": []},
            "start_on_completion": True
        }
        async with self.session.post(f"{PANEL_URL}/api/application/servers", headers=ADMIN_HEADERS, json=payload) as r:
            return await r.json() if r.status in [200, 201] else None

    async def delete_server(self, server_id):
        async with self.session.delete(f"{PANEL_URL}/api/application/servers/{server_id}/force", headers=ADMIN_HEADERS) as r:
            return r.status == 204

    async def suspend_server(self, server_id):
        async with self.session.post(f"{PANEL_URL}/api/application/servers/{server_id}/suspend", headers=ADMIN_HEADERS) as r:
            return r.status == 204

    async def unsuspend_server(self, server_id):
        async with self.session.post(f"{PANEL_URL}/api/application/servers/{server_id}/unsuspend", headers=ADMIN_HEADERS) as r:
            return r.status == 204

    async def update_limits(self, server_id, ram, disk, cpu):
        payload = {
            "limits": {"memory": ram, "swap": 0, "disk": disk, "io": 500, "cpu": cpu}
        }
        async with self.session.patch(f"{PANEL_URL}/api/application/servers/{server_id}/build", headers=ADMIN_HEADERS, json=payload) as r:
            return r.status == 200

    async def list_servers_on_node(self, node_id: int):
        async with self.session.get(f"{PANEL_URL}/api/application/servers", headers=ADMIN_HEADERS) as r:
            if r.status != 200:
                return []
            data = await r.json()
            servers = [s["attributes"]["identifier"] for s in data["data"] if s["attributes"]["node"] == node_id]
            return servers

    async def list_nodes(self):
        async with self.session.get(f"{PANEL_URL}/api/application/nodes", headers=ADMIN_HEADERS) as r:
            if r.status != 200:
                return []
            data = await r.json()
            return [n["attributes"] for n in data["data"]]

    async def get_node_status(self, node_id: int):
        async with self.session.get(f"{PANEL_URL}/api/application/nodes/{node_id}", headers=ADMIN_HEADERS) as r:
            if r.status != 200:
                return None
            node = await r.json()
            return {
                "disk": f"{node['attributes']['disk_used']} / {node['attributes']['disk']}",
                "memory": f"{node['attributes']['memory_used']} / {node['attributes']['memory']}",
                "servers": node['attributes']['servers_count']
            }

    async def close(self):
        await self.session.close()
