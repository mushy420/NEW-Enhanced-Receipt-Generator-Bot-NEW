import os
import logging
import random
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
from config import FONT_PATH, FONT_SIZE, STORES

# Set up logging
logger = logging.getLogger('receipt_generator')

class ReceiptGenerator:
    """A class to generate realistic-looking receipts for various stores."""
    
    def __init__(self):
        """Initialize the receipt generator with necessary fonts and templates."""
        self.logger = logging.getLogger('receipt_generator')
        self.font_path = FONT_PATH
        self.font_size = FONT_SIZE
        
        # Ensure template directory exists
        os.makedirs("templates", exist_ok=True)
        
        # Ensure fonts directory exists
        os.makedirs("fonts", exist_ok=True)
        
        # Try to load the font, use default if not available
        try:
            self.font = ImageFont.truetype(self.font_path, self.font_size)
            self.bold_font = ImageFont.truetype(self.font_path, self.font_size + 2)
            self.small_font = ImageFont.truetype(self.font_path, self.font_size - 4)
        except (OSError, IOError) as e:
            self.logger.warning(f"Could not load font {self.font_path}: {e}. Using default font.")
            # Use default font
            self.font = ImageFont.load_default()
            self.bold_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()
    
    def download_image(self, url):
        """Download an image from a URL and return it as a PIL Image."""
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            self.logger.error(f"Error downloading image from {url}: {e}")
            return None
    
    def generate_receipt(self, store, data):
        """Generate a receipt for the specified store with the provided data."""
        self.logger.info(f"Generating receipt for {store} with data: {data}")
        
        if store.lower() not in STORES:
            self.logger.error(f"Store {store} not found in configured stores")
            return None
        
        store_info = STORES[store.lower()]
        
        try:
            # Try to open the template
            template_path = store_info["template_path"]
            if not os.path.exists(template_path):
                # Create a blank template if it doesn't exist
                self.logger.warning(f"Template {template_path} not found, creating blank template")
                img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
            else:
                img = Image.open(template_path)
            
            # Create draw object
            draw = ImageDraw.Draw(img)
            
            # Call store-specific receipt generation method
            method_name = f"_generate_{store.lower()}_receipt"
            if hasattr(self, method_name):
                img = getattr(self, method_name)(img, draw, data)
            else:
                self.logger.warning(f"No specific method for {store}, using generic template")
                img = self._generate_generic_receipt(img, draw, store_info, data)
            
            # Save the receipt to a BytesIO object
            output = BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            return output
            
        except Exception as e:
            self.logger.error(f"Error generating receipt: {e}", exc_info=True)
            return None
    
    def _generate_generic_receipt(self, img, draw, store_info, data):
        """Generate a generic receipt template for any store."""
        # Add store logo if available
        if "logo_url" in store_info:
            try:
                logo = self.download_image(store_info["logo_url"])
                if logo:
                    # Resize logo if needed
                    logo = logo.resize((200, 100), Image.LANCZOS)
                    img.paste(logo, (300, 50), logo if logo.mode == 'RGBA' else None)
            except Exception as e:
                self.logger.error(f"Error adding logo: {e}")
        
        # Add store name
        draw.text((400, 170), store_info["name"], fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        
        # Add receipt header
        draw.text((400, 200), "PURCHASE RECEIPT", fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        
        # Add order date and number
        date = data.get("date", datetime.now().strftime("%m/%d/%Y"))
        order_id = str(uuid.uuid4())[:8].upper()
        draw.text((100, 250), f"Date: {date}", fill=(0, 0, 0), font=self.font)
        draw.text((500, 250), f"Order #: {order_id}", fill=(0, 0, 0), font=self.font)
        
        # Add customer info
        name = data.get("full_name", "John Doe")
        draw.text((100, 300), f"Customer: {name}", fill=(0, 0, 0), font=self.font)
        
        # Add shipping and billing address if available
        if "shipping_address" in data:
            address_lines = data["shipping_address"].split('\n')
            draw.text((100, 330), "Shipping Address:", fill=(0, 0, 0), font=self.font)
            for i, line in enumerate(address_lines):
                draw.text((120, 360 + i*25), line, fill=(0, 0, 0), font=self.small_font)
        
        if "billing_address" in data:
            address_lines = data["billing_address"].split('\n')
            draw.text((400, 330), "Billing Address:", fill=(0, 0, 0), font=self.font)
            for i, line in enumerate(address_lines):
                draw.text((420, 360 + i*25), line, fill=(0, 0, 0), font=self.small_font)
        
        # Add horizontal line
        draw.line([(100, 480), (700, 480)], fill=(0, 0, 0), width=2)
        
        # Add product info
        draw.text((100, 500), "Product", fill=(0, 0, 0), font=self.bold_font)
        draw.text((500, 500), "Price", fill=(0, 0, 0), font=self.bold_font)
        draw.text((600, 500), "Qty", fill=(0, 0, 0), font=self.bold_font)
        draw.text((680, 500), "Total", fill=(0, 0, 0), font=self.bold_font)
        
        # Add horizontal line
        draw.line([(100, 530), (700, 530)], fill=(0, 0, 0), width=1)
        
        # Add product details
        product = data.get("product", "Unknown Product")
        price = data.get("price", "0.00")
        quantity = data.get("quantity", 1)
        
        # Calculate total
        try:
            price_val = float(price)
            total = price_val * int(quantity)
        except (ValueError, TypeError):
            total = 0.0
        
        draw.text((100, 550), product[:40], fill=(0, 0, 0), font=self.font)
        if len(product) > 40:
            draw.text((100, 575), product[40:80], fill=(0, 0, 0), font=self.small_font)
        
        currency = data.get("currency", "$")
        draw.text((500, 550), f"{currency}{price}", fill=(0, 0, 0), font=self.font)
        draw.text((600, 550), str(quantity), fill=(0, 0, 0), font=self.font)
        draw.text((680, 550), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal line
        draw.line([(100, 600), (700, 600)], fill=(0, 0, 0), width=1)
        
        # Add subtotal, tax, shipping, and total
        shipping_cost = data.get("shipping_cost", "0.00")
        try:
            shipping_val = float(shipping_cost)
        except (ValueError, TypeError):
            shipping_val = 0.0
        
        tax_rate = 0.0825  # Example tax rate (8.25%)
        tax = total * tax_rate
        grand_total = total + tax + shipping_val
        
        draw.text((500, 630), "Subtotal:", fill=(0, 0, 0), font=self.font)
        draw.text((680, 630), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        draw.text((500, 660), f"Tax ({tax_rate*100:.2f}%):", fill=(0, 0, 0), font=self.font)
        draw.text((680, 660), f"{currency}{tax:.2f}", fill=(0, 0, 0), font=self.font)
        
        draw.text((500, 690), "Shipping:", fill=(0, 0, 0), font=self.font)
        draw.text((680, 690), f"{currency}{shipping_val:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal line
        draw.line([(500, 720), (700, 720)], fill=(0, 0, 0), width=1)
        
        # Add grand total
        draw.text((500, 750), "TOTAL:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((680, 750), f"{currency}{grand_total:.2f}", fill=(0, 0, 0), font=self.bold_font)
        
        # Add payment info
        payment_method = data.get("payment", "Visa")
        draw.text((100, 750), f"Payment Method: {payment_method}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal line
        draw.line([(100, 800), (700, 800)], fill=(0, 0, 0), width=2)
        
        # Add thank you message
        draw.text((400, 850), "Thank you for your purchase!", fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        
        # Add store website or contact
        website = f"www.{store_info['name'].lower().replace(' ', '')}.com"
        draw.text((400, 880), website, fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        return img
    
    def _generate_amazon_receipt(self, img, draw, data):
        """Generate an Amazon-specific receipt."""
        # Create a new white image for Amazon receipt
        img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Add Amazon logo
        try:
            logo = self.download_image(STORES["amazon"]["logo_url"])
            if logo:
                logo = logo.resize((150, 75), Image.LANCZOS)
                img.paste(logo, (50, 50), logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            self.logger.error(f"Error adding Amazon logo: {e}")
        
        # Add order information
        draw.text((50, 150), "ORDER INFORMATION", fill=(0, 0, 0), font=self.bold_font)
        
        # Generate random order number and date if not provided
        order_num = f"D01-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}"
        order_date = data.get("date", datetime.now().strftime("%B %d, %Y"))
        
        draw.text((50, 185), f"Order #: {order_num}", fill=(0, 0, 0), font=self.font)
        draw.text((50, 215), f"Order Date: {order_date}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(50, 250), (750, 250)], fill=(200, 200, 200), width=2)
        
        # Add shipping address
        draw.text((50, 280), "SHIPPING ADDRESS:", fill=(0, 0, 0), font=self.bold_font)
        
        name = data.get("full_name", "John Doe")
        draw.text((50, 310), name, fill=(0, 0, 0), font=self.font)
        
        if "shipping_address" in data:
            address_lines = data["shipping_address"].split('\n')
            for i, line in enumerate(address_lines):
                draw.text((50, 340 + i*30), line, fill=(0, 0, 0), font=self.font)
        
        # Add payment information
        draw.text((400, 280), "PAYMENT INFORMATION:", fill=(0, 0, 0), font=self.bold_font)
        
        payment_method = data.get("payment", "Visa")
        last_4 = random.randint(1000, 9999)
        draw.text((400, 310), f"Payment Method: {payment_method} ending in {last_4}", fill=(0, 0, 0), font=self.font)
        
        if "billing_address" in data:
            draw.text((400, 340), "Billing Address:", fill=(0, 0, 0), font=self.font)
            address_lines = data["billing_address"].split('\n')
            for i, line in enumerate(address_lines):
                draw.text((400, 370 + i*30), line, fill=(0, 0, 0), font=self.small_font)
        
        # Add horizontal separator
        draw.line([(50, 480), (750, 480)], fill=(200, 200, 200), width=2)
        
        # Add order details header
        draw.text((50, 510), "ORDER DETAILS", fill=(0, 0, 0), font=self.bold_font)
        
        # Add table headers
        draw.text((50, 550), "Item", fill=(0, 0, 0), font=self.bold_font)
        draw.text((500, 550), "Price", fill=(0, 0, 0), font=self.bold_font)
        draw.text((600, 550), "Qty", fill=(0, 0, 0), font=self.bold_font)
        draw.text((700, 550), "Total", fill=(0, 0, 0), font=self.bold_font)
        
        # Add horizontal separator
        draw.line([(50, 580), (750, 580)], fill=(200, 200, 200), width=1)
        
        # Add product details
        product = data.get("product", "Unknown Product")
        price = data.get("price", "0.00")
        quantity = data.get("quantity", 1)
        
        # Format product name to wrap if too long
        if len(product) > 40:
            product_line1 = product[:40]
            product_line2 = product[40:80]
            draw.text((50, 610), product_line1, fill=(0, 0, 0), font=self.font)
            draw.text((50, 640), product_line2, fill=(0, 0, 0), font=self.small_font)
        else:
            draw.text((50, 610), product, fill=(0, 0, 0), font=self.font)
        
        # Calculate total
        try:
            price_val = float(price)
            total = price_val * int(quantity)
        except (ValueError, TypeError):
            price_val = 0.0
            total = 0.0
        
        currency = data.get("currency", "$")
        draw.text((500, 610), f"{currency}{price_val:.2f}", fill=(0, 0, 0), font=self.font)
        draw.text((600, 610), str(quantity), fill=(0, 0, 0), font=self.font)
        draw.text((700, 610), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(50, 670), (750, 670)], fill=(200, 200, 200), width=1)
        
        # Add order summary
        draw.text((500, 700), "Item(s) Subtotal:", fill=(0, 0, 0), font=self.font)
        draw.text((700, 700), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add shipping cost
        shipping_cost = data.get("shipping_cost", "0.00")
        try:
            shipping_val = float(shipping_cost)
        except (ValueError, TypeError):
            shipping_val = 0.0
        
        draw.text((500, 730), "Shipping & Handling:", fill=(0, 0, 0), font=self.font)
        draw.text((700, 730), f"{currency}{shipping_val:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add tax
        tax_rate = 0.0825  # Example tax rate (8.25%)
        tax = total * tax_rate
        
        draw.text((500, 760), f"Estimated Tax:", fill=(0, 0, 0), font=self.font)
        draw.text((700, 760), f"{currency}{tax:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(500, 790), (750, 790)], fill=(0, 0, 0), width=2)
        
        # Add grand total
        grand_total = total + shipping_val + tax
        
        draw.text((500, 820), "Grand Total:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((700, 820), f"{currency}{grand_total:.2f}", fill=(0, 0, 0), font=self.bold_font)
        
        # Add footer
        draw.text((400, 900), "Thank you for shopping with Amazon!", fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        draw.text((400, 930), "www.amazon.com", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        return img
    
    def _generate_apple_receipt(self, img, draw, data):
        """Generate an Apple-specific receipt."""
        # Create a new white image for Apple receipt
        img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Add Apple logo
        try:
            logo = self.download_image(STORES["apple"]["logo_url"])
            if logo:
                logo = logo.resize((50, 50), Image.LANCZOS)
                img.paste(logo, (375, 50), logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            self.logger.error(f"Error adding Apple logo: {e}")
        
        # Add receipt title
        draw.text((400, 120), "Apple Store Receipt", fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        
        # Add date and order number
        order_date = data.get("date", datetime.now().strftime("%d-%b-%Y"))
        order_num = f"W{random.randint(1000000000, 9999999999)}"
        
        draw.text((400, 150), f"Date: {order_date}", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        draw.text((400, 180), f"Order ID: {order_num}", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        # Add horizontal separator
        draw.line([(100, 220), (700, 220)], fill=(200, 200, 200), width=1)
        
        # Add customer information
        draw.text((100, 250), "SOLD TO:", fill=(0, 0, 0), font=self.bold_font)
        
        name = data.get("full_name", "John Doe")
        draw.text((100, 280), name, fill=(0, 0, 0), font=self.font)
        
        # Add billing address
        if "billing_address" in data:
            address_lines = data["billing_address"].split('\n')
            for i, line in enumerate(address_lines):
                draw.text((100, 310 + i*30), line, fill=(0, 0, 0), font=self.font)
        
        # Add shipping information
        draw.text((450, 250), "SHIP TO:", fill=(0, 0, 0), font=self.bold_font)
        
        if "shipping_address" in data:
            address_lines = data["shipping_address"].split('\n')
            for i, line in enumerate(address_lines):
                draw.text((450, 310 + i*30), line, fill=(0, 0, 0), font=self.font)
        else:
            draw.text((450, 310), name, fill=(0, 0, 0), font=self.font)
            if "billing_address" in data:
                address_lines = data["billing_address"].split('\n')
                for i, line in enumerate(address_lines):
                    draw.text((450, 340 + i*30), line, fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(100, 450), (700, 450)], fill=(200, 200, 200), width=1)
        
        # Add item details headers
        draw.text((100, 480), "ITEM", fill=(0, 0, 0), font=self.bold_font)
        draw.text((500, 480), "PRICE", fill=(0, 0, 0), font=self.bold_font)
        draw.text((600, 480), "QTY", fill=(0, 0, 0), font=self.bold_font)
        draw.text((700, 480), "AMOUNT", fill=(0, 0, 0), font=self.bold_font)
        
        # Add horizontal separator
        draw.line([(100, 510), (700, 510)], fill=(200, 200, 200), width=1)
        
        # Add product details
        product = data.get("product", "Unknown Product")
        price = data.get("price", "0.00")
        quantity = data.get("quantity", 1)
        
        # Format product name to wrap if too long
        if len(product) > 35:
            product_line1 = product[:35]
            product_line2 = product[35:70]
            draw.text((100, 540), product_line1, fill=(0, 0, 0), font=self.font)
            draw.text((100, 570), product_line2, fill=(0, 0, 0), font=self.small_font)
        else:
            draw.text((100, 540), product, fill=(0, 0, 0), font=self.font)
        
        # Calculate total
        try:
            price_val = float(price)
            total = price_val * int(quantity)
        except (ValueError, TypeError):
            price_val = 0.0
            total = 0.0
        
        currency = data.get("currency", "$")
        draw.text((500, 540), f"{currency}{price_val:.2f}", fill=(0, 0, 0), font=self.font)
        draw.text((600, 540), str(quantity), fill=(0, 0, 0), font=self.font)
        draw.text((700, 540), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(100, 600), (700, 600)], fill=(200, 200, 200), width=1)
        
        # Add summary
        draw.text((500, 630), "Subtotal:", fill=(0, 0, 0), font=self.font)
        draw.text((700, 630), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add tax
        tax_rate = 0.095  # Example tax rate (9.5% - typical for Apple products)
        tax = total * tax_rate
        
        draw.text((500, 660), f"Tax ({tax_rate*100:.1f}%):", fill=(0, 0, 0), font=self.font)
        draw.text((700, 660), f"{currency}{tax:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add shipping
        shipping_cost = data.get("shipping_cost", "0.00")
        try:
            shipping_val = float(shipping_cost)
        except (ValueError, TypeError):
            shipping_val = 0.0
        
        draw.text((500, 690), "Shipping:", fill=(0, 0, 0), font=self.font)
        draw.text((700, 690), f"{currency}{shipping_val:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(500, 720), (700, 720)], fill=(0, 0, 0), width=2)
        
        # Add total
        grand_total = total + tax + shipping_val
        
        draw.text((500, 750), "TOTAL:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((700, 750), f"{currency}{grand_total:.2f}", fill=(0, 0, 0), font=self.bold_font)
        
        # Add payment information
        payment_method = data.get("payment", "Visa")
        last_4 = random.randint(1000, 9999)
        
        draw.text((100, 700), "PAYMENT INFORMATION", fill=(0, 0, 0), font=self.bold_font)
        draw.text((100, 730), f"{payment_method} ending in {last_4}", fill=(0, 0, 0), font=self.font)
        draw.text((100, 760), f"Amount: {currency}{grand_total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add footer
        draw.text((400, 850), "Thank you for shopping at Apple", fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        draw.text((400, 880), "apple.com", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        draw.text((400, 910), "1-800-MY-APPLE", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        return img
    
    def _generate_stockx_receipt(self, img, draw, data):
        """Generate a StockX-specific receipt."""
        # Create a new white image with StockX branding
        img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Add StockX logo
        try:
            logo = self.download_image(STORES["stockx"]["logo_url"])
            if logo:
                logo = logo.resize((200, 80), Image.LANCZOS)
                img.paste(logo, (300, 50), logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            self.logger.error(f"Error adding StockX logo: {e}")
        
        # Add green header bar
        draw.rectangle([(0, 150), (800, 200)], fill=(0, 185, 0))
        draw.text((400, 175), "ORDER CONFIRMATION", fill=(255, 255, 255), font=self.bold_font, anchor="mm")
        
        # Add order information
        order_date = data.get("date", datetime.now().strftime("%m/%d/%Y"))
        order_num = f"{random.randint(10000000, 99999999)}"
        
        draw.text((100, 230), "ORDER DATE:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((300, 230), order_date, fill=(0, 0, 0), font=self.font)
        
        draw.text((500, 230), "ORDER #:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((650, 230), order_num, fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(100, 270), (700, 270)], fill=(200, 200, 200), width=2)
        
        # Add product image placeholder (StockX receipts often have the product image)
        draw.rectangle([(150, 300), (350, 450)], outline=(200, 200, 200))
        
        # Try to add product image if URL is provided
        if "image_url" in data and data["image_url"]:
            try:
                product_img = self.download_image(data["image_url"])
                if product_img:
                    product_img = product_img.resize((200, 150), Image.LANCZOS)
                    img.paste(product_img, (150, 300), product_img if product_img.mode == 'RGBA' else None)
            except Exception as e:
                self.logger.error(f"Error adding product image: {e}")
                draw.text((250, 375), "Product Image", fill=(150, 150, 150), font=self.font, anchor="mm")
        else:
            draw.text((250, 375), "Product Image", fill=(150, 150, 150), font=self.font, anchor="mm")
        
        # Add product details
        product = data.get("product", "Unknown Product")
        price = data.get("price", "0.00")
        
        # Try to get style ID or generate one
        style_id = data.get("style_id", f"SK-{random.randint(10000000, 99999999)}")
        
        # Get size information
        size = data.get("size", "")
        size_display = f"Size: {size}" if size else ""
        
        # Show product information
        draw.text((400, 320), product, fill=(0, 0, 0), font=self.bold_font)
        if len(product) > 30:  # If product name is too long, use smaller font for style ID
            draw.text((400, 350), f"Style: {style_id}", fill=(100, 100, 100), font=self.small_font)
            draw.text((400, 380), size_display, fill=(0, 0, 0), font=self.font)
        else:
            draw.text((400, 350), f"Style: {style_id}", fill=(100, 100, 100), font=self.font)
            draw.text((400, 380), size_display, fill=(0, 0, 0), font=self.font)
        
        # Add condition
        condition = data.get("condition", "New")
        draw.text((400, 410), f"Condition: {condition}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(100, 480), (700, 480)], fill=(200, 200, 200), width=2)
        
        # Add price breakdown
        draw.text((100, 510), "PRICE SUMMARY", fill=(0, 0, 0), font=self.bold_font)
        
        # Calculate values
        try:
            price_val = float(price)
        except (ValueError, TypeError):
            price_val = 0.0
        
        # Get fees
        fee_amount = data.get("fee", "0.00")
        try:
            fee_val = float(fee_amount)
        except (ValueError, TypeError):
            fee_val = price_val * 0.095  # Default StockX fee (9.5%)
        
        # Get shipping
        shipping_cost = data.get("shipping_cost", "0.00")
        try:
            shipping_val = float(shipping_cost)
        except (ValueError, TypeError):
            shipping_val = 13.95  # Default StockX shipping
        
        # Calculate tax (varies by state, using 7% as example)
        tax_rate = 0.07
        tax = (price_val + fee_val) * tax_rate
        
        # Calculate total
        total = price_val + fee_val + shipping_val + tax
        
        currency = data.get("currency", "$")
        
        # Display price breakdown
        draw.text((100, 550), "Purchase Price:", fill=(0, 0, 0), font=self.font)
        draw.text((300, 550), f"{currency}{price_val:.2f}", fill=(0, 0, 0), font=self.font)
        
        draw.text((100, 580), "Processing Fee:", fill=(0, 0, 0), font=self.font)
        draw.text((300, 580), f"{currency}{fee_val:.2f}", fill=(0, 0, 0), font=self.font)
        
        draw.text((100, 610), "Shipping:", fill=(0, 0, 0), font=self.font)
        draw.text((300, 610), f"{currency}{shipping_val:.2f}", fill=(0, 0, 0), font=self.font)
        
        draw.text((100, 640), f"Tax ({tax_rate*100:.0f}%):", fill=(0, 0, 0), font=self.font)
        draw.text((300, 640), f"{currency}{tax:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator for total
        draw.line([(100, 670), (350, 670)], fill=(0, 0, 0), width=1)
        
        draw.text((100, 700), "Total:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((300, 700), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.bold_font)
        
        # Add shipping information
        draw.text((450, 510), "SHIPPING INFORMATION", fill=(0, 0, 0), font=self.bold_font)
        
        name = data.get("full_name", "John Doe")
        draw.text((450, 550), name, fill=(0, 0, 0), font=self.font)
        
        if "shipping_address" in data:
            address_lines = data["shipping_address"].split('\n')
            for i, line in enumerate(address_lines):
                draw.text((450, 580 + i*30), line, fill=(0, 0, 0), font=self.font)
        
        # Add payment information
        draw.text((100, 750), "PAYMENT INFORMATION", fill=(0, 0, 0), font=self.bold_font)
        
        payment_method = data.get("payment", "Visa")
        last_4 = random.randint(1000, 9999)
        
        draw.text((100, 790), f"{payment_method} ending in {last_4}", fill=(0, 0, 0), font=self.font)
        draw.text((100, 820), f"Amount: {currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add authentication guarantee (StockX specific)
        draw.rectangle([(400, 750), (700, 850)], outline=(0, 185, 0), width=2)
        draw.text((550, 780), "100% AUTHENTIC", fill=(0, 185, 0), font=self.bold_font, anchor="mm")
        draw.text((550, 810), "StockX Verified", fill=(0, 185, 0), font=self.font, anchor="mm")
        
        # Add footer
        draw.text((400, 900), "StockX: The Stock Market of Things", fill=(0, 185, 0), font=self.bold_font, anchor="mm")
        draw.text((400, 930), "www.stockx.com", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        return img
    
    def _generate_goat_receipt(self, img, draw, data):
        """Generate a GOAT-specific receipt."""
        # Create a new white image for GOAT receipt
        img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Add GOAT logo
        try:
            logo = self.download_image(STORES["goat"]["logo_url"])
            if logo:
                logo = logo.resize((150, 50), Image.LANCZOS)
                img.paste(logo, (325, 50), logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            self.logger.error(f"Error adding GOAT logo: {e}")
        
        # Add order information header
        draw.text((400, 120), "ORDER CONFIRMATION", fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        
        # Add date and order number
        order_date = data.get("date", datetime.now().strftime("%m/%d/%Y"))
        order_num = f"GO-{random.randint(1000000, 9999999)}"
        
        draw.text((100, 170), "ORDER DATE:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((250, 170), order_date, fill=(0, 0, 0), font=self.font)
        
        draw.text((500, 170), "ORDER #:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((600, 170), order_num, fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(100, 210), (700, 210)], fill=(200, 200, 200), width=2)
        
        # Add product info header
        draw.text((100, 240), "PRODUCT INFORMATION", fill=(0, 0, 0), font=self.bold_font)
        
        # Add product image placeholder
        draw.rectangle([(100, 280), (300, 430)], outline=(200, 200, 200))
        
        # Try to add product image if URL is provided
        if "image_url" in data and data["image_url"]:
            try:
                product_img = self.download_image(data["image_url"])
                if product_img:
                    product_img = product_img.resize((200, 150), Image.LANCZOS)
                    img.paste(product_img, (100, 280), product_img if product_img.mode == 'RGBA' else None)
            except Exception as e:
                self.logger.error(f"Error adding product image: {e}")
                draw.text((200, 355), "Product Image", fill=(150, 150, 150), font=self.font, anchor="mm")
        else:
            draw.text((200, 355), "Product Image", fill=(150, 150, 150), font=self.font, anchor="mm")
        
        # Add product details
        product = data.get("product", "Unknown Product")
        price = data.get("price", "0.00")
        
        # Get size information
        size = data.get("size", "")
        size_display = f"Size: {size}" if size else ""
        
        # Show product information
        if len(product) > 30:
            draw.text((350, 280), product[:30], fill=(0, 0, 0), font=self.bold_font)
            draw.text((350, 310), product[30:60], fill=(0, 0, 0), font=self.font)
        else:
            draw.text((350, 280), product, fill=(0, 0, 0), font=self.bold_font)
        
        # Add SKU/Style
        sku = data.get("style_id", f"SKU-{random.randint(100000, 999999)}")
        draw.text((350, 340), f"SKU: {sku}", fill=(100, 100, 100), font=self.font)
        
        # Add size
        draw.text((350, 370), size_display, fill=(0, 0, 0), font=self.font)
        
        # Add condition
        condition = data.get("condition", "New")
        draw.text((350, 400), f"Condition: {condition}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(100, 450), (700, 450)], fill=(200, 200, 200), width=2)
        
        # Add shipping address
        draw.text((100, 480), "SHIPPING ADDRESS", fill=(0, 0, 0), font=self.bold_font)
        
        name = data.get("full_name", "John Doe")
        draw.text((100, 510), name, fill=(0, 0, 0), font=self.font)
        
        if "shipping_address" in data:
            address_lines = data["shipping_address"].split('\n')
            for i, line in enumerate(address_lines):
                draw.text((100, 540 + i*30), line, fill=(0, 0, 0), font=self.font)
        
        # Add order summary
        draw.text((400, 480), "ORDER SUMMARY", fill=(0, 0, 0), font=self.bold_font)
        
        # Calculate values
        try:
            price_val = float(price)
        except (ValueError, TypeError):
            price_val = 0.0
        
        # Get shipping
        shipping_cost = data.get("shipping_cost", "0.00")
        try:
            shipping_val = float(shipping_cost)
        except (ValueError, TypeError):
            shipping_val = 12.00  # Default GOAT shipping
        
        # Calculate tax (varies by state, using 7% as example)
        tax_rate = 0.07
        tax = price_val * tax_rate
        
        # Calculate total
        total = price_val + shipping_val + tax
        
        currency = data.get("currency", "$")
        
        # Display order summary
        draw.text((400, 510), "Subtotal:", fill=(0, 0, 0), font=self.font)
        draw.text((650, 510), f"{currency}{price_val:.2f}", fill=(0, 0, 0), font=self.font)
        
        draw.text((400, 540), "Shipping:", fill=(0, 0, 0), font=self.font)
        draw.text((650, 540), f"{currency}{shipping_val:.2f}", fill=(0, 0, 0), font=self.font)
        
        draw.text((400, 570), f"Tax ({tax_rate*100:.0f}%):", fill=(0, 0, 0), font=self.font)
        draw.text((650, 570), f"{currency}{tax:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator for total
        draw.line([(400, 600), (700, 600)], fill=(0, 0, 0), width=1)
        
        draw.text((400, 630), "Total:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((650, 630), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.bold_font)
        
        # Add payment method
        draw.text((100, 650), "PAYMENT INFORMATION", fill=(0, 0, 0), font=self.bold_font)
        
        payment_method = data.get("payment", "Visa")
        last_4 = random.randint(1000, 9999)
        
        draw.text((100, 680), f"{payment_method} ending in {last_4}", fill=(0, 0, 0), font=self.font)
        draw.text((100, 710), f"Amount: {currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add authentication guarantee (GOAT specific)
        draw.rectangle([(100, 750), (700, 830)], outline=(0, 0, 0), width=2)
        draw.text((400, 780), "AUTHENTICITY GUARANTEED", fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        draw.text((400, 810), "This item has been verified by GOAT's authentication team.", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        # Add footer
        draw.text((400, 900), "Thank you for shopping with GOAT", fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        draw.text((400, 930), "www.goat.com", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        return img
    
    # Add other store-specific receipt generators as needed
    def _generate_walmart_receipt(self, img, draw, data):
        """Generate a Walmart-specific receipt."""
        # Create a new white image for Walmart receipt
        img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Add Walmart logo
        try:
            logo = self.download_image(STORES["walmart"]["logo_url"])
            if logo:
                logo = logo.resize((200, 100), Image.LANCZOS)
                img.paste(logo, (300, 50), logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            self.logger.error(f"Error adding Walmart logo: {e}")
        
        # Add receipt title
        draw.text((400, 180), "eReceipt", fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        
        # Generate store number and add store info
        store_num = random.randint(1000, 9999)
        draw.text((400, 210), f"Store #{store_num}", fill=(0, 0, 0), font=self.font, anchor="mm")
        draw.text((400, 240), "123 Main Street, Anytown, USA", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        # Add order date and number
        order_date = data.get("date", datetime.now().strftime("%m/%d/%Y"))
        order_time = datetime.now().strftime("%I:%M %p")
        receipt_num = random.randint(10000, 99999)
        
        draw.text((100, 280), f"Date: {order_date}", fill=(0, 0, 0), font=self.font)
        draw.text((100, 310), f"Time: {order_time}", fill=(0, 0, 0), font=self.font)
        draw.text((500, 280), f"Receipt #: {receipt_num}", fill=(0, 0, 0), font=self.font)
        
        # Add cashier info
        cashier_names = ["John", "Mary", "Robert", "Lisa", "Michael"]
        cashier = random.choice(cashier_names)
        draw.text((500, 310), f"Cashier: {cashier}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(100, 350), (700, 350)], fill=(0, 0, 0), width=1)
        
        # Add item headers
        draw.text((100, 380), "ITEM", fill=(0, 0, 0), font=self.bold_font)
        draw.text((500, 380), "PRICE", fill=(0, 0, 0), font=self.bold_font)
        draw.text((600, 380), "QTY", fill=(0, 0, 0), font=self.bold_font)
        draw.text((700, 380), "TOTAL", fill=(0, 0, 0), font=self.bold_font)
        
        # Add horizontal separator
        draw.line([(100, 410), (700, 410)], fill=(0, 0, 0), width=1)
        
        # Add product details
        product = data.get("product", "Unknown Product")
        price = data.get("price", "0.00")
        quantity = data.get("quantity", 1)
        
        # Format product name to wrap if too long
        y_position = 440
        if len(product) > 40:
            lines = [product[i:i+40] for i in range(0, len(product), 40)]
            for i, line in enumerate(lines[:2]):  # Only show first two lines
                draw.text((100, y_position + i*30), line, fill=(0, 0, 0), font=self.font)
            y_position = 440 + (min(len(lines), 2) - 1) * 30
        else:
            draw.text((100, y_position), product, fill=(0, 0, 0), font=self.font)
        
        # Calculate total
        try:
            price_val = float(price)
            total = price_val * int(quantity)
        except (ValueError, TypeError):
            price_val = 0.0
            total = 0.0
        
        currency = data.get("currency", "$")
        draw.text((500, 440), f"{currency}{price_val:.2f}", fill=(0, 0, 0), font=self.font)
        draw.text((600, 440), str(quantity), fill=(0, 0, 0), font=self.font)
        draw.text((700, 440), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(100, y_position + 60), (700, y_position + 60)], fill=(0, 0, 0), width=1)
        
        # Add subtotal
        y_position += 90
        draw.text((500, y_position), "Subtotal:", fill=(0, 0, 0), font=self.font)
        draw.text((700, y_position), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add tax
        tax_rate = 0.0825  # Example tax rate (8.25%)
        tax = total * tax_rate
        
        y_position += 30
        draw.text((500, y_position), f"Tax ({tax_rate*100:.2f}%):", fill=(0, 0, 0), font=self.font)
        draw.text((700, y_position), f"{currency}{tax:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        y_position += 30
        draw.line([(500, y_position), (700, y_position)], fill=(0, 0, 0), width=1)
        
        # Add total
        grand_total = total + tax
        
        y_position += 30
        draw.text((500, y_position), "Total:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((700, y_position), f"{currency}{grand_total:.2f}", fill=(0, 0, 0), font=self.bold_font)
        
        # Add payment method
        payment_method = data.get("payment", "Visa")
        last_4 = random.randint(1000, 9999)
        
        y_position += 30
        draw.text((500, y_position), f"{payment_method} **** {last_4}:", fill=(0, 0, 0), font=self.font)
        draw.text((700, y_position), f"{currency}{grand_total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add change
        y_position += 30
        draw.text((500, y_position), "Change:", fill=(0, 0, 0), font=self.font)
        draw.text((700, y_position), f"{currency}0.00", fill=(0, 0, 0), font=self.font)
        
        # Add customer information if available
        if "full_name" in data:
            y_position += 60
            draw.text((100, y_position), "CUSTOMER INFORMATION", fill=(0, 0, 0), font=self.bold_font)
            
            name = data.get("full_name", "John Doe")
            y_position += 30
            draw.text((100, y_position), f"Name: {name}", fill=(0, 0, 0), font=self.font)
            
            if "shipping_address" in data:
                y_position += 30
                draw.text((100, y_position), "Shipping Address:", fill=(0, 0, 0), font=self.font)
                
                address_lines = data["shipping_address"].split('\n')
                for i, line in enumerate(address_lines):
                    y_position += 30
                    draw.text((120, y_position), line, fill=(0, 0, 0), font=self.font)
        
        # Add footer with Walmart slogan
        draw.text((400, 900), "Save Money. Live Better.", fill=(0, 73, 144), font=self.bold_font, anchor="mm")
        draw.text((400, 930), "www.walmart.com", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        return img
    
    def _generate_bestbuy_receipt(self, img, draw, data):
        """Generate a Best Buy-specific receipt."""
        # Create a new white image for Best Buy receipt
        img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Add blue header
        draw.rectangle([(0, 0), (800, 100)], fill=(0, 70, 190))
        
        # Add Best Buy logo
        try:
            logo = self.download_image(STORES["bestbuy"]["logo_url"])
            if logo:
                logo = logo.resize((150, 75), Image.LANCZOS)
                img.paste(logo, (325, 15), logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            self.logger.error(f"Error adding Best Buy logo: {e}")
        
        # Add receipt title
        draw.text((400, 120), "CUSTOMER RECEIPT", fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        
        # Add order information
        order_date = data.get("date", datetime.now().strftime("%m/%d/%Y"))
        order_time = datetime.now().strftime("%I:%M %p")
        order_num = f"BBY01-{random.randint(100000000, 999999999)}"
        store_num = random.randint(100, 999)
        
        draw.text((100, 160), f"Store #: {store_num}", fill=(0, 0, 0), font=self.font)
        draw.text((350, 160), f"Date: {order_date}", fill=(0, 0, 0), font=self.font)
        draw.text((550, 160), f"Time: {order_time}", fill=(0, 0, 0), font=self.font)
        draw.text((100, 190), f"Order #: {order_num}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        draw.line([(100, 220), (700, 220)], fill=(0, 0, 0), width=1)
        
        # Add customer information if available
        y_position = 250
        if "full_name" in data:
            draw.text((100, y_position), "CUSTOMER INFORMATION", fill=(0, 0, 0), font=self.bold_font)
            
            name = data.get("full_name", "John Doe")
            y_position += 30
            draw.text((100, y_position), f"Name: {name}", fill=(0, 0, 0), font=self.font)
            
            if "shipping_address" in data:
                y_position += 30
                draw.text((100, y_position), "Ship To:", fill=(0, 0, 0), font=self.font)
                
                address_lines = data["shipping_address"].split('\n')
                for i, line in enumerate(address_lines):
                    y_position += 30
                    draw.text((120, y_position), line, fill=(0, 0, 0), font=self.font)
            
            y_position += 50
        
        # Add product information header
        draw.text((100, y_position), "PRODUCT INFORMATION", fill=(0, 0, 0), font=self.bold_font)
        
        # Add item headers
        y_position += 30
        draw.text((100, y_position), "DESCRIPTION", fill=(0, 0, 0), font=self.bold_font)
        draw.text((500, y_position), "PRICE", fill=(0, 0, 0), font=self.bold_font)
        draw.text((600, y_position), "QTY", fill=(0, 0, 0), font=self.bold_font)
        draw.text((700, y_position), "TOTAL", fill=(0, 0, 0), font=self.bold_font)
        
        # Add horizontal separator
        y_position += 20
        draw.line([(100, y_position), (700, y_position)], fill=(0, 0, 0), width=1)
        
        # Add product details
        product = data.get("product", "Unknown Product")
        price = data.get("price", "0.00")
        quantity = data.get("quantity", 1)
        
        # Format product name to wrap if too long
        y_position += 30
        product_y = y_position
        if len(product) > 35:
            lines = [product[i:i+35] for i in range(0, len(product), 35)]
            for i, line in enumerate(lines[:2]):  # Only show first two lines
                draw.text((100, product_y + i*30), line, fill=(0, 0, 0), font=self.font)
        else:
            draw.text((100, product_y), product, fill=(0, 0, 0), font=self.font)
        
        # Generate SKU
        sku = data.get("style_id", f"{random.randint(1000000, 9999999)}")
        if len(product) <= 35:
            draw.text((100, product_y + 30), f"SKU: {sku}", fill=(100, 100, 100), font=self.small_font)
        else:
            draw.text((100, product_y + 60), f"SKU: {sku}", fill=(100, 100, 100), font=self.small_font)
        
        # Calculate total
        try:
            price_val = float(price)
            total = price_val * int(quantity)
        except (ValueError, TypeError):
            price_val = 0.0
            total = 0.0
        
        currency = data.get("currency", "$")
        draw.text((500, product_y), f"{currency}{price_val:.2f}", fill=(0, 0, 0), font=self.font)
        draw.text((600, product_y), str(quantity), fill=(0, 0, 0), font=self.font)
        draw.text((700, product_y), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        y_position = max(product_y + 90, y_position + 90)
        draw.line([(100, y_position), (700, y_position)], fill=(0, 0, 0), width=1)
        
        # Add subtotal
        y_position += 30
        draw.text((500, y_position), "Subtotal:", fill=(0, 0, 0), font=self.font)
        draw.text((700, y_position), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add tax
        tax_rate = 0.0725  # Example tax rate (7.25%)
        tax = total * tax_rate
        
        y_position += 30
        draw.text((500, y_position), f"Tax ({tax_rate*100:.2f}%):", fill=(0, 0, 0), font=self.font)
        draw.text((700, y_position), f"{currency}{tax:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add shipping
        shipping_cost = data.get("shipping_cost", "0.00")
        try:
            shipping_val = float(shipping_cost)
        except (ValueError, TypeError):
            shipping_val = 0.0
        
        y_position += 30
        draw.text((500, y_position), "Shipping:", fill=(0, 0, 0), font=self.font)
        draw.text((700, y_position), f"{currency}{shipping_val:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add horizontal separator
        y_position += 30
        draw.line([(500, y_position), (700, y_position)], fill=(0, 0, 0), width=1)
        
        # Add total
        grand_total = total + tax + shipping_val
        
        y_position += 30
        draw.text((500, y_position), "TOTAL:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((700, y_position), f"{currency}{grand_total:.2f}", fill=(0, 0, 0), font=self.bold_font)
        
        # Add payment information
        y_position += 60
        draw.text((100, y_position), "PAYMENT INFORMATION", fill=(0, 0, 0), font=self.bold_font)
        
        payment_method = data.get("payment", "Visa")
        last_4 = random.randint(1000, 9999)
        
        y_position += 30
        draw.text((100, y_position), f"{payment_method} **** {last_4}:", fill=(0, 0, 0), font=self.font)
        draw.text((400, y_position), f"{currency}{grand_total:.2f}", fill=(0, 0, 0), font=self.font)
        
        # Add Return Policy
        y_position += 60
        draw.text((100, y_position), "RETURN POLICY", fill=(0, 0, 0), font=self.bold_font)
        
        y_position += 30
        draw.text((100, y_position), "Standard Return Policy: 15 days for most items", fill=(0, 0, 0), font=self.small_font)
        y_position += 25
        draw.text((100, y_position), "Elite Members: 30 days for most items", fill=(0, 0, 0), font=self.small_font)
        y_position += 25
        draw.text((100, y_position), "Elite Plus Members: 45 days for most items", fill=(0, 0, 0), font=self.small_font)
        
        # Add Best Buy Rewards message
        y_position += 60
        draw.rectangle([(100, y_position), (700, y_position + 80)], outline=(0, 70, 190), width=2)
        
        y_position += 20
        draw.text((400, y_position), "JOIN MY BEST BUY REWARDS", fill=(0, 70, 190), font=self.bold_font, anchor="mm")
        y_position += 30
        draw.text((400, y_position), "Get points for every dollar you spend", fill=(0, 0, 0), font=self.font, anchor="mm")
        
        # Add footer with Best Buy tagline
        draw.text((400, 900), "BEST BUY", fill=(0, 70, 190), font=self.bold_font, anchor="mm")
        draw.text((400, 930), "www.bestbuy.com", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        return img
    
    def _generate_louisvuitton_receipt(self, img, draw, data):
        """Generate a Louis Vuitton-specific receipt."""
        # Create a new cream-colored image for LV receipt (luxury feel)
        img = Image.new('RGB', (800, 1000), color=(245, 245, 240))
        draw = ImageDraw.Draw(img)
        
        # Add Louis Vuitton logo
        try:
            logo = self.download_image(STORES["louisvuitton"]["logo_url"])
            if logo:
                logo = logo.resize((200, 100), Image.LANCZOS)
                img.paste(logo, (300, 50), logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            self.logger.error(f"Error adding Louis Vuitton logo: {e}")
        
        # Add receipt title with elegant spacing
        draw.text((400, 180), "PURCHASE RECEIPT", fill=(101, 67, 33), font=self.bold_font, anchor="mm")
        
        # Add order information
        order_date = data.get("date", datetime.now().strftime("%d %B %Y"))  # More elegant date format
        boutique_num = random.randint(100, 999)
        receipt_num = f"LV{random.randint(10000, 99999)}"
        
        draw.text((400, 220), f"Date: {order_date}", fill=(0, 0, 0), font=self.font, anchor="mm")
        draw.text((400, 250), f"Boutique: {boutique_num}", fill=(0, 0, 0), font=self.font, anchor="mm")
        draw.text((400, 280), f"Receipt: {receipt_num}", fill=(0, 0, 0), font=self.font, anchor="mm")
        
        # Add horizontal separator (thin and elegant)
        draw.line([(200, 320), (600, 320)], fill=(101, 67, 33), width=1)
        
        # Add customer information
        name = data.get("full_name", "John Doe")
        draw.text((400, 350), name, fill=(0, 0, 0), font=self.bold_font, anchor="mm")
        
        if "shipping_address" in data:
            address_lines = data["shipping_address"].split('\n')
            y_position = 380
            for line in address_lines:
                draw.text((400, y_position), line, fill=(0, 0, 0), font=self.font, anchor="mm")
                y_position += 30
        
        # Add another horizontal separator
        draw.line([(200, 480), (600, 480)], fill=(101, 67, 33), width=1)
        
        # Add product details in an elegant format
        draw.text((400, 520), "PRODUCT DETAILS", fill=(101, 67, 33), font=self.bold_font, anchor="mm")
        
        # Add product name with proper formatting for luxury items
        product = data.get("product", "Unknown Product")
        
        # Format product name elegantly, centered
        y_position = 560
        if len(product) > 30:
            lines = [product[i:i+30] for i in range(0, len(product), 30)]
            for line in lines[:2]:  # Only show first two lines
                draw.text((400, y_position), line, fill=(0, 0, 0), font=self.font, anchor="mm")
                y_position += 30
        else:
            draw.text((400, y_position), product, fill=(0, 0, 0), font=self.font, anchor="mm")
            y_position += 30
        
        # Add product code/style if available
        style_id = data.get("style_id", f"M{random.randint(10000, 99999)}")
        draw.text((400, y_position + 20), f"Ref: {style_id}", fill=(101, 67, 33), font=self.small_font, anchor="mm")
        
        # Add horizontal separator
        draw.line([(300, y_position + 60), (500, y_position + 60)], fill=(101, 67, 33), width=1)
        
        # Add price information
        price = data.get("price", "0.00")
        try:
            price_val = float(price)
        except (ValueError, TypeError):
            price_val = 0.0
        
        currency = data.get("currency", "$")
        
        # Calculate tax
        tax_rate = 0.0825  # Example tax rate (8.25%)
        tax = price_val * tax_rate
        
        # Add shipping
        shipping_cost = data.get("shipping_cost", "0.00")
        try:
            shipping_val = float(shipping_cost)
        except (ValueError, TypeError):
            shipping_val = 0.0  # Luxury brands often offer free shipping
        
        # Calculate total
        total = price_val + tax + shipping_val
        
        # Display price details elegantly
        y_position += 80
        
        draw.text((300, y_position), "Price:", fill=(0, 0, 0), font=self.font)
        draw.text((500, y_position), f"{currency}{price_val:.2f}", fill=(0, 0, 0), font=self.font, anchor="ra")
        
        y_position += 30
        draw.text((300, y_position), f"Tax ({tax_rate*100:.2f}%):", fill=(0, 0, 0), font=self.font)
        draw.text((500, y_position), f"{currency}{tax:.2f}", fill=(0, 0, 0), font=self.font, anchor="ra")
        
        y_position += 30
        draw.text((300, y_position), "Shipping:", fill=(0, 0, 0), font=self.font)
        draw.text((500, y_position), f"{currency}{shipping_val:.2f}", fill=(0, 0, 0), font=self.font, anchor="ra")
        
        # Add horizontal separator for total
        y_position += 20
        draw.line([(300, y_position), (500, y_position)], fill=(101, 67, 33), width=1)
        
        # Add total
        y_position += 30
        draw.text((300, y_position), "Total:", fill=(0, 0, 0), font=self.bold_font)
        draw.text((500, y_position), f"{currency}{total:.2f}", fill=(0, 0, 0), font=self.bold_font, anchor="ra")
        
        # Add payment method
        y_position += 60
        payment_method = data.get("payment", "Visa")
        last_4 = random.randint(1000, 9999)
        
        draw.text((400, y_position), f"Payment: {payment_method} **** {last_4}", fill=(0, 0, 0), font=self.font, anchor="mm")
        
        # Add thank you note (elegant and personalized)
        y_position += 100
        draw.text((400, y_position), "Thank you for your purchase", fill=(101, 67, 33), font=self.bold_font, anchor="mm")
        
        y_position += 30
        draw.text((400, y_position), "We are delighted to welcome you to the Louis Vuitton world", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        # Add footer
        draw.text((400, 900), "LOUIS VUITTON", fill=(101, 67, 33), font=self.bold_font, anchor="mm")
        draw.text((400, 930), "www.louisvuitton.com", fill=(0, 0, 0), font=self.small_font, anchor="mm")
        
        return img
