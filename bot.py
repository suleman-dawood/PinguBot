import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
try:
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN environment variable is not set")

    TARGET_USER_ID = int(os.getenv("TARGET_USER_ID"))
    GUILD_ID = int(os.getenv("GUILD_ID"))
    ANNOUNCE_CHANNEL_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID"))
    MOD_ROLE_ID = int(os.getenv("MOD_ROLE_ID"))  # Role ID for moderators
except (ValueError, TypeError) as e:
    print(f"Error in environment variables: {e}")
    exit(1)

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True

# Custom bot class for slash command syncing
class MyBot(commands.Bot):
    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = MyBot(command_prefix="!", intents=intents)

# Global state variables
user_message_count = 0
removed_roles = []
message_limit = 200  # Default message limit

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    reset_roles.start()

@bot.event
async def on_message(message):
    global user_message_count, removed_roles

    if message.author.bot or message.author.id != TARGET_USER_ID:
        return

    user_message_count += 1
    channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)

    if user_message_count == message_limit - 5 and channel:
        await channel.send(f"{message.author.mention} has sent {user_message_count} messages today. Almost at the limit!")

    if user_message_count == message_limit:
        member = message.author
        removed_roles = [role for role in member.roles if role.name != "@everyone"]
        if removed_roles:
            await member.remove_roles(*removed_roles)
            if channel:
                await channel.send(f"{member.mention} has hit {message_limit} messages and had their roles removed.")

    await bot.process_commands(message)

@tasks.loop(time=time(hour=0, minute=0))
async def reset_roles():
    global user_message_count, removed_roles

    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if not guild:
        print("Guild not found during reset_roles task.")
        return

    member = guild.get_member(TARGET_USER_ID)
    channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)

    if member and removed_roles:
        await member.add_roles(*removed_roles)
        if channel:
            await channel.send(f"{member.mention}'s roles have been restored at midnight.")

    user_message_count = 0
    removed_roles = []

@bot.tree.command(name="pstatus", description="Check how many messages the tracked user has sent today")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"<@{TARGET_USER_ID}> has sent {user_message_count} messages today (limit: {message_limit})."
    )

@bot.tree.command(name="preset", description="Reset the message counter manually (mods only)")
async def reset(interaction: discord.Interaction):
    global user_message_count, removed_roles

    mod_role = discord.utils.get(interaction.user.roles, id=MOD_ROLE_ID)
    if not mod_role:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    user_message_count = 0
    removed_roles = []
    await interaction.response.send_message("Message count and removed roles have been reset.")

@bot.tree.command(name="psetlimit", description="Set the daily message limit (mods only)")
@app_commands.describe(limit="New message limit (must be >= 5)")
async def setlimit(interaction: discord.Interaction, limit: int):
    global message_limit

    if limit < 5:
        await interaction.response.send_message("Message limit must be at least 5.", ephemeral=True)
        return

    mod_role = discord.utils.get(interaction.user.roles, id=MOD_ROLE_ID)
    if not mod_role:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    message_limit = limit
    await interaction.response.send_message(f"Message limit has been updated to {message_limit}.")

if __name__ == "__main__":
    try:
        print("Starting PinguBot...")
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error running bot: {e}")
