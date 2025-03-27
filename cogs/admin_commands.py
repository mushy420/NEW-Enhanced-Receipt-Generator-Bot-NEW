import discord
from discord import app_commands
from discord.ext import commands
import logging
import os
import sys
from typing import List, Optional

# Update import to use relative path
from ..config import ADMIN_ROLE_ID, EMBED_COLOR, ERROR_COLOR

# Setup logging
logger = logging.getLogger('admin_commands')

async def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    await bot.add_cog(AdminCog(bot))
    logger.info("Admin Commands cog added successfully")
