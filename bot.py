import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables with error handling
try:
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN environment variable is not set")
        
    TARGET_USER_ID = int(os.getenv("TARGET_USER_ID"))
    GUILD_ID = int(os.getenv("GUILD_ID"))
    ANNOUNCE_CHANNEL_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID"))
except (ValueError, TypeError) as e:
    print(f"Error in environment variables: {e}")
    print("Please make sure all required environment variables are set correctly in .env file")
    exit(1)

# Set up bot intents (permissions)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True

# Initialize bot with command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Global variables to track state
user_message_count = 0
removed_roles = []

@bot.event
async def on_ready():
    """Called when the bot has successfully connected to Discord"""
    print(f"Bot is online as {bot.user}")
    # Start the daily role reset task
    reset_roles.start()

@bot.event
async def on_message(message):
    """Handles message events to track and limit user messages"""
    global user_message_count, removed_roles

    # Ignore messages from bots and users we're not tracking
    if message.author.bot or message.author.id != TARGET_USER_ID:
        return

    user_message_count += 1

    channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)

    # Warning at 195 messages
    if user_message_count == 195 and channel:
        await channel.send(f"{message.author.mention} has sent 195 messages today. Almost at the limit!")

    # Role removal at 200 messages
    if user_message_count == 200:
        member = message.author
        # Store all roles except @everyone
        removed_roles = [role for role in member.roles if role.name != "@everyone"]
        if removed_roles:
            await member.remove_roles(*removed_roles)
            if channel:
                await channel.send(f"{member.mention} has hit 200 messages and had their roles removed.")

    # Process any commands in the message
    await bot.process_commands(message)

@tasks.loop(time=time(hour=0, minute=0))
async def reset_roles():
    """Daily task to reset message count and restore roles at midnight"""
    global user_message_count, removed_roles

    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    member = guild.get_member(TARGET_USER_ID)
    channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)

    if member and removed_roles:
        await member.add_roles(*removed_roles)
        if channel:
            await channel.send(f"{member.mention}'s roles have been restored at midnight.")

    # Reset counters
    user_message_count = 0
    removed_roles = []

# Main execution block
if __name__ == "__main__":
    try:
        print("Starting PinguBot...")
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error running bot: {e}")
