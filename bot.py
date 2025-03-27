import asyncio
import sys
import logging
import time
import traceback
import os
from typing import List, Dict, Any
import datetime
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands

from core.config import BOT_TOKEN, PREFIX, LOG_LEVEL, LOG_FORMAT, LOG_FILE, ERROR_COLOR

def setup_bot() -> commands.Bot:
    """Set up and configure the bot instance."""
    # Create bot intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    # Create bot instance
    bot = commands.Bot(
        command_prefix=PREFIX, 
        intents=intents, 
        help_command=None
    )
    
    # Set up global error handlers
    @bot.event
    async def on_command_error(ctx, error):
        """Global error handler for all command errors."""
        error_message = None
        
        if isinstance(error, commands.CommandOnCooldown):
            error_message = f"⏱️ **Command on cooldown!** Try again in {error.retry_after:.1f}s"
        elif isinstance(error, commands.MissingRequiredArgument):
            error_message = f"❌ **Missing required argument!** Please check the command usage."
        elif isinstance(error, commands.BadArgument):
            error_message = f"❌ **Invalid argument!** Please check the command usage."
        elif isinstance(error, commands.MissingPermissions):
            error_message = f"❌ **You don't have permission to use this command!**"
        elif isinstance(error, commands.BotMissingPermissions):
            error_message = f"❌ **Bot doesn't have required permissions!**"
        elif isinstance(error, commands.CommandNotFound):
            # Don't respond to unknown commands
            return
        else:
            # Log unexpected errors with detailed traceback
            error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            logger.error(f"Unexpected error: {str(error)}\n{error_traceback}")
            error_message = f"❌ **An error occurred:** {str(error)}"
        
        if error_message:
            embed = discord.Embed(
                title="Error",
                description=error_message,
                color=discord.Color.red()
            )
            try:
                await ctx.send(embed=embed, ephemeral=True)
            except discord.errors.HTTPException:
                # Fallback if the message can't be sent normally
                logger.error(f"Failed to send error message for error: {error}")

    # Global error handler for app commands
    @bot.tree.error
    async def on_app_command_error(interaction, error):
        """Global error handler for all application command errors."""
        error_message = None
        
        if isinstance(error, app_commands.CommandOnCooldown):
            error_message = f"⏱️ **Command on cooldown!** Try again in {error.retry_after:.1f}s"
        elif isinstance(error, app_commands.MissingPermissions):
            error_message = f"❌ **You don't have permission to use this command!**"
        elif isinstance(error, app_commands.BotMissingPermissions):
            error_message = f"❌ **Bot doesn't have required permissions!**"
        else:
            # Log unexpected errors with detailed traceback
            error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            logger.error(f"Unexpected app command error: {str(error)}\n{error_traceback}")
            error_message = f"❌ **An error occurred:** {str(error)}"
        
        if error_message:
            embed = discord.Embed(
                title="Error",
                description=error_message,
                color=discord.Color(ERROR_COLOR)
            )
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
            except discord.errors.HTTPException as e:
                # Interaction might have expired or other HTTP error
                logger.error(f"Failed to send error message for interaction error: {error}. HTTP error: {e}")
    
    return bot

# Set up directory structure
def setup_directories():
    """Create required directories if they don't exist."""
    directories = [
        'assets',
        'assets/fonts',
        'assets/templates',
        'data'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

async def load_extensions(bot: commands.Bot) -> List[str]:
    """Load all extensions from the cogs directory."""
    loaded_extensions = []
    
    # Add main cogs directories
    cog_directories = [
        "./cogs",
    ]
    
    for directory in cog_directories:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            if filename.endswith(".py") and not filename.startswith("_"):
                extension = f"{directory[2:]}.{filename[:-3]}"  # Remove './' and '.py'
                try:
                    await bot.load_extension(extension)
                    loaded_extensions.append(extension)
                    logger.info(f"Loaded extension: {extension}")
                except Exception as e:
                    error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                    logger.error(f"Failed to load extension {extension}:\n{error_traceback}")
    
    return loaded_extensions

async def main():
    """Main function to run the bot."""
    setup_directories()
    
    bot = setup_bot()
    
    @bot.event
    async def on_ready():
        """Called when the bot is ready."""
        # Explicitly sync commands on startup
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
        
        logger.info(f"{bot.user.name} is now online!")
        
        # Set status
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="for /receipt")
        )
        
        # Log server information
        server_count = len(bot.guilds)
        member_count = sum(guild.member_count for guild in bot.guilds)
        logger.info(f"Bot is active in {server_count} servers with {member_count} total members")
    
# Load cogs
async def load_extensions():
    """Load all extensions from the cogs folder."""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                logger.error(f"Failed to load extension {extension}:\n{error_traceback}")

# Main function to run the bot
async def main():
    """Main function to run the bot."""
    async with bot:
        # Make sure the utils directory exists with validators.py
        try:
            from utils import validators
            logger.info("utils.validators module found")
        except ImportError:
            logger.warning("utils.validators module not found, creating...")
            # The file will be created when we run the script
        
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
