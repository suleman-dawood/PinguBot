# PinguBot

A Discord bot that tracks message count for a specific user and temporarily removes their roles if they exceed a daily message limit.

## Features

- Tracks messages from a specific user
- Warns the user when they're approaching the daily limit (195 messages)
- Removes user roles when they hit the limit (200 messages)
- Automatically restores roles at midnight
- Posts notifications in a designated announcement channel

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following variables:
   ```
   DISCORD_TOKEN=your_bot_token_here
   TARGET_USER_ID=123456789012345678
   GUILD_ID=123456789012345678
   ANNOUNCE_CHANNEL_ID=123456789012345678
   ```
   Replace the placeholder values with your actual Discord bot token and IDs.

4. Run the bot:
   ```
   python bot.py
   ```

## Requirements

- Python 3.8 or higher
- discord.py
- python-dotenv

## License

MIT
