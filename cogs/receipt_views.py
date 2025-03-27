import discord
from discord import ui
import logging
import re
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
import random
import sys
import importlib

from config import STORES, DROPDOWN_TIMEOUT, MODAL_TIMEOUT, PRICE_REGEX, DATE_REGEX
from receipt_generator import ReceiptGenerator

# Setup logging
logger = logging.getLogger('receipt_views')

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
        try:
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

            # Make sure the module is reloaded to get the latest version
            import cogs.receipt_modals
            importlib.reload(cogs.receipt_modals)
            
            # Dynamically import the modal classes
            if selected_store == 'amazon':
                from cogs.receipt_modals import AmazonBasicInfoModal
                modal = AmazonBasicInfoModal(user_id=interaction.user.id, store_id=selected_store)
            elif selected_store == 'apple':
                from cogs.receipt_modals import AppleBasicInfoModal
                modal = AppleBasicInfoModal(user_id=interaction.user.id, store_id=selected_store)
            else:
                from cogs.receipt_modals import GenericBasicInfoModal
                modal = GenericBasicInfoModal(user_id=interaction.user.id, store_id=selected_store)
            
            await interaction.response.send_modal(modal)
            logger.info(f"Sent modal for store {selected_store} to user {interaction.user.id}")
            
        except Exception as e:
            logger.error(f"Error in store selection callback: {str(e)}", exc_info=True)
            # Use followup since response might already be used
            try:
                await interaction.followup.send(
                    f"❌ An error occurred: {str(e)}", 
                    ephemeral=True
                )
            except:
                # If followup fails, try response if it wasn't used
                try:
                    await interaction.response.send_message(
                        f"❌ An error occurred: {str(e)}", 
                        ephemeral=True
                    )
                except Exception as e2:
                    logger.error(f"Failed to send error message: {str(e2)}", exc_info=True)

    def _get_first_stage_modal(self, store_id: str):
        """
        This method is maintained for backward compatibility but is no longer used.
        We now import the modals directly in the callback.
        """
        pass

class ReceiptView(ui.View):
    """View containing the store selection dropdown."""
    def __init__(self, user_id: int):
        super().__init__(timeout=DROPDOWN_TIMEOUT)
        self.add_item(StoreSelect(user_id))

# Required for Discord.py extension loading
async def setup(bot):
    # This cog doesn't need to be added to the bot directly
    # It's used by the receipt_generator cog
    pass
