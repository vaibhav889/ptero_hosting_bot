from discord.ext import commands
from discord import app_commands, Interaction
from utils.ptero_api import PteroAPI
from utils.database import Database
import discord
import os
import json

ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i.strip()]

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = PteroAPI()
        self.db = Database()

    def is_admin(self, user_id):
        return int(user_id) in ADMIN_IDS

    @app_commands.command(name="create-server", description="Admin: Create a server for a user")
    async def create_server(self, interaction: Interaction, user: discord.User, name: str, ram: int, disk: int):
        await interaction.response.defer()
        if not self.is_admin(interaction.user.id):
            return await interaction.followup.send("⛔ You are not authorized.")

        user_data = self.db.get_user(str(user.id))
        if not user_data:
            return await interaction.followup.send("❌ That user has not created a panel account yet.")

        ptero_user_id = user_data[2]
        limits = {"memory": ram, "disk": disk, "cpu": 100}
        env = {"SERVER_JARFILE": "server.jar", "VERSION": "latest", "TYPE": "vanilla"}

        server = await self.api.create_server(ptero_user_id, name, egg=1, nest=1, limits=limits, env=env, location=1)
        if server:
            uuid = server['attributes']['uuid']
            await interaction.followup.send(f"✅ Server `{name}` created! UUID: `{uuid}`")
        else:
            await interaction.followup.send("❌ Failed to create server.")

    @app_commands.command(name="delete-server", description="Admin: Delete a server by ID")
    async def delete_server(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        if not self.is_admin(interaction.user.id):
            return await interaction.followup.send("⛔ You are not authorized.")

        success = await self.api.delete_server(server_id)
        if success:
            await interaction.followup.send(f"🗑️ Server `{server_id}` deleted.")
        else:
            await interaction.followup.send("❌ Failed to delete server.")

    @app_commands.command(name="servers-on-node", description="Admin: List all servers on a node")
    async def servers_on_node(self, interaction: Interaction, node_id: int):
        await interaction.response.defer()
        if not self.is_admin(interaction.user.id):
            return await interaction.followup.send("⛔ You are not authorized.")

        servers = await self.api.list_node_servers(node_id)
        if servers:
            names = [s['attributes']['name'] for s in servers.get("data", [])]
            msg = f"🧩 **{len(names)} Servers on Node {node_id}:**\n```" + "\n".join(names) + "```"
        else:
            msg = "❌ Could not retrieve server list for this node."
        await interaction.followup.send(msg)

    @app_commands.command(name="nodes", description="Admin: View all node info and status")
    async def nodes(self, interaction: Interaction):
        await interaction.response.defer()
        if not self.is_admin(interaction.user.id):
            return await interaction.followup.send("⛔ You are not authorized.")

        async with self.api.session.get(f"{self.api.PANEL_URL}/api/application/nodes") as resp:
            data = await resp.json()
            if resp.status != 200:
                return await interaction.followup.send("❌ Failed to fetch nodes.")

            nodes = data.get("data", [])
            embed = discord.Embed(title="📡 Node Status", color=discord.Color.blurple())
            for node in nodes:
                n = node['attributes']
                embed.add_field(
                    name=n['name'],
                    value=f"Location: `{n['location_id']}`\nRAM: {n['memory']}MB\nDisk: {n['disk']}MB\nAllocations: {n['allocations']}",
                    inline=False
                )
            await interaction.followup.send(embed=embed)

    def cog_unload(self):
        self.bot.loop.create_task(self.api.close())
        self.db.close()
