import discord
from discord import app_commands, ui
from discord.ext import commands
import logging
import asyncio
import re
import time
from io import BytesIO
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Any, Set
from collections import defaultdict

from config import (
    STORES, EMBED_COLOR, ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR,
    BUTTON_TIMEOUT, DROPDOWN_TIMEOUT, MODAL_TIMEOUT, COOLDOWN_SECONDS,
    MAX_REQUESTS_PER_DAY, PRICE_REGEX, URL_REGEX, DATE_REGEX
)
from receipt_generator import ReceiptGenerator

# Setup logging
logger = logging.getLogger('receipt_cog')

class StoreSelect(ui.Select):
    """Dropdown for selecting a store."""
    def __init__(self, user_id: int):
        """Initialize the store selection dropdown."""
        options = [
            discord.SelectOption(
                label=store_info['name'], 
                value=store_id, 
                description=f"Generate a receipt for {store_info['name']}"
            ) for store_id, store_info in STORES.items()
        ]
        
        super().__init__(
            placeholder="Select a store...", 
            min_values=1, 
            max_values=1, 
            options=options
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        """Handle store selection."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ You cannot interact with this dropdown.", 
                ephemeral=True
            )
            return

        selected_store = self.values[0]
        store_info = STORES.get(selected_store)
        
        if not store_info:
            await interaction.response.send_message(
                "❌ Invalid store selected.", 
                ephemeral=True
            )
            return

        # Determine the appropriate modal for the store
        modal_class = self._get_store_modal(selected_store)
        modal = modal_class(user_id=interaction.user.id, store_id=selected_store)
        
        await interaction.response.send_modal(modal)

    def _get_store_modal(self, store_id: str):
        """Get the appropriate modal for the selected store."""
        store_modals = {
            'amazon': AmazonDetailsModal,
            'apple': AppleDetailsModal,
            # Add more store-specific modals as needed
        }
        return store_modals.get(store_id, GenericDetailsModal)

class BaseDetailsModal(ui.Modal):
    """Base modal for collecting receipt details."""
    def __init__(self, user_id: int, store_id: str):
        super().__init__(title=f"{STORES[store_id]['name']} Receipt Details")
        self.user_id = user_id
        self.store_id = store_id

    async def on_submit(self, interaction: discord.Interaction):
        """Base submit handler."""
        try:
            # Validate inputs 
            await interaction.response.defer(ephemeral=True)
            
            # Validate modal inputs
            details = await self._validate_inputs(interaction)
            
            # Generate receipt
            generator = ReceiptGenerator()
            receipt_image = generator.generate_receipt(self.store_id, details)
            
            if not receipt_image:
                await interaction.followup.send(
                    "❌ Failed to generate receipt. Please try again.", 
                    ephemeral=True
                )
                return
            
            # Send receipt image
            await interaction.followup.send(
                content="Here's your receipt!",
                file=discord.File(receipt_image, filename=f"{self.store_id}_receipt.png"),
                ephemeral=True
            )
        
        except Exception as e:
            logger.error(f"Receipt generation error: {str(e)}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}", 
                ephemeral=True
            )

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate modal inputs. To be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement input validation")

class GenericDetailsModal(BaseDetailsModal):
    """Generic modal for stores without specific customization."""
    def __init__(self, user_id: int, store_id: str):
        super().__init__(user_id, store_id)
        
        # Product details
        self.product = ui.TextInput(
            label="Product Name", 
            placeholder="Enter product name", 
            required=True, 
            style=discord.TextStyle.short
        )
        self.add_item(self.product)
        
        # Price
        self.price = ui.TextInput(
            label="Price", 
            placeholder="Enter price (e.g., 99.99)", 
            required=True, 
            style=discord.TextStyle.short
        )
        self.add_item(self.price)
        
        # Date
        self.date = ui.TextInput(
            label="Purchase Date", 
            placeholder="MM/DD/YYYY", 
            required=True, 
            style=discord.TextStyle.short
        )
        self.add_item(self.date)
        
        # Shipping address
        self.shipping_address = ui.TextInput(
            label="Shipping Address", 
            placeholder="Enter full shipping address", 
            required=True, 
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.shipping_address)

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate inputs for generic receipt modal."""
        # Validate price
        if not re.match(PRICE_REGEX, self.price.value):
            raise ValueError("Invalid price format. Use format like 99.99")
        
        # Validate date
        if not re.match(DATE_REGEX, self.date.value):
            raise ValueError("Invalid date format. Use MM/DD/YYYY")
        
        return {
            'store_name': STORES[self.store_id]['name'],
            'product': self.product.value,
            'price': self.price.value,
            'date': self.date.value,
            'shipping_address': self.shipping_address.value,
            'currency': '$'
        }

class AmazonDetailsModal(GenericDetailsModal):
    """Specific modal for Amazon with additional fields."""
    def __init__(self, user_id: int, store_id: str):
        super().__init__(user_id, store_id)
        
        # Add Amazon-specific fields
        self.order_number = ui.TextInput(
            label="Order Number", 
            placeholder="Enter Amazon order number", 
            required=True, 
            style=discord.TextStyle.short
        )
        self.add_item(self.order_number)

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate inputs for Amazon receipt modal."""
        details = await super()._validate_inputs(interaction)
        details['order_number'] = self.order_number.value
        return details

class AppleDetailsModal(GenericDetailsModal):
    """Specific modal for Apple with additional fields."""
    def __init__(self, user_id: int, store_id: str):
        super().__init__(user_id, store_id)
        
        # Add Apple-specific fields
        self.serial_number = ui.TextInput(
            label="Serial Number", 
            placeholder="Enter product serial number", 
            required=True, 
            style=discord.TextStyle.short
        )
        self.add_item(self.serial_number)

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate inputs for Apple receipt modal."""
        details = await super()._validate_inputs(interaction)
        details['serial_number'] = self.serial_number.value
        return details

class ReceiptView(ui.View):
    """View containing the store selection dropdown."""
    def __init__(self, user_id: int):
        super().__init__(timeout=DROPDOWN_TIMEOUT)
        self.add_item(StoreSelect(user_id))

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
        """Log when the cog is loaded."""
        self.logger.info("Receipt Generator cog is ready")
    
    @app_commands.command(name="receipt", description="Generate a receipt for various stores")
    @app_commands.checks.cooldown(1, COOLDOWN_SECONDS)
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
        if self.usage_counts[user_id] >= MAX_REQUESTS_PER_DAY:
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
            description="Please select a store to generate a receipt:",
            color=discord.Color(EMBED_COLOR)
        )
        
        # Create view with store selection dropdown
        view = ReceiptView(interaction.user.id)
        
        # Increment usage count
        self.usage_counts[user_id] += 1
        
        # Send the embed and view
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        self.logger.info(f"Receipt generation started by {user_id}")


async def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    await bot.add_cog(ReceiptCog(bot))
