import discord
from discord.ext import commands
from discord import app_commands, Interaction
from utils.ptero_api import PteroAPI
from utils.database import DB

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = PteroAPI()
        self.db = DB()

    @app_commands.command(name="create-account", description="Register a Pterodactyl account with your email and password")
    async def create_account(self, interaction: Interaction, email: str, password: str):
        await interaction.response.defer(thinking=True, ephemeral=True)

        # Optional email domain check
        allowed_domains = os.getenv("ALLOWED_DOMAINS", "")
        if allowed_domains:
            allowed = [d.strip() for d in allowed_domains.split(",")]
            if not any(email.endswith("@" + d) for d in allowed):
                return await interaction.followup.send("❌ That email domain is not allowed.")

        user_exists = self.db.get_user(interaction.user.id)
        if user_exists:
            return await interaction.followup.send("⚠️ You already have a linked account.")

        created = await self.api.create_account(email, password, str(interaction.user))
        if created:
            self.db.add_user(discord_id=interaction.user.id, panel_id=created["id"], email=email)
            await interaction.followup.send("✅ Account created successfully and linked.")
        else:
            await interaction.followup.send("❌ Failed to create account. Try again later.")

    @app_commands.command(name="dashboard", description="View your linked account and servers")
    async def dashboard(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        user = self.db.get_user(interaction.user.id)
        if not user:
            return await interaction.followup.send("❌ You have not created an account yet.")

        owned = self.db.get_owned_servers(interaction.user.id)
        shared = self.db.get_shared_servers(interaction.user.id)

        embed = discord.Embed(
            title="📊 Your Hosting Dashboard",
            color=discord.Color.green()
        )
        embed.add_field(name="📧 Email", value=user['email'], inline=True)
        embed.add_field(name="🆔 Panel User ID", value=str(user['panel_id']), inline=True)
        embed.add_field(name="🧾 Owned Servers", value="\n".join(f"`{s}`" for s in owned) or "None", inline=False)
        embed.add_field(name="🔁 Shared With You", value="\n".join(f"`{s}`" for s in shared) or "None", inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="share-access", description="Grant server access to another Discord user")
    async def share_access(self, interaction: Interaction, user: discord.User, server_id: str):
        await interaction.response.defer(ephemeral=True)
        if not self.db.server_exists(server_id, interaction.user.id):
            return await interaction.followup.send("❌ You do not own that server.")
        self.db.share_server(server_id, user.id)
        await interaction.followup.send(f"✅ Shared server `{server_id}` with {user.mention}")

    @app_commands.command(name="unshare-access", description="Remove server access from a shared user")
    async def unshare_access(self, interaction: Interaction, user: discord.User, server_id: str):
        await interaction.response.defer(ephemeral=True)
        if not self.db.server_exists(server_id, interaction.user.id):
            return await interaction.followup.send("❌ You do not own that server.")
        self.db.unshare_server(server_id, user.id)
        await interaction.followup.send(f"✅ Removed server access for {user.mention}")

    @app_commands.command(name="list-servers", description="List all servers you own or have access to")
    async def list_servers(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        owned = self.db.get_owned_servers(interaction.user.id)
        shared = self.db.get_shared_servers(interaction.user.id)

        embed = discord.Embed(title="📦 Your Servers", color=discord.Color.blue())
        embed.add_field(name="Owned", value="\n".join(f"`{s}`" for s in owned) or "None", inline=False)
        embed.add_field(name="Shared", value="\n".join(f"`{s}`" for s in shared) or "None", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="server-logs", description="Get the recent logs from your server")
    async def server_logs(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        content = await self.api.get_logs(server_id)
        if content:
            await interaction.followup.send(f"🧾 Latest logs:\n```\n{content[-1500:]}\n```")
        else:
            await interaction.followup.send("❌ Could not fetch logs.")

    @app_commands.command(name="change-name", description="Change the name of your server")
    async def change_name(self, interaction: Interaction, server_id: str, new_name: str):
        await interaction.response.defer()
        success = await self.api.rename_server(server_id, new_name)
        if success:
            await interaction.followup.send("✅ Server name updated.")
        else:
            await interaction.followup.send("❌ Failed to rename server.")

    @app_commands.command(name="server-resources", description="Check your server’s current usage")
    async def server_resources(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        data = await self.api.get_server_status(server_id)
        if not data:
            return await interaction.followup.send("❌ Could not fetch status.")
        usage = data["attributes"]["resources"]
        embed = discord.Embed(title="📈 Server Usage", color=discord.Color.blurple())
        embed.add_field(name="RAM", value=f"{usage['memory_bytes']//1024//1024} MB", inline=True)
        embed.add_field(name="Disk", value=f"{usage['disk_bytes']//1024//1024} MB", inline=True)
        embed.add_field(name="CPU", value=f"{usage['cpu_absolute']}%", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="download-backup", description="List and download server backups")
    async def download_backup(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        backups = await self.api.list_backups(server_id)
        if not backups:
            return await interaction.followup.send("❌ No backups found.")
        message = "\n".join([f"🗂️ `{b['name']}` → {b['url']}" for b in backups])
        await interaction.followup.send(f"**Backups:**\n{message}")

    @app_commands.command(name="reset-server", description="Wipe all server files")
    async def reset_server(self, interaction: Interaction, server_id: str):
        await interaction.response.defer()
        success = await self.api.wipe_server(server_id)
        if success:
            await interaction.followup.send("⚠️ Server has been wiped.")
        else:
            await interaction.followup.send("❌ Failed to wipe the server.")
