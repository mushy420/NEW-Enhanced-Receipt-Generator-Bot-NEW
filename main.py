import os
import sys
import discord
import logging
import asyncio
import traceback
import datetime
import time
import aiohttp
from discord.ext import commands
from discord import app_commands
from config import BOT_TOKEN, PREFIX, LOG_LEVEL, LOG_FORMAT, LOG_FILE, ERROR_COLOR

# Setup logging
logger = logging.getLogger('discord')
logger.setLevel(getattr(logging, LOG_LEVEL))

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(filename=LOG_FILE, encoding='utf-8', mode='a')

# Set formatter
formatter = logging.Formatter(LOG_FORMAT)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Create bot instance with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Connection tracking variables
last_disconnect = None
reconnect_attempts = 0
connection_errors = []

# Global error handler for commands
@bot.event
async def on_command_error(ctx, error):
    """Global error handler for all command errors."""
    # ... keep existing code (command error handling)

# Global error handler for app commands
@bot.tree.error
async def on_app_command_error(interaction, error):
    """Global error handler for all application command errors."""
    # ... keep existing code (app command error handling)

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    global reconnect_attempts, last_disconnect
    
    # Reset reconnection tracking on successful connection
    if reconnect_attempts > 0:
        logger.info(f"Successfully reconnected after {reconnect_attempts} attempts")
        reconnect_attempts = 0
        connection_errors.clear()
    
    if last_disconnect:
        downtime = datetime.datetime.now() - last_disconnect
        logger.info(f"Bot was down for {downtime.total_seconds():.2f} seconds")
        last_disconnect = None
    
    await bot.tree.sync()
    logger.info(f"{bot.user.name} is now online!")
    logger.info(f"Synced {len(bot.tree.get_commands())} command(s)")
    
    # Set status
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="for /receipt")
    )
    
    # Log server information
    server_count = len(bot.guilds)
    member_count = sum(guild.member_count for guild in bot.guilds)
    logger.info(f"Bot is active in {server_count} servers with {member_count} total members")

@bot.event
async def on_disconnect():
    """Event fired when the bot disconnects from Discord."""
    global last_disconnect
    last_disconnect = datetime.datetime.now()
    logger.warning(f"Bot disconnected from Discord at {last_disconnect.strftime('%Y-%m-%d %H:%M:%S')}")

@bot.event
async def on_resumed():
    """Event fired when the bot resumes a disconnected session."""
    if last_disconnect:
        downtime = datetime.datetime.now() - last_disconnect
        logger.info(f"Session resumed after {downtime.total_seconds():.2f} seconds of downtime")

@bot.event
async def on_connect():
    """Event fired when the bot connects to Discord."""
    logger.info(f"Connected to Discord (Session ID: {bot.ws.session_id if bot.ws else 'Unknown'})")

# Improved exception catching for unhandled errors
@bot.event
async def on_error(event, *args, **kwargs):
    """Global handler for all events that raise uncaught exceptions."""
    global reconnect_attempts, connection_errors
    
    error_type, error, error_traceback = sys.exc_info()
    formatted_traceback = ''.join(traceback.format_exception(error_type, error, error_traceback))
    
    # Track connection-related errors
    if isinstance(error, (discord.errors.GatewayNotFound, 
                          discord.errors.ConnectionClosed,
                          discord.errors.HTTPException,
                          aiohttp.ClientError,
                          asyncio.TimeoutError)):
        reconnect_attempts += 1
        connection_errors.append(f"{type(error).__name__}: {str(error)}")
        logger.error(f"Connection error #{reconnect_attempts}: {type(error).__name__} - {str(error)}")
        
        # Log more details for certain errors
        if isinstance(error, discord.errors.HTTPException):
            logger.error(f"HTTP Error: Status {error.status}, Code {error.code}, Response: {error.text}")
        elif isinstance(error, discord.errors.ConnectionClosed):
            logger.error(f"WebSocket closed with code {error.code}, reason: {error.reason}")
    
    logger.error(f"Unhandled exception in {event}:\n{formatted_traceback}")
    
    # Try to get the relevant channel to report the error if possible
    channel = None
    if args and isinstance(args[0], discord.Message):
        channel = args[0].channel
    
    if channel:
        try:
            embed = discord.Embed(
                title="Bot Error",
                description="❌ **An unexpected error occurred. The bot developers have been notified.**",
                color=discord.Color(ERROR_COLOR)
            )
            await channel.send(embed=embed)
        except discord.errors.HTTPException:
            pass

# Load cogs
async def load_extensions():
    """Load all extensions from the cogs folder."""
    # ... keep existing code (cog loading)

# Main function to run the bot
async def main():
    async with bot:
        await load_extensions()
        try:
            logger.info("Starting bot...")
            await bot.start(BOT_TOKEN)
        except discord.errors.LoginFailure:
            logger.critical("Invalid token provided. Please check your BOT_TOKEN in the .env file.")
            sys.exit(1)
        except discord.errors.PrivilegedIntentsRequired:
            logger.critical("Bot requires privileged intents. Enable them in the Discord Developer Portal.")
            sys.exit(1)
        except discord.errors.ConnectionClosed as e:
            logger.critical(f"Connection closed with code {e.code}, reason: {e.reason}")
            sys.exit(1)
        except Exception as e:
            error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.critical(f"Failed to start bot:\n{error_traceback}")
            sys.exit(1)

if __name__ == "__main__":
    # Set up asyncio policy for Windows if needed
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Add backoff for reconnection attempts
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            asyncio.run(main())
            break  # If we get here without exception, break the retry loop
        except KeyboardInterrupt:
            logger.info("Bot shutdown via KeyboardInterrupt")
            break
        except (discord.errors.GatewayNotFound, discord.errors.ConnectionClosed, ConnectionError) as e:
            retry_count += 1
            wait_time = min(retry_count * 5, 60)  # Exponential backoff with max 60 seconds
            logger.error(f"Connection error: {str(e)}. Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
            time.sleep(wait_time)
        except Exception as e:
            error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.critical(f"Unhandled exception:\n{error_traceback}")
            sys.exit(1)
    
    if retry_count >= max_retries:
        logger.critical(f"Failed to connect after {max_retries} attempts. Giving up.")
        sys.exit(1)
