import discord
from discord import ui
import logging
import re
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
import random
import sys
import importlib
import traceback
import os

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

            # Log the store selection before doing anything else
            logger.info(f"User {interaction.user.id} selected store: {selected_store}")

            try:
                # Check if the receipt_modals.py file exists in the cogs directory
                if not os.path.exists("cogs/receipt_modals.py"):
                    await interaction.response.send_message(
                        "❌ Receipt modals module not found. Please contact the bot administrator.",
                        ephemeral=True
                    )
                    logger.error(f"receipt_modals.py not found in cogs directory")
                    return

                # Make sure the module is properly imported
                try:
                    # This is the critical fix: make sure we have the correct absolute import
                    from cogs.receipt_modals import (
                        AmazonBasicInfoModal, 
                        AppleBasicInfoModal, 
                        GenericBasicInfoModal
                    )
                    
                    # Create the appropriate modal based on store selection
                    if selected_store == 'amazon':
                        modal = AmazonBasicInfoModal(user_id=interaction.user.id, store_id=selected_store)
                        logger.info(f"Created Amazon modal for user {interaction.user.id}")
                    elif selected_store == 'apple':
                        modal = AppleBasicInfoModal(user_id=interaction.user.id, store_id=selected_store)
                        logger.info(f"Created Apple modal for user {interaction.user.id}")
                    else:
                        modal = GenericBasicInfoModal(user_id=interaction.user.id, store_id=selected_store)
                        logger.info(f"Created Generic modal for user {interaction.user.id}")
                    
                    # Log before sending modal
                    logger.info(f"Sending {selected_store} modal to user {interaction.user.id}")
                    
                    # Send the modal
                    await interaction.response.send_modal(modal)
                    
                    # Log after sending modal
                    logger.info(f"Successfully sent modal for store {selected_store} to user {interaction.user.id}")
                
                except ImportError as import_error:
                    error_traceback = ''.join(traceback.format_exception(type(import_error), import_error, import_error.__traceback__))
                    logger.error(f"Import error: {str(import_error)}\n{error_traceback}")
                    
                    await interaction.response.send_message(
                        f"❌ Error importing modal classes: {str(import_error)}", 
                        ephemeral=True
                    )
                    return
                
            except Exception as modal_error:
                # Log detailed error information for modal creation/sending
                error_traceback = ''.join(traceback.format_exception(type(modal_error), modal_error, modal_error.__traceback__))
                logger.error(f"Error creating/sending modal: {str(modal_error)}\n{error_traceback}")
                
                # Try to respond to the interaction if it hasn't been responded to yet
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"❌ Error creating modal: {str(modal_error)}", 
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ Error creating modal: {str(modal_error)}", 
                        ephemeral=True
                    )
            
        except Exception as e:
            # Catch-all for any other errors in the callback
            error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.error(f"Unhandled error in store selection callback: {str(e)}\n{error_traceback}")
            
            # Handle the response based on whether the interaction has been responded to
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"❌ An error occurred: {str(e)}", 
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ An error occurred: {str(e)}", 
                        ephemeral=True
                    )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {str(send_error)}", exc_info=True)

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
