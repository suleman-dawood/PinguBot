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
        await self.tree.sync()

bot = MyBot(command_prefix="!", intents=intents)

# Global state
user_message_count = 0
removed_roles = []

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

    if user_message_count == 195 and channel:
        await channel.send(f"{message.author.mention} has sent 195 messages today. Almost at the limit!")

    if user_message_count == 200:
        member = message.author
        removed_roles = [role for role in member.roles if role.name != "@everyone"]
        if removed_roles:
            await member.remove_roles(*removed_roles)
            if channel:
                await channel.send(f"{member.mention} has hit 200 messages and had their roles removed.")

    await bot.process_commands(message)

@tasks.loop(time=time(hour=0, minute=0))
async def reset_roles():
    global user_message_count, removed_roles

    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    member = guild.get_member(TARGET_USER_ID)
    channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)

    if member and removed_roles:
        await member.add_roles(*removed_roles)
        if channel:
            await channel.send(f"{member.mention}'s roles have been restored at midnight.")

    user_message_count = 0
    removed_roles = []

# /status slash command
@bot.tree.command(name="status", description="Check how many messages you've sent today.")
async def status_command(interaction: discord.Interaction):
    global user_message_count

    if interaction.user.id == TARGET_USER_ID:
        await interaction.response.send_message(
            f"You've sent {user_message_count} messages today.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "You are not the tracked user.", ephemeral=True
        )

# /reset slash command - mod only
@bot.tree.command(name="reset", description="Reset message count and restore roles for the user.")
async def reset_command(interaction: discord.Interaction):
    global user_message_count, removed_roles

    mod_role = discord.utils.get(interaction.user.roles, id=MOD_ROLE_ID)
    if not mod_role:
        await interaction.response.send_message(
            "You don’t have permission to use this command.", ephemeral=True
        )
        return

    guild = interaction.guild
    member = guild.get_member(TARGET_USER_ID)
    channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)

    if member and removed_roles:
        await member.add_roles(*removed_roles)
        await interaction.response.send_message(
            f"{member.mention}'s roles have been manually restored. Message count reset.", ephemeral=False
        )
        if channel:
            await channel.send(
                f"{member.mention}'s roles have been manually restored by a moderator."
            )
    else:
        await interaction.response.send_message(
            "No roles to restore or target user not found.", ephemeral=True
        )

    user_message_count = 0
    removed_roles = []

# Run bot
if __name__ == "__main__":
    try:
        print("Starting PinguBot...")
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error running bot: {e}")
