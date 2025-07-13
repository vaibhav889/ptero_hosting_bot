import discord
from discord import app_commands, Interaction
from discord.ext import commands
from utils.ptero_api import PteroAPI

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
            await interaction.followup.send(f"📊 Server Status: `{state}`")
        else:
            await interaction.followup.send("❌ Unable to retrieve status.")

    @app_commands.command(name="cmd", description="Send a command to your server console")
    async def send_cmd(self, interaction: Interaction, server_id: str, command: str):
        await interaction.response.defer()
        result = await self.api.send_command(server_id, command)
        if result:
            await interaction.followup.send(f"📥 Sent command: `{command}`")
        else:
            await interaction.followup.send("❌ Failed to send command.")

    @app_commands.command(name="ping", description="Check if the bot is alive.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms")

    @app_commands.command(name="help", description="Show all available commands.")
    async def help(self, interaction: discord.Interaction):
        pages = [
            discord.Embed(
                title="📘 User Commands - Page 1/2",
                description="Here are the available commands for users:",
                color=discord.Color.blurple()
            ).add_field(
                name="/dashboard", value="View your Pterodactyl account and linked servers", inline=False
            ).add_field(
                name="/create-account", value="Create a Pterodactyl panel account", inline=False
            ).add_field(
                name="/share-access", value="Grant access to your server to another user", inline=False
            ).add_field(
                name="/unshare-access", value="Revoke shared access from another user", inline=False
            ).add_field(
                name="/list-servers", value="List your owned and shared servers", inline=False
            ).add_field(
                name="/server-logs", value="View recent logs of a server", inline=False
            ).add_field(
                name="/change-name", value="Change the name of your server", inline=False
            ).add_field(
                name="/server-resources", value="Check RAM, CPU, and disk usage", inline=False
            ).add_field(
                name="/download-backup", value="List and download backups", inline=False
            ).add_field(
                name="/reset-server", value="Wipe all files on the server", inline=False
            ).add_field(
                name="/start /stop /restart /status", value="Control your server’s power state", inline=False
            ).add_field(
                name="/cmd", value="Send a command to the server console", inline=False
            ).add_field(
                name="/ping", value="Check bot responsiveness", inline=False),

            discord.Embed(
                title="🔧 Admin Commands - Page 2/2",
                description="Admin-only commands:",
                color=discord.Color.dark_red()
            ).add_field(
                name="/create-server", value="Create a server for a user", inline=False
            ).add_field(
                name="/delete-server", value="Permanently delete a server", inline=False
            ).add_field(
                name="/suspend-server", value="Suspend a running server", inline=False
            ).add_field(
                name="/unsuspend-server", value="Unsuspend a server", inline=False
            ).add_field(
                name="/wipe-server", value="Delete all server files", inline=False
            ).add_field(
                name="/update-server-limits", value="Modify RAM, CPU, disk of a server", inline=False
            ).add_field(
                name="/ban-user", value="Prevent a user from using the bot", inline=False
            ).add_field(
                name="/unban-user", value="Unban a previously banned user", inline=False
            ).add_field(
                name="/list-users", value="List all panel-linked users", inline=False
            ).add_field(
                name="/list-shared-access", value="View who has access to a server", inline=False
            ).add_field(
                name="/servers-on-node", value="List all servers hosted on a node", inline=False
            ).add_field(
                name="/nodes", value="View all registered nodes", inline=False
            ).add_field(
                name="/node-status", value="Check usage and status of a node", inline=False)
        ]

        class HelpView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.page = 0

            @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.gray)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.page = (self.page - 1) % len(pages)
                await interaction.response.edit_message(embed=pages[self.page], view=self)

            @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.gray)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.page = (self.page + 1) % len(pages)
                await interaction.response.edit_message(embed=pages[self.page], view=self)

        await interaction.response.send_message(embed=pages[0], view=HelpView(), ephemeral=True)

    def cog_unload(self):
        self.bot.loop.create_task(self.api.close())
