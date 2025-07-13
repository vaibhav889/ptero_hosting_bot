import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio

from commands.core import Core
from commands.user import UserCommands
from commands.admin import AdminCommands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

async def setup():
    await bot.add_cog(Core(bot))
    await bot.add_cog(UserCommands(bot))
    await bot.add_cog(AdminCommands(bot))

async def main():
    await setup()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
