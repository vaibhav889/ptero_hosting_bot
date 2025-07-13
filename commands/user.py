from discord.ext import commands
from discord import app_commands, Interaction
from utils.ptero_api import PteroAPI
from utils.database import Database
import discord
import os

ALLOWED_DOMAINS = os.getenv("ALLOWED_DOMAINS", "").split(",")

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = PteroAPI()
        self.db = Database()

    @app_commands.command(name="create-account", description="Create a Pterodactyl panel account")
    async def create_account(self, interaction: Interaction, email: str):
        await interaction.response.defer()
        if ALLOWED_DOMAINS and not any(email.endswith(d.strip()) for d in ALLOWED_DOMAINS):
            return await interaction.followup.send("❌ Email domain is not allowed.")

        existing = self.db.get_user(interaction.user.id)
        if existing:
            return await interaction.followup.send("⚠️ You already have an account linked.")

        username = interaction.user.name.lower()
        first_name = interaction.user.display_name.split(" ")[0]
        last_name = "discord"

        user_data = await self.api.create_user(username, email, first_name, last_name)
        if user_data:
            ptero_id = user_data["attributes"]["id"]
            self.db.add_user(str(interaction.user.id), email, ptero_id)
            await interaction.followup.send(f"✅ Account created for `{email}`. You can now manage servers.")
        else:
            await interaction.followup.send("❌ Failed to create your account. Contact admin.")

    @app_commands.command(name="share-access", description="Share server access with another user")
    async def share_access(self, interaction: Interaction, user: discord.User, server_id: str):
        await interaction.response.defer()
        self.db.share_server(str(interaction.user.id), str(user.id), server_id)
        await interaction.followup.send(f"✅ Shared server `{server_id}` with {user.mention}.")

    @app_commands.command(name="unshare-access", description="Remove access previously shared")
    async def unshare_access(self, interaction: Interaction, user: discord.User, server_id: str):
        await interaction.response.defer()
        self.db.unshare_server(str(interaction.user.id), str(user.id), server_id)
        await interaction.followup.send(f"🚫 Revoked access to `{server_id}` from {user.mention}.")

    @app_commands.command(name="myplan", description="View your hosting plan and server access")
    async def myplan(self, interaction: Interaction):
        await interaction.response.defer()
        user_data = self.db.get_user(str(interaction.user.id))
        if user_data:
            plan = user_data[3]
            shared = self.db.get_shared_servers(str(interaction.user.id))
            msg = f"📦 **Your Plan:** `{plan}`\n🔗 **Shared Servers:** {len(shared)}"
            if shared:
                msg += "\n```" + "\n".join(shared) + "```"
        else:
            msg = "❌ You have not created an account yet. Use `/create-account`."
        await interaction.followup.send(msg)

    def cog_unload(self):
        self.bot.loop.create_task(self.api.close())
        self.db.close()
