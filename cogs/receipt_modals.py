import discord
from discord import ui
import logging
import re
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
import random

from config import STORES, PRICE_REGEX, DATE_REGEX, MODAL_TIMEOUT
from receipt_generator import ReceiptGenerator

# Setup logging
logger = logging.getLogger('receipt_modals')

# First-stage modals for basic information
class BaseBasicInfoModal(ui.Modal):
    """Base first-stage modal for collecting basic receipt information."""
    def __init__(self, user_id: int, store_id: str):
        super().__init__(title=f"Basic {STORES[store_id]['name']} Receipt Info")
        self.user_id = user_id
        self.store_id = store_id
        self.basic_info = {}

    async def on_submit(self, interaction: discord.Interaction):
        """Process the first stage and show the second stage modal."""
        try:
            # Validate basic inputs
            self.basic_info = await self._validate_inputs(interaction)
            
            # Create and show the second stage modal
            second_stage_modal = self._get_second_stage_modal(interaction)
            await interaction.response.send_modal(second_stage_modal)
            
        except Exception as e:
            logger.error(f"Error in first stage modal: {str(e)}", exc_info=True)
            await interaction.response.send_message(
                f"❌ An error occurred: {str(e)}", 
                ephemeral=True
            )

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate modal inputs. To be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement input validation")

    def _get_second_stage_modal(self, interaction: discord.Interaction) -> ui.Modal:
        """Get the appropriate second stage modal based on store ID."""
        second_stage_classes = {
            'amazon': AmazonAdditionalInfoModal,
            'apple': AppleAdditionalInfoModal,
            # Add more store-specific second-stage modals as needed
        }
        
        modal_class = second_stage_classes.get(self.store_id, GenericAdditionalInfoModal)
        return modal_class(user_id=self.user_id, store_id=self.store_id, basic_info=self.basic_info)

# Second-stage modals for additional information
class BaseAdditionalInfoModal(ui.Modal):
    """Base second-stage modal for collecting additional receipt information."""
    def __init__(self, user_id: int, store_id: str, basic_info: Dict[str, Any]):
        super().__init__(title=f"Additional {STORES[store_id]['name']} Details")
        self.user_id = user_id
        self.store_id = store_id
        self.basic_info = basic_info

    async def on_submit(self, interaction: discord.Interaction):
        """Process the combined data and generate the receipt."""
        try:
            # Defer the response to give us time to process
            await interaction.response.defer(ephemeral=True)
            
            # Validate additional inputs and combine with basic info
            additional_info = await self._validate_inputs(interaction)
            combined_data = {**self.basic_info, **additional_info}
            
            # Generate receipt
            generator = ReceiptGenerator()
            receipt_image = generator.generate_receipt(self.store_id, combined_data)
            
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

# Generic store modals
class GenericBasicInfoModal(BaseBasicInfoModal):
    """First-stage modal for generic stores to collect basic information."""
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
            style=discord.TextStyle.short,
            default=datetime.now().strftime("%m/%d/%Y")
        )
        self.add_item(self.date)

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate inputs for generic receipt first-stage modal."""
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
            'currency': '$'
        }

class GenericAdditionalInfoModal(BaseAdditionalInfoModal):
    """Second-stage modal for generic stores to collect additional information."""
    def __init__(self, user_id: int, store_id: str, basic_info: Dict[str, Any]):
        super().__init__(user_id, store_id, basic_info)
        
        # Customer name
        self.customer_name = ui.TextInput(
            label="Customer Name", 
            placeholder="Enter customer name", 
            required=False, 
            style=discord.TextStyle.short
        )
        self.add_item(self.customer_name)
        
        # Shipping address
        self.shipping_address = ui.TextInput(
            label="Shipping Address", 
            placeholder="Enter full shipping address", 
            required=True, 
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.shipping_address)
        
        # Order number
        self.order_number = ui.TextInput(
            label="Order Number (Optional)", 
            placeholder="Enter order number or leave blank for auto-generate",
            required=False,
            style=discord.TextStyle.short
        )
        self.add_item(self.order_number)

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate inputs for generic receipt second-stage modal."""
        # Generate order number if not provided
        order_number = self.order_number.value
        if not order_number:
            import random
            order_number = f"ORD-{random.randint(10000, 99999)}"
            
        return {
            'customer_name': self.customer_name.value if self.customer_name.value else interaction.user.display_name,
            'shipping_address': self.shipping_address.value,
            'order_number': order_number
        }

# Amazon-specific modals
class AmazonBasicInfoModal(BaseBasicInfoModal):
    """First-stage modal for Amazon to collect basic product information."""
    def __init__(self, user_id: int, store_id: str):
        super().__init__(user_id, store_id)
        
        # Product URL (optional)
        self.product_url = ui.TextInput(
            label="Product URL (Optional)",
            placeholder="https://amazon.com/...",
            required=False,
            style=discord.TextStyle.short
        )
        self.add_item(self.product_url)
        
        # Product name
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

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate inputs for Amazon first-stage modal."""
        # Validate price
        if not re.match(PRICE_REGEX, self.price.value):
            raise ValueError("Invalid price format. Use format like 99.99")
        
        # Current date
        current_date = datetime.now().strftime("%m/%d/%Y")
        
        return {
            'store_name': STORES[self.store_id]['name'],
            'product': self.product.value,
            'price': self.price.value,
            'date': current_date,
            'product_url': self.product_url.value if self.product_url.value else None,
            'currency': '$'
        }

class AmazonAdditionalInfoModal(BaseAdditionalInfoModal):
    """Second-stage modal for Amazon to collect shipping and payment details."""
    def __init__(self, user_id: int, store_id: str, basic_info: Dict[str, Any]):
        super().__init__(user_id, store_id, basic_info)
        
        # Shipping address
        self.shipping_address = ui.TextInput(
            label="Shipping Address", 
            placeholder="Enter full shipping address", 
            required=True, 
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.shipping_address)
        
        # Order number
        self.order_number = ui.TextInput(
            label="Order Number (Optional)", 
            placeholder="Leave blank for auto-generate",
            required=False,
            style=discord.TextStyle.short
        )
        self.add_item(self.order_number)
        
        # Payment method
        self.payment_method = ui.TextInput(
            label="Payment Method (Optional)", 
            placeholder="e.g., Visa ending in 1234",
            required=False,
            style=discord.TextStyle.short,
            default="Visa ending in 1234"
        )
        self.add_item(self.payment_method)
        
        # Quantity
        self.quantity = ui.TextInput(
            label="Quantity", 
            placeholder="Enter quantity",
            required=False,
            style=discord.TextStyle.short,
            default="1"
        )
        self.add_item(self.quantity)

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate inputs for Amazon second-stage modal."""
        # Generate order number if not provided
        order_number = self.order_number.value
        if not order_number:
            # Generate a random-looking Amazon order number
            random_chars = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=7))
            order_number = f"113-{random_chars}-{random.randint(1000000, 9999999)}"
        
        # Validate quantity
        quantity = 1
        if self.quantity.value:
            try:
                quantity = int(self.quantity.value)
                if quantity < 1:
                    quantity = 1
            except ValueError:
                quantity = 1
        
        return {
            'customer_name': interaction.user.display_name,
            'shipping_address': self.shipping_address.value,
            'order_number': order_number,
            'payment_method': self.payment_method.value if self.payment_method.value else "Visa ending in 1234",
            'quantity': quantity
        }

# Apple-specific modals
class AppleBasicInfoModal(BaseBasicInfoModal):
    """First-stage modal for Apple to collect basic product information."""
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
            style=discord.TextStyle.short,
            default=datetime.now().strftime("%m/%d/%Y")
        )
        self.add_item(self.date)

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate inputs for Apple first-stage modal."""
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
            'currency': '$'
        }

class AppleAdditionalInfoModal(BaseAdditionalInfoModal):
    """Second-stage modal for Apple to collect additional product details."""
    def __init__(self, user_id: int, store_id: str, basic_info: Dict[str, Any]):
        super().__init__(user_id, store_id, basic_info)
        
        # Serial number
        self.serial_number = ui.TextInput(
            label="Serial Number", 
            placeholder="Enter product serial number", 
            required=True, 
            style=discord.TextStyle.short
        )
        self.add_item(self.serial_number)
        
        # Shipping address
        self.shipping_address = ui.TextInput(
            label="Shipping Address", 
            placeholder="Enter full shipping address", 
            required=True, 
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.shipping_address)
        
        # Payment method
        self.payment_method = ui.TextInput(
            label="Payment Method (Optional)", 
            placeholder="e.g., Apple Pay",
            required=False,
            style=discord.TextStyle.short,
            default="Apple Pay"
        )
        self.add_item(self.payment_method)

    async def _validate_inputs(self, interaction: discord.Interaction) -> Dict[str, Any]:
        """Validate inputs for Apple second-stage modal."""
        return {
            'customer_name': interaction.user.display_name,
            'serial_number': self.serial_number.value,
            'shipping_address': self.shipping_address.value,
            'payment_method': self.payment_method.value if self.payment_method.value else "Apple Pay"
        }

# Required for Discord.py extension loading
async def setup(bot):
    # This cog doesn't need to be added to the bot directly
    # It's used by the receipt_generator cog
    pass
