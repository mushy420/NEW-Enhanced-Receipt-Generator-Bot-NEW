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
    """Dropdown menu for selecting a store."""
    
    def __init__(self, stores: Dict[str, Dict[str, Any]]):
        options = []
        for store_id, store_info in stores.items():
            options.append(discord.SelectOption(
                label=store_info['name'],
                value=store_id,
                description=f"Generate a {store_info['name']} receipt"
            ))
        
        super().__init__(
            placeholder="Select a store",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if hasattr(view, 'on_store_select'):
            await view.on_store_select(interaction, self.values[0])


class ReceiptView(ui.View):
    """View containing store selection dropdown."""
    
    def __init__(self, author_id: int, timeout: int = DROPDOWN_TIMEOUT):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.store_select = StoreSelect(STORES)
        self.add_item(self.store_select)


class FinalReceiptView(ui.View):
    """View with buttons to edit or generate the final receipt."""
    
    def __init__(self, author_id: int, store_id: str, receipt_data: Dict[str, Any], timeout: int = BUTTON_TIMEOUT):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.store_id = store_id
        self.receipt_data = receipt_data
        self.generator = ReceiptGenerator()
    
    @ui.button(label="Edit Product Details", style=discord.ButtonStyle.secondary, row=0)
    async def edit_product_button(self, interaction: discord.Interaction, button: ui.Button):
        """Allow user to edit the product details."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return
        
        # Create the appropriate modal based on store
        if self.store_id == "amazon":
            modal = AmazonDetailsModal()
        elif self.store_id == "apple":
            modal = AppleDetailsModal()
        elif self.store_id == "bestbuy":
            modal = BestBuyDetailsModal()
        elif self.store_id == "walmart":
            modal = WalmartDetailsModal()
        elif self.store_id == "goat":
            modal = GoatDetailsModal()
        elif self.store_id == "stockx":
            modal = StockXDetailsModal()
        elif self.store_id == "louisvuitton":
            modal = LouisVuittonDetailsModal()
        else:
            # Generic modal as fallback
            modal = GenericDetailsModal(self.store_id)
        
        # Set the store ID and prefill with existing data
        modal.store_id = self.store_id
        
        # Filter out customer-specific data
        product_data = {k: v for k, v in self.receipt_data.items() 
                       if k not in ['full_name', 'shipping_address', 'billing_address', 'date']}
        
        modal.prefill_fields(product_data)
        
        await interaction.response.send_modal(modal)
    
    @ui.button(label="Edit Customer Details", style=discord.ButtonStyle.secondary, row=0)
    async def edit_customer_button(self, interaction: discord.Interaction, button: ui.Button):
        """Allow user to edit the customer details."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return
        
        # Create customer details modal
        modal = CustomerDetailsModal(self.store_id)
        
        # Prefill customer data
        customer_data = {k: v for k, v in self.receipt_data.items() 
                        if k in ['full_name', 'shipping_address', 'billing_address', 'date', 'size', 'condition']}
        
        if 'full_name' in customer_data:
            modal.full_name.default = customer_data['full_name']
        
        if 'date' in customer_data:
            modal.date.default = customer_data['date']
        
        if 'shipping_address' in customer_data:
            modal.shipping_address.default = customer_data['shipping_address']
        
        if hasattr(modal, 'billing_address') and 'billing_address' in customer_data:
            modal.billing_address.default = customer_data['billing_address']
        
        if hasattr(modal, 'size') and 'size' in customer_data:
            modal.size.default = customer_data['size']
            
        if hasattr(modal, 'condition') and 'condition' in customer_data:
            modal.condition.default = customer_data['condition']
        
        await interaction.response.send_modal(modal)
    
    @ui.button(label="Generate Receipt", style=discord.ButtonStyle.success, row=1)
    async def generate_button(self, interaction: discord.Interaction, button: ui.Button):
        """Generate the final receipt."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return
        
        # Disable all buttons to prevent multiple submissions
        for child in self.children:
            child.disabled = True
        
        # Update the embed to show processing
        embed = discord.Embed(
            title="Generating Receipt",
            description="🧾 **Generating your receipt...**",
            color=discord.Color(EMBED_COLOR)
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Generate the receipt
        try:
            receipt_bytes = self.generator.generate_receipt(self.store_id, self.receipt_data)
            
            if receipt_bytes:
                # Try to send via DM first
                dm_success = await self.send_receipt_dm(interaction.user, receipt_bytes)
                
                # Update the embed based on DM success
                if dm_success:
                    success_embed = discord.Embed(
                        title="Receipt Generated",
                        description="✅ **Receipt has been sent to your DMs!**",
                        color=discord.Color(SUCCESS_COLOR)
                    )
                    
                    # Add a restart button
                    restart_view = RestartView(interaction.user.id)
                    await interaction.edit_original_response(embed=success_embed, view=restart_view)
                else:
                    # Send in the channel if DMs failed
                    file = discord.File(fp=receipt_bytes, filename=f"{self.store_id}_receipt.png")
                    
                    success_embed = discord.Embed(
                        title="Receipt Generated",
                        description=f"✅ **Receipt generated successfully for {STORES[self.store_id]['name']}!**\n\n❗ **Note:** We couldn't send this to your DMs. Please make sure your DMs are open for future receipts.",
                        color=discord.Color(SUCCESS_COLOR)
                    )
                    
                    # Add a restart button
                    restart_view = RestartView(interaction.user.id)
                    await interaction.edit_original_response(embed=success_embed, file=file, view=restart_view)
            else:
                # Handle generation failure
                error_embed = discord.Embed(
                    title="Generation Failed",
                    description="❌ **Failed to generate receipt. Please try again.**",
                    color=discord.Color(ERROR_COLOR)
                )
                await interaction.edit_original_response(embed=error_embed, view=None)
                
        except Exception as e:
            logger.error(f"Error generating receipt: {e}", exc_info=True)
            error_embed = discord.Embed(
                title="Error",
                description=f"❌ **An error occurred:** {str(e)}",
                color=discord.Color(ERROR_COLOR)
            )
            await interaction.edit_original_response(embed=error_embed, view=None)
    
    async def send_receipt_dm(self, user: discord.User, receipt_bytes: BytesIO) -> bool:
        """Send the receipt to the user's DMs."""
        try:
            file = discord.File(fp=receipt_bytes, filename=f"{self.store_id}_receipt.png")
            
            embed = discord.Embed(
                title=f"{STORES[self.store_id]['name']} Receipt",
                description="Here is your generated receipt:",
                color=discord.Color(STORES[self.store_id]['color'])
            )
            
            await user.send(embed=embed, file=file)
            logger.info(f"Receipt sent to {user.id}'s DMs successfully")
            return True
        except discord.Forbidden:
            logger.warning(f"Cannot send DM to {user.id}, DMs are closed")
            return False
        except Exception as e:
            logger.error(f"Error sending DM to {user.id}: {e}", exc_info=True)
            return False
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user interacting is the author."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
            return False
        return True


class RestartView(ui.View):
    """View with a button to start a new receipt."""
    
    def __init__(self, author_id: int, timeout: int = BUTTON_TIMEOUT):
        super().__init__(timeout=timeout)
        self.author_id = author_id
    
    @ui.button(label="Generate Another Receipt", style=discord.ButtonStyle.primary)
    async def restart_button(self, interaction: discord.Interaction, button: ui.Button):
        """Start a new receipt generation process."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return
        
        # Create a new embed and view for store selection
        embed = discord.Embed(
            title="Receipt Generator",
            description="Please select a store to generate a receipt:",
            color=discord.Color(EMBED_COLOR)
        )
        
        view = ReceiptView(interaction.user.id)
        
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user interacting is the author."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
            return False
        return True


# Store-specific modals with validation
class GenericDetailsModal(BaseDetailsModal):
    """Generic modal for collecting receipt details."""
    
    def __init__(self, store_id: str, timeout: int = MODAL_TIMEOUT):
        store_name = STORES[store_id]['name']
        super().__init__(title=f"{store_name} Receipt Details", timeout=timeout)
        
        self.product_url = ui.TextInput(
            label="Product URL",
            placeholder="https://example.com/product",
            required=False
        )
        self.add_item(self.product_url)
        
        self.product = ui.TextInput(
            label="Product Name",
            placeholder="Product Name",
            required=True
        )
        self.add_item(self.product)
        
        self.price = ui.TextInput(
            label="Price",
            placeholder="99.99",
            required=True
        )
        self.add_item(self.price)
        
        self.currency = ui.TextInput(
            label="Currency",
            placeholder="$",
            default="$",
            required=True
        )
        self.add_item(self.currency)
        
        self.shipping_cost = ui.TextInput(
            label="Shipping Cost",
            placeholder="0.00",
            default="0.00",
            required=True
        )
        self.add_item(self.shipping_cost)
    
    def gather_data(self) -> Dict[str, Any]:
        """Gather data from modal fields."""
        data = super().gather_data()
        data.update({
            'product_url': self.product_url.value.strip(),
            'product': self.product.value.strip(),
            'price': self.price.value.strip(),
            'currency': self.currency.value.strip(),
            'shipping_cost': self.shipping_cost.value.strip()
        })
        return data
    
    def validate_data(self) -> List[str]:
        """Validate the gathered data."""
        errors = super().validate_data()
        
        # Additional validation for shipping cost
        shipping_cost = self.receipt_data.get('shipping_cost', '')
        if not re.match(PRICE_REGEX, shipping_cost):
            errors.append("Shipping cost must be a valid number (e.g., 5.99)")
        
        return errors
    
    def prefill_fields(self, data: Dict[str, Any]):
        """Prefill the modal fields with existing data."""
        if 'product_url' in data and data['product_url']:
            self.product_url.default = data['product_url']
        
        if 'product' in data and data['product']:
            self.product.default = data['product']
        
        if 'price' in data and data['price']:
            self.price.default = data['price']
        
        if 'currency' in data and data['currency']:
            self.currency.default = data['currency']
        
        if 'shipping_cost' in data and data['shipping_cost']:
            self.shipping_cost.default = data['shipping_cost']


# Store-specific modals with proper validation
class AmazonDetailsModal(GenericDetailsModal):
    """Amazon-specific modal for collecting receipt details."""
    
    def __init__(self, timeout: int = MODAL_TIMEOUT):
        super().__init__("amazon", timeout)
        # Override the label for Amazon-specific fields
        self.product_url.label = "Amazon Product URL"
        self.product_url.placeholder = "https://www.amazon.com/product"


class AppleDetailsModal(GenericDetailsModal):
    """Apple-specific modal for collecting receipt details."""
    
    def __init__(self, timeout: int = MODAL_TIMEOUT):
        super().__init__("apple", timeout)
        # Override the label for Apple-specific fields
        self.product_url.label = "Apple Product URL"
        self.product_url.placeholder = "https://www.apple.com/shop/product"
        self.product.placeholder = "iPhone 14 Pro Max 256GB"


class BestBuyDetailsModal(GenericDetailsModal):
    """Best Buy-specific modal for collecting receipt details."""
    
    def __init__(self, timeout: int = MODAL_TIMEOUT):
        super().__init__("bestbuy", timeout)
        # Override the label for Best Buy-specific fields
        self.product_url.label = "Best Buy Product URL"
        self.product_url.placeholder = "https://www.bestbuy.com/site/product"
        self.product.placeholder = "PlayStation 5 Console"


class WalmartDetailsModal(BaseDetailsModal):
    """Walmart-specific modal for collecting receipt details."""
    
    def __init__(self, timeout: int = MODAL_TIMEOUT):
        super().__init__(title="Walmart Receipt Details", timeout=timeout)
        
        self.product_url = ui.TextInput(
            label="Walmart Product URL",
            placeholder="https://www.walmart.com/ip/product",
            required=False
        )
        self.add_item(self.product_url)
        
        self.product = ui.TextInput(
            label="Product Name",
            placeholder="65\" Class 4K Smart TV",
            required=True
        )
        self.add_item(self.product)
        
        self.price = ui.TextInput(
            label="Price",
            placeholder="499.99",
            required=True
        )
        self.add_item(self.price)
        
        self.currency = ui.TextInput(
            label="Currency",
            placeholder="$",
            default="$",
            required=True
        )
        self.add_item(self.currency)
        
        self.quantity = ui.TextInput(
            label="Quantity",
            placeholder="1",
            default="1",
            required=True
        )
        self.add_item(self.quantity)
    
    def gather_data(self) -> Dict[str, Any]:
        """Gather data from modal fields."""
        data = super().gather_data()
        data.update({
            'product_url': self.product_url.value.strip(),
            'product': self.product.value.strip(),
            'price': self.price.value.strip(),
            'currency': self.currency.value.strip(),
            'quantity': self.quantity.value.strip(),
            'shipping_cost': "0.00"  # Walmart often has free shipping or store pickup
        })
        return data
    
    def validate_data(self) -> List[str]:
        """Validate the gathered data."""
        errors = super().validate_data()
        
        # Validate quantity
        quantity = self.receipt_data.get('quantity', '')
        if not quantity.isdigit() or int(quantity) < 1:
            errors.append("Quantity must be a positive whole number")
        
        return errors
    
    def prefill_fields(self, data: Dict[str, Any]):
        """Prefill the modal fields with existing data."""
        if 'product_url' in data and data['product_url']:
            self.product_url.default = data['product_url']
        
        if 'product' in data and data['product']:
            self.product.default = data['product']
        
        if 'price' in data and data['price']:
            self.price.default = data['price']
        
        if 'currency' in data and data['currency']:
            self.currency.default = data['currency']
        
        if 'quantity' in data and data['quantity']:
            self.quantity.default = data['quantity']


class GoatDetailsModal(BaseDetailsModal):
    """GOAT-specific modal for collecting receipt details."""
    
    def __init__(self, timeout: int = MODAL_TIMEOUT):
        super().__init__(title="GOAT Receipt Details", timeout=timeout)
        
        self.product_url = ui.TextInput(
            label="Product URL",
            placeholder="https://www.goat.com/sneakers/product",
            required=False
        )
        self.add_item(self.product_url)
        
        self.image_url = ui.TextInput(
            label="Direct Image URL (optional)",
            placeholder="https://image-hosting.com/shoe.jpg",
            required=False
        )
        self.add_item(self.image_url)
        
        self.product = ui.TextInput(
            label="Product Name",
            placeholder="Air Jordan 1 Retro High OG 'Chicago'",
            required=True
        )
        self.add_item(self.product)
        
        self.price = ui.TextInput(
            label="Price",
            placeholder="299.99",
            required=True
        )
        self.add_item(self.price)
        
        self.currency = ui.TextInput(
            label="Currency",
            placeholder="$",
            default="$",
            required=True
        )
        self.add_item(self.currency)
    
    def gather_data(self) -> Dict[str, Any]:
        """Gather data from modal fields."""
        data = super().gather_data()
        data.update({
            'product_url': self.product_url.value.strip(),
            'image_url': self.image_url.value.strip(),
            'product': self.product.value.strip(),
            'price': self.price.value.strip(),
            'currency': self.currency.value.strip(),
            'shipping_cost': "12.00"  # Default GOAT shipping
        })
        return data
    
    def prefill_fields(self, data: Dict[str, Any]):
        """Prefill the modal fields with existing data."""
        if 'product_url' in data and data['product_url']:
            self.product_url.default = data['product_url']
        
        if 'image_url' in data and data['image_url']:
            self.image_url.default = data['image_url']
        
        if 'product' in data and data['product']:
            self.product.default = data['product']
        
        if 'price' in data and data['price']:
            self.price.default = data['price']
        
        if 'currency' in data and data['currency']:
            self.currency.default = data['currency']


class StockXDetailsModal(BaseDetailsModal):
    """StockX-specific modal for collecting receipt details."""
    
    def __init__(self, timeout: int = MODAL_TIMEOUT):
        super().__init__(title="StockX Receipt Details", timeout=timeout)
        
        self.image_url = ui.TextInput(
            label="Direct Image URL (optional)",
            placeholder="https://image-hosting.com/product.jpg",
            required=False
        )
        self.add_item(self.image_url)
        
        self.product = ui.TextInput(
            label="Product Name",
            placeholder="Nike Dunk Low 'Panda'",
            required=True
        )
        self.add_item(self.product)
        
        self.price = ui.TextInput(
            label="Price",
            placeholder="199.99",
            required=True
        )
        self.add_item(self.price)
        
        self.currency = ui.TextInput(
            label="Currency",
            placeholder="$",
            default="$",
            required=True
        )
        self.add_item(self.currency)
        
        self.fee = ui.TextInput(
            label="Processing Fee",
            placeholder="19.99",
            required=True
        )
        self.add_item(self.fee)
    
    def gather_data(self) -> Dict[str, Any]:
        """Gather data from modal fields."""
        data = super().gather_data()
        data.update({
            'image_url': self.image_url.value.strip(),
            'product': self.product.value.strip(),
            'price': self.price.value.strip(),
            'currency': self.currency.value.strip(),
            'fee': self.fee.value.strip(),
            'shipping_cost': "13.95"  # Default StockX shipping
        })
        return data
    
    def validate_data(self) -> List[str]:
        """Validate the gathered data."""
        errors = super().validate_data()
        
        # Validate fee
        fee = self.receipt_data.get('fee', '')
        if not re.match(PRICE_REGEX, fee):
            errors.append("Processing fee must be a valid number (e.g., 19.99)")
        
        return errors
    
    def prefill_fields(self, data: Dict[str, Any]):
        """Prefill the modal fields with existing data."""
        if 'image_url' in data and data['image_url']:
            self.image_url.default = data['image_url']
        
        if 'product' in data and data['product']:
            self.product.default = data['product']
        
        if 'price' in data and data['price']:
            self.price.default = data['price']
        
        if 'currency' in data and data['currency']:
            self.currency.default = data['currency']
        
        if 'fee' in data and data['fee']:
            self.fee.default = data['fee']


class LouisVuittonDetailsModal(BaseDetailsModal):
    """Louis Vuitton-specific modal for collecting receipt details."""
    
    def __init__(self, timeout: int = MODAL_TIMEOUT):
        super().__init__(title="Louis Vuitton Receipt Details", timeout=timeout)
        
        self.product_url = ui.TextInput(
            label="Product URL",
            placeholder="https://us.louisvuitton.com/product",
            required=False
        )
        self.add_item(self.product_url)
        
        self.product = ui.TextInput(
            label="Product Name",
            placeholder="Neverfull MM Monogram Canvas",
            required=True
        )
        self.add_item(self.product)
        
        self.style_id = ui.TextInput(
            label="Style ID/Reference (optional)",
            placeholder="M40995",
            required=False
        )
        self.add_item(self.style_id)
        
        self.price = ui.TextInput(
            label="Price",
            placeholder="1960.00",
            required=True
        )
        self.add_item(self.price)
        
        self.currency = ui.TextInput(
            label="Currency",
            placeholder="$",
            default="$",
            required=True
        )
        self.add_item(self.currency)
    
    def gather_data(self) -> Dict[str, Any]:
        """Gather data from modal fields."""
        data = super().gather_data()
        data.update({
            'product_url': self.product_url.value.strip(),
            'product': self.product.value.strip(),
            'style_id': self.style_id.value.strip(),
            'price': self.price.value.strip(),
            'currency': self.currency.value.strip(),
            'shipping_cost': "0.00"  # LV typically offers free shipping
        })
        return data
    
    def prefill_fields(self, data: Dict[str, Any]):
        """Prefill the modal fields with existing data."""
        if 'product_url' in data and data['product_url']:
            self.product_url.default = data['product_url']
        
        if 'product' in data and data['product']:
            self.product.default = data['product']
        
        if 'style_id' in data and data['style_id']:
            self.style_id.default = data['style_id']
        
        if 'price' in data and data['price']:
            self.price.default = data['price']
        
        if 'currency' in data and data['currency']:
            self.currency.default = data['currency']


class ReceiptCog(commands.Cog):
    """Cog for handling receipt generation commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.generator = ReceiptGenerator()
        self.logger = logging.getLogger('receipt_cog')
        
        # Improved rate limiting
        self.cooldowns = {}  # Short-term cooldowns
        self.daily_usage = defaultdict(int)  # Daily request counter
        self.daily_reset_time = datetime.now() + timedelta(days=1)  # Time to reset daily counters
        self.user_last_receipt = {}  # Track last receipt time per user
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Log when the cog is loaded."""
        self.logger.info("Receipt Generator cog is ready")
        
        # Start the task to reset daily usage counters
        self.bot.loop.create_task(self.reset_daily_usage_task())
    
    async def reset_daily_usage_task(self):
        """Task to reset daily usage counters every 24 hours."""
        while not self.bot.is_closed():
            now = datetime.now()
            if now >= self.daily_reset_time:
                self.daily_usage.clear()
                self.daily_reset_time = now + timedelta(days=1)
                self.logger.info("Daily usage counters have been reset")
            
            # Check again in 15 minutes
            await asyncio.sleep(900)  # 15 minutes in seconds
    
    def is_on_cooldown(self, user_id: int) -> bool:
        """Check if a user is on cooldown."""
        if user_id not in self.cooldowns:
            return False
        
        cooldown_time = self.cooldowns[user_id]
        current_time = datetime.now()
        
        if (current_time - cooldown_time).total_seconds() < COOLDOWN_SECONDS:
            return True
        
        # Cooldown expired
        del self.cooldowns[user_id]
        return False
    
    def get_remaining_cooldown(self, user_id: int) -> float:
        """Get remaining cooldown time in seconds."""
        if user_id not in self.cooldowns:
            return 0
        
        cooldown_time = self.cooldowns[user_id]
        current_time = datetime.now()
        elapsed = (current_time - cooldown_time).total_seconds()
        
        if elapsed < COOLDOWN_SECONDS:
            return COOLDOWN_SECONDS - elapsed
        
        return 0
    
    def add_cooldown(self, user_id: int):
        """Add a user to cooldown."""
        self.cooldowns[user_id] = datetime.now()
        self.user_last_receipt[user_id] = time.time()
        self.daily_usage[user_id] += 1
    
    def check_daily_limit(self, user_id: int) -> bool:
        """Check if a user has reached their daily limit."""
        return self.daily_usage.get(user_id, 0) >= MAX_REQUESTS_PER_DAY
    
    def get_cooldown_info(self, user_id: int) -> tuple:
        """Get comprehensive cooldown information for a user."""
        is_cooldown = self.is_on_cooldown(user_id)
        remaining_cooldown = self.get_remaining_cooldown(user_id)
        daily_used = self.daily_usage.get(user_id, 0)
        daily_limit_reached = self.check_daily_limit(user_id)
        
        return (is_cooldown, remaining_cooldown, daily_used, daily_limit_reached)
    
    @app_commands.command(name="receipt", description="Generate a receipt for various stores")
    async def receipt(self, interaction: discord.Interaction):
        """Generate a receipt using the dropdown and modal system."""
        # Get comprehensive cooldown information
        is_cooldown, remaining_cooldown, daily_used, daily_limit_reached = self.get_cooldown_info(interaction.user.id)
        
        # Check for daily limit first
        if daily_limit_reached:
            hours_until_reset = (self.daily_reset_time - datetime.now()).total_seconds() / 3600
            embed = discord.Embed(
                title="Daily Limit Reached",
                description=f"⚠️ **You've reached your daily limit of {MAX_REQUESTS_PER_DAY} receipts.**\nPlease try again in {hours_until_reset:.1f} hours when your limit resets.",
                color=discord.Color(WARNING_COLOR)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check for cooldown
        if is_cooldown:
            embed = discord.Embed(
                title="Cooldown",
                description=f"⏱️ **You're on cooldown!** Please wait {remaining_cooldown:.1f} more seconds before generating another receipt.\n\nDaily usage: {daily_used}/{MAX_REQUESTS_PER_DAY} receipts",
                color=discord.Color(ERROR_COLOR)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Add user to cooldown
        self.add_cooldown(interaction.user.id)
        
        embed = discord.Embed(
            title="Receipt Generator",
            description="Please select a store to generate a receipt:",
            color=discord.Color(EMBED_COLOR)
        )
        
        # Add brief instructions
        embed.add_field(
            name="How it works:",
            value="1. Select a store from the dropdown menu\n"
                  "2. Fill in the product details\n"
                  "3. Fill in your personal details\n"
                  "4. Review and submit\n"
                  "5. Receive your receipt in DMs",
            inline=False
        )
        
        # Add usage information
        embed.add_field(
            name="Usage Information:",
            value=f"Daily usage: {daily_used}/{MAX_REQUESTS_PER_DAY} receipts",
            inline=False
        )
        
        view = ReceiptView(interaction.user.id)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        self.logger.info(f"Receipt command used by {interaction.user.id} ({daily_used}/{MAX_REQUESTS_PER_DAY} daily uses)")
    
    @commands.command(name="receipt", hidden=True)
    @commands.cooldown(1, COOLDOWN_SECONDS, commands.BucketType.user)
    async def receipt_legacy(self, ctx, *args):
        """Legacy command for receipt generation, hidden from help."""
        embed = discord.Embed(
            title="Command Deprecated",
            description="⚠️ The prefix command is deprecated. Please use the slash command `/receipt` instead.",
            color=discord.Color(EMBED_COLOR)
        )
        await ctx.send(embed=embed)
        

async def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    await bot.add_cog(ReceiptCog(bot))
