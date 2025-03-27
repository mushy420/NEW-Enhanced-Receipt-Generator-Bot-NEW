import discord
from discord import ui
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

from config import STORES, PRICE_REGEX, DATE_REGEX, MODAL_TIMEOUT
from receipt_generator import ReceiptGenerator

# Setup logging
logger = logging.getLogger('receipt_modals')

class BaseDetailsModal(ui.Modal):
    """Base modal for collecting receipt details."""
    def __init__(self, user_id: int, store_id: str):
        super().__init__(title=f"{STORES[store_id]['name']} Receipt Details")
        self.user_id = user_id
        self.store_id = store_id

    async def on_submit(self, interaction: discord.Interaction):
        """Base submit handler."""
        try:
            # Defer the response to give us time to process
            await interaction.response.defer(ephemeral=True)
            
            # Validate inputs and get receipt details
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
        
        # Customer name
        self.customer_name = ui.TextInput(
            label="Customer Name", 
            placeholder="Enter customer name", 
            required=False, 
            style=discord.TextStyle.short
        )
        self.add_item(self.customer_name)
        
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
            style=discord.TextStyle.short,
            default=datetime.now().strftime("%m/%d/%Y")
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
            'customer_name': self.customer_name.value,
            'product': self.product.value,
            'price': self.price.value,
            'date': self.date.value,
            'shipping_address': self.shipping_address.value,
            'currency': '$'
        }

class AmazonDetailsModal(BaseDetailsModal):
    """Specific modal for Amazon with appropriate fields."""
    def __init__(self, user_id: int, store_id: str):
        super().__init__(user_id, store_id)
        
        # Product URL for image
        self.product_url = ui.TextInput(
            label="Product URL (Optional)",
            placeholder="https://amazon.com/...",
            required=False,
            style=discord.TextStyle.short
        )
        self.add_item(self.product_url)
        
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
        
        # Order number
        self.order_number = ui.TextInput(
            label="Order Number (Optional)", 
            placeholder="Enter order number or leave blank for auto-generate",
            required=False,
            style=discord.TextStyle.short
        )
        self.add_item(self.order_number)
        
        # Shipping address
        self.shipping_address = ui.TextInput(
            label="Shipping Address", 
            placeholder="Enter full shipping address", 
            required=True, 
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.shipping_address)

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate inputs for Amazon receipt modal."""
        # Validate price
        if not re.match(PRICE_REGEX, self.price.value):
            raise ValueError("Invalid price format. Use format like 99.99")
        
        # Generate order number if not provided
        order_number = self.order_number.value
        if not order_number:
            # Generate a random-looking order number
            import random
            order_number = f"{random.randint(100, 999)}-{random.randint(1000000, 9999999)}"
        
        # Current date
        current_date = datetime.now().strftime("%m/%d/%Y")
        
        return {
            'store_name': STORES[self.store_id]['name'],
            'customer_name': interaction.user.display_name,
            'product': self.product.value,
            'price': self.price.value,
            'date': current_date,
            'order_number': order_number,
            'shipping_address': self.shipping_address.value,
            'product_url': self.product_url.value if self.product_url.value else None,
            'currency': '$'
        }

class AppleDetailsModal(BaseDetailsModal):
    """Specific modal for Apple with additional fields."""
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
        
        # Serial number
        self.serial_number = ui.TextInput(
            label="Serial Number", 
            placeholder="Enter product serial number", 
            required=True, 
            style=discord.TextStyle.short
        )
        self.add_item(self.serial_number)
        
        # Date
        self.date = ui.TextInput(
            label="Purchase Date", 
            placeholder="MM/DD/YYYY", 
            required=True, 
            style=discord.TextStyle.short,
            default=datetime.now().strftime("%m/%d/%Y")
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
        """Validate inputs for Apple receipt modal."""
        # Validate price
        if not re.match(PRICE_REGEX, self.price.value):
            raise ValueError("Invalid price format. Use format like 99.99")
        
        # Validate date
        if not re.match(DATE_REGEX, self.date.value):
            raise ValueError("Invalid date format. Use MM/DD/YYYY")
        
        return {
            'store_name': STORES[self.store_id]['name'],
            'customer_name': interaction.user.display_name,
            'product': self.product.value,
            'price': self.price.value,
            'date': self.date.value,
            'serial_number': self.serial_number.value,
            'shipping_address': self.shipping_address.value,
            'currency': '$'
        }
