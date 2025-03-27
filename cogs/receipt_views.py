import discord
from discord import ui
import logging
import re
from typing import Dict, Any, Optional
from config import STORES, DROPDOWN_TIMEOUT, MODAL_TIMEOUT, PRICE_REGEX, DATE_REGEX
from receipt_generator import ReceiptGenerator
from datetime import datetime

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
        
        try:
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(f"Error showing modal: {str(e)}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred while showing the modal: {str(e)}", 
                ephemeral=True
            )

    def _get_store_modal(self, store_id: str):
        """Get the appropriate modal for the selected store."""
        # Import here to avoid circular imports
        from cogs.receipt_modals import AmazonDetailsModal, AppleDetailsModal, GenericDetailsModal
        
        store_modals = {
            'amazon': AmazonDetailsModal,
            'apple': AppleDetailsModal,
            # Add more store-specific modals as needed
        }
        return store_modals.get(store_id, GenericDetailsModal)

class ReceiptView(ui.View):
    """View containing the store selection dropdown."""
    def __init__(self, user_id: int):
        super().__init__(timeout=DROPDOWN_TIMEOUT)
        self.add_item(StoreSelect(user_id))
