from discord.ext import commands
from discord import app_commands, Interaction
from utils.ptero_api import PteroAPI
import discord
import json
import asyncio

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = PteroAPI()

    @app_commands.command(name="start", description="Start your Minecraft server")
    async def start_server(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        result = await self.api.send_power_action(server_id, "start")
        if result:
            await interaction.followup.send("🟢 Server starting...")
        else:
            await interaction.followup.send("❌ Failed to start server.")

    @app_commands.command(name="stop", description="Stop your Minecraft server")
    async def stop_server(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        result = await self.api.send_power_action(server_id, "stop")
        if result:
            await interaction.followup.send("🔴 Server stopping...")
        else:
            await interaction.followup.send("❌ Failed to stop server.")

    @app_commands.command(name="restart", description="Restart your Minecraft server")
    async def restart_server(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        result = await self.api.send_power_action(server_id, "restart")
        if result:
            await interaction.followup.send("🔁 Server restarting...")
        else:
            await interaction.followup.send("❌ Failed to restart server.")

    @app_commands.command(name="status", description="Check server status")
    async def status(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        status = await self.api.get_server_status(server_id)
        if status:
            state = status["attributes"]["current_state"]
            players = status["attributes"].get("resources", {}).get("current_state", "N/A")
            await interaction.followup.send(f"📊 Server Status: `{state}`")
        else:
            await interaction.followup.send("❌ Unable to retrieve status.")

    @app_commands.command(name="ip", description="Show server IP and port")
    async def ip(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        data = await self.api.get_server_info(server_id)
        if not data:
            return await interaction.followup.send("❌ Could not fetch server info.")

        allocations = data["attributes"]["relationships"]["allocations"]["data"]
        main_alloc = next((a for a in allocations if a["attributes"]["is_default"]), allocations[0])
        ip = main_alloc["attributes"]["ip"]
        port = main_alloc["attributes"]["port"]
        await interaction.followup.send(f"🌐 Server IP: `{ip}:{port}`")

    @app_commands.command(name="cmd", description="Send a command to your server console")
    async def send_cmd(self, interaction: Interaction, server_id: str, command: str):
        await interaction.response.defer()
        result = await self.api.send_command(server_id, command)
        if result:
            await interaction.followup.send(f"📥 Sent command: `{command}`")
        else:
            await interaction.followup.send("❌ Failed to send command.")

    @app_commands.command(name="backup", description="Create a backup of your server")
    async def backup(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        result = await self.api.create_backup(server_id)
        if result:
            name = result["attributes"]["name"]
            await interaction.followup.send(f"🗂️ Backup created: `{name}`")
        else:
            await interaction.followup.send("❌ Failed to create backup.")

    def cog_unload(self):
        self.bot.loop.create_task(self.api.close())

