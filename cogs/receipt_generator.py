import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict
from collections import defaultdict

# Update import to use relative path
from ..config import (
    EMBED_COLOR, ERROR_COLOR, COOLDOWN_SECONDS, MAX_REQUESTS_PER_DAY
)
from .receipt_views import ReceiptView

# Setup logging
logger = logging.getLogger('receipt_cog')

class ReceiptCog(commands.Cog):
    """Cog for receipt generator commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger('receipt_cog')
        self.cooldowns = defaultdict(int)
        self.usage_counts = defaultdict(int)
        self.last_reset = datetime.now()
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Log when the cog is loaded and ensure commands are registered."""
        self.logger.info("Receipt Generator cog is ready")
    
    @app_commands.command(name="receipt", description="Generate a realistic receipt for various stores")
    async def receipt(self, interaction: discord.Interaction):
        """Start the receipt generation process."""
        # Check if user has hit the daily limit
        user_id = interaction.user.id
        current_time = datetime.now()
        
        # Reset counters if it's a new day
        if current_time.date() > self.last_reset.date():
            self.usage_counts.clear()
            self.last_reset = current_time
        
        # Check if user has reached the daily limit
        if self.usage_counts.get(user_id, 0) >= MAX_REQUESTS_PER_DAY:
            embed = discord.Embed(
                title="Daily Limit Reached",
                description=f"❌ You've reached the limit of {MAX_REQUESTS_PER_DAY} receipts per day. Please try again tomorrow.",
                color=discord.Color(ERROR_COLOR)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create embed for store selection
        embed = discord.Embed(
            title="Receipt Generator",
            description="Please select a store to generate a receipt. You'll be guided through two steps to complete your receipt.",
            color=discord.Color(EMBED_COLOR)
        )
        
        # Add more details to the embed
        embed.add_field(
            name="Step 1",
            value="Select basic product information (name, price, etc.)",
            inline=False
        )
        
        embed.add_field(
            name="Step 2",
            value="Add shipping details and other information",
            inline=False
        )
        
        # Create view with store selection dropdown
        view = ReceiptView(interaction.user.id)
        
        # Increment usage count
        self.usage_counts[user_id] = self.usage_counts.get(user_id, 0) + 1
        
        # Send the embed and view
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        self.logger.info(f"Receipt generation started by {user_id}")

async def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    try:
        # First check that required modules exist
        try:
            import utils.validators
            logger.info("utils.validators module found")
        except ImportError as e:
            logger.error(f"utils.validators module not found during setup: {e}")
            
        await bot.add_cog(ReceiptCog(bot))
        logger.info("Receipt Generator cog added successfully")
    except Exception as e:
        logger.error(f"Failed to add ReceiptCog: {e}", exc_info=True)
        raise
