import discord
from discord.ext import commands
from discord import app_commands, Interaction
from utils.ptero_api import PteroAPI
from utils.database import DB
import os

ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = PteroAPI()
        self.db = DB()

    async def admin_check(self, interaction: Interaction) -> bool:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use this command.", ephemeral=True)
            return False
        return True

    @app_commands.command(name="create-server", description="Create a new server for a user")
    async def create_server(self, interaction: Interaction, user: discord.User, ram: int, disk: int, cpu: int):
        if not await self.admin_check(interaction): return
        await interaction.response.defer()
        panel_user = self.db.get_user(user.id)
        if not panel_user:
            return await interaction.followup.send("❌ That user does not have a panel account.")

        server = await self.api.create_server(panel_user["panel_id"], ram, disk, cpu)
        if server:
            self.db.add_server(server["identifier"], owner_id=user.id)
            await interaction.followup.send(f"✅ Server created: `{server['identifier']}`")
        else:
            await interaction.followup.send("❌ Failed to create server.")

    @app_commands.command(name="delete-server", description="Delete a server")
    async def delete_server(self, interaction: Interaction, server_id: str):
        if not await self.admin_check(interaction): return
        await interaction.response.defer()
        success = await self.api.delete_server(server_id)
        if success:
            self.db.delete_server(server_id)
            await interaction.followup.send("🗑️ Server deleted.")
        else:
            await interaction.followup.send("❌ Failed to delete server.")

    @app_commands.command(name="suspend-server", description="Suspend a server")
    async def suspend_server(self, interaction: Interaction, server_id: str):
        if not await self.admin_check(interaction): return
        await interaction.response.defer()
        success = await self.api.suspend_server(server_id)
        await interaction.followup.send("⏸️ Suspended." if success else "❌ Failed.")

    @app_commands.command(name="unsuspend-server", description="Unsuspend a server")
    async def unsuspend_server(self, interaction: Interaction, server_id: str):
        if not await self.admin_check(interaction): return
        await interaction.response.defer()
        success = await self.api.unsuspend_server(server_id)
        await interaction.followup.send("▶️ Unsuspended." if success else "❌ Failed.")

    @app_commands.command(name="wipe-server", description="Wipe all server files")
    async def wipe_server(self, interaction: Interaction, server_id: str):
        if not await self.admin_check(interaction): return
        await interaction.response.defer()
        success = await self.api.wipe_server(server_id)
        await interaction.followup.send("🧼 Wiped." if success else "❌ Failed.")

    @app_commands.command(name="update-server-limits", description="Update server resource limits")
    async def update_limits(self, interaction: Interaction, server_id: str, ram: int, disk: int, cpu: int):
        if not await self.admin_check(interaction): return
        await interaction.response.defer()
        success = await self.api.update_limits(server_id, ram, disk, cpu)
        await interaction.followup.send("🔧 Updated." if success else "❌ Failed.")

    @app_commands.command(name="ban-user", description="Ban a user from using the bot")
    async def ban_user(self, interaction: Interaction, user: discord.User):
        if not await self.admin_check(interaction): return
        self.db.ban_user(user.id)
        await interaction.response.send_message(f"🚫 Banned {user.mention}", ephemeral=True)

    @app_commands.command(name="unban-user", description="Unban a previously banned user")
    async def unban_user(self, interaction: Interaction, user: discord.User):
        if not await self.admin_check(interaction): return
        self.db.unban_user(user.id)
        await interaction.response.send_message(f"✅ Unbanned {user.mention}", ephemeral=True)

    @app_commands.command(name="list-users", description="List all users linked to the panel")
    async def list_users(self, interaction: Interaction):
        if not await self.admin_check(interaction): return
        users = self.db.list_users()
        if not users:
            return await interaction.response.send_message("❌ No users found.", ephemeral=True)
        msg = "\n".join(f"`{u['discord_id']}` | {u['email']}" for u in users)
        await interaction.response.send_message(f"📋 **Linked Users:**\n{msg}", ephemeral=True)

    @app_commands.command(name="list-shared-access", description="List who has access to a server")
    async def list_shared(self, interaction: Interaction, server_id: str):
        if not await self.admin_check(interaction): return
        users = self.db.get_shared_users(server_id)
        if not users:
            return await interaction.response.send_message("No one has access to this server.", ephemeral=True)
        mentions = [f"<@{uid}>" for uid in users]
        await interaction.response.send_message(f"👥 Shared with: {', '.join(mentions)}", ephemeral=True)

    @app_commands.command(name="servers-on-node", description="List all servers on a given node")
    async def servers_on_node(self, interaction: Interaction, node_id: int):
        if not await self.admin_check(interaction): return
        await interaction.response.defer()
        servers = await self.api.list_servers_on_node(node_id)
        if not servers:
            return await interaction.followup.send("❌ No servers found.")
        await interaction.followup.send("🖥️ Servers:\n" + "\n".join(f"`{s}`" for s in servers))

    @app_commands.command(name="nodes", description="List all nodes")
    async def list_nodes(self, interaction: Interaction):
        if not await self.admin_check(interaction): return
        await interaction.response.defer()
        nodes = await self.api.list_nodes()
        if not nodes:
            return await interaction.followup.send("❌ Could not fetch nodes.")
        embed = discord.Embed(title="📡 Registered Nodes", color=discord.Color.purple())
        for node in nodes:
            embed.add_field(name=node["name"], value=f"ID: `{node['id']}` - {node['fqdn']}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="node-status", description="Show usage stats of a node")
    async def node_status(self, interaction: Interaction, node_id: int):
        if not await self.admin_check(interaction): return
        await interaction.response.defer()
        usage = await self.api.get_node_status(node_id)
        if not usage:
            return await interaction.followup.send("❌ Could not get node stats.")
        embed = discord.Embed(title=f"📊 Node Status (ID: {node_id})", color=discord.Color.teal())
        embed.add_field(name="Disk", value=usage.get("disk", "N/A"), inline=True)
        embed.add_field(name="Memory", value=usage.get("memory", "N/A"), inline=True)
        embed.add_field(name="Servers", value=usage.get("servers", "N/A"), inline=True)
        await interaction.followup.send(embed=embed)
