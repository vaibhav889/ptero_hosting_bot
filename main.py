import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from commands import core, user, admin

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

async def setup():
    await bot.add_cog(core.CoreCommands(bot))
    await bot.add_cog(user.UserCommands(bot))
    await bot.add_cog(admin.AdminCommands(bot))

asyncio.run(setup())
bot.run(TOKEN)
