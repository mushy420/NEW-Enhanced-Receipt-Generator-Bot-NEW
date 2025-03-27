import logging
from io import BytesIO
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import os
import requests
from datetime import datetime
import hashlib
import random

# Setup logging
logger = logging.getLogger('receipt_generator')

class ReceiptGenerator:
    """Class to generate receipt images."""
    
    def __init__(self):
        self.logger = logging.getLogger('receipt_generator')
    
    def generate_receipt(self, store_id: str, data: Dict[str, Any]) -> Optional[BytesIO]:
        """Generate a receipt image based on store and data.
        
        Args:
            store_id: The ID of the store.
            data: Dictionary containing receipt data.
            
        Returns:
            BytesIO: The receipt image as a BytesIO object, or None if generation failed.
        """
        try:
            self.logger.info(f"Generating receipt for store {store_id}")
            
            # Find a reliable font
            fonts = self._load_fonts()
            
            # Create a new image with white background
            width, height = 800, 1200
            
            # For Amazon, use a light cream background
            background_color = (255, 255, 255)  # White for basic template
            if store_id == 'amazon':
                background_color = (252, 252, 248)  # Light cream for Amazon
            
            image = Image.new('RGB', (width, height), color=background_color)
            draw = ImageDraw.Draw(image)
            
            # Use store-specific template
            if store_id == 'amazon':
                return self._generate_amazon_receipt(image, draw, data, fonts)
            elif store_id == 'apple':
                return self._generate_apple_receipt(image, draw, data, fonts)
            
            # Default template for any other store
            return self._generate_default_receipt(image, draw, data, store_id, fonts)
            
        except Exception as e:
            self.logger.error(f"Error generating receipt: {str(e)}", exc_info=True)
            return None
    
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts needed for receipt generation."""
        try:
            # Look for fonts in multiple common locations
            possible_fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/Library/Fonts/Arial.ttf",  # macOS
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                "/usr/share/fonts/TTF/DejaVuSans.ttf",  # Another Linux path
                "arial.ttf",  # Fallback
                "./fonts/Arial.ttf"  # Project fonts directory
            ]
            
            # Find the first available font
            for font_path in possible_fonts:
                if os.path.exists(font_path):
                    break
            else:
                font_path = None
                
            # Create a fonts directory if it doesn't exist
            os.makedirs("./fonts", exist_ok=True)
            
            # If no font found, use default
            if not font_path:
                title_font = ImageFont.load_default()
                regular_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
                bold_font = ImageFont.load_default()
                small_bold_font = ImageFont.load_default()
            else:
                # Create different font sizes
                title_font = ImageFont.truetype(font_path, 28)
                regular_font = ImageFont.truetype(font_path, 20)
                small_font = ImageFont.truetype(font_path, 16)
                
                # Try to find a bold font
                bold_font_path = None
                possible_bold_fonts = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "/Library/Fonts/Arial Bold.ttf",
                    "C:\\Windows\\Fonts\\arialbd.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
                    "./fonts/Arial-Bold.ttf"
                ]
                
                for bold_path in possible_bold_fonts:
                    if os.path.exists(bold_path):
                        bold_font_path = bold_path
                        break
                
                # If no bold font found, use regular font
                if not bold_font_path:
                    bold_font = regular_font
                    small_bold_font = small_font
                else:
                    bold_font = ImageFont.truetype(bold_font_path, 20)
                    small_bold_font = ImageFont.truetype(bold_font_path, 16)
            
            return {
                'title': title_font,
                'regular': regular_font,
                'small': small_font,
                'bold': bold_font,
                'small_bold': small_bold_font
            }
            
        except Exception as e:
            self.logger.error(f"Error loading fonts: {str(e)}", exc_info=True)
            # Fallback to default font
            default = ImageFont.load_default()
            return {
                'title': default,
                'regular': default,
                'small': default,
                'bold': default,
                'small_bold': default
            }
    
    def _generate_amazon_receipt(self, image: Image.Image, draw: ImageDraw.Draw, 
                               data: Dict[str, Any], fonts: Dict[str, ImageFont.FreeTypeFont]) -> BytesIO:
        """Generate an Amazon-styled receipt matching the real example."""
        width, height = image.size
        
        # AMAZON HEADER SECTION
        # ---------------------
        # Amazon logo
        draw.text((width//2, 50), "amazon", fill=(0, 0, 0), font=fonts['title'], anchor="mm")
        
        # Amazon smile underline (orange curve)
        draw.arc([(width//2 - 55, 55), (width//2 + 55, 75)], 0, 180, fill=(255, 153, 0), width=2)
        
        # Add "Order Confirmation" text
        draw.text((width//2, 100), "Order Confirmation", fill=(0, 0, 0), font=fonts['regular'], anchor="mm")
        
        # Draw header separator line
        draw.line([(50, 130), (width-50, 130)], fill=(220, 220, 220), width=1)
        
        # Current position for drawing content
        y_position = 160
        
        # GREETING SECTION
        # ---------------
        # Add greeting if customer name is provided
        if 'customer_name' in data:
            draw.text((58, y_position), f"Hello {data['customer_name']},", fill=(50, 50, 50), font=fonts['regular'])
            y_position += 40
        else:
            draw.text((58, y_position), "Hello,", fill=(50, 50, 50), font=fonts['regular'])
            y_position += 40
        
        # Thank you message
        draw.text((58, y_position), "Thank you for shopping with Amazon.", fill=(80, 80, 80), font=fonts['small'])
        y_position += 30
        
        # Order confirmation message
        draw.text((58, y_position), "Your order has been confirmed and will ship soon.", fill=(80, 80, 80), font=fonts['small'])
        y_position += 40
        
        # ORDER DETAILS SECTION
        # --------------------
        # Draw a separator line
        draw.line([(50, y_position), (width-50, y_position)], fill=(220, 220, 220), width=1)
        y_position += 30
        
        # Order Details heading
        draw.text((58, y_position), "Order Details", fill=(40, 40, 40), font=fonts['bold'])
        y_position += 40
        
        # Order number and date
        order_number = data.get('order_number', '')
        if not order_number:
            # Generate a realistic Amazon order number
            random_chars = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=7))
            order_number = f"113-{random_chars}-{random.randint(1000000, 9999999)}"
        
        order_date = data.get('date', datetime.now().strftime('%B %d, %Y'))
        
        # Format date to look more like Amazon's format (e.g., "August 15, 2023")
        try:
            date_obj = datetime.strptime(order_date, '%m/%d/%Y')
            order_date = date_obj.strftime('%B %d, %Y')
        except:
            # Keep existing format if parsing fails
            pass
        
        draw.text((58, y_position), f"Order #: {order_number}", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 30
        draw.text((58, y_position), f"Order Date: {order_date}", fill=(80, 80, 80), font=fonts['small'])
        y_position += 40
        
        # ITEMS SECTION
        # ------------
        draw.text((58, y_position), "Items Ordered:", fill=(40, 40, 40), font=fonts['bold'])
        y_position += 30
        
        # Product details with a light gray background
        product_section = [(50, y_position), (width-50, y_position + 160)]
        draw.rectangle(product_section, fill=(245, 245, 245))
        
        # Product name and price
        if 'product' in data:
            # Truncate product name if too long
            product_name = data['product']
            if len(product_name) > 60:
                product_name = product_name[:57] + "..."
                
            # Product name
            draw.text((70, y_position + 20), product_name, fill=(0, 0, 0), font=fonts['bold'])
            
            # Sold by Amazon.com
            draw.text((70, y_position + 50), "Sold by: Amazon.com Services LLC", fill=(80, 80, 80), font=fonts['small'])
            
            # Quantity (default to 1)
            quantity = data.get('quantity', 1)
            draw.text((70, y_position + 75), f"Quantity: {quantity}", fill=(80, 80, 80), font=fonts['small'])
            
            # Price
            if 'price' in data:
                price = data.get('price', '0.00')
                draw.text((70, y_position + 100), f"Price: ${price}", fill=(0, 0, 0), font=fonts['regular'])
                
                # Calculate subtotal
                try:
                    subtotal = float(price) * int(quantity)
                    subtotal_str = f"{subtotal:.2f}"
                except (ValueError, TypeError):
                    subtotal_str = price
                    
                draw.text((70, y_position + 125), f"Subtotal: ${subtotal_str}", fill=(0, 0, 0), font=fonts['regular'])
        
        y_position = product_section[1][1] + 40
        
        # ORDER SUMMARY SECTION
        # -------------------
        draw.text((58, y_position), "Order Summary:", fill=(40, 40, 40), font=fonts['bold'])
        y_position += 40
        
        # Get price value
        price = data.get('price', '0.00')
        
        # Calculate values
        try:
            price_float = float(price)
            tax = price_float * 0.0925  # 9.25% tax
            shipping = 5.99
            total = price_float + tax + shipping
            
            # Format as strings
            price_str = f"{price_float:.2f}"
            tax_str = f"{tax:.2f}"
            shipping_str = f"{shipping:.2f}"
            total_str = f"{total:.2f}"
        except ValueError:
            price_str = price
            tax_str = "0.00"
            shipping_str = "5.99"
            total_str = "0.00"
        
        # Table layout
        left_x = 58
        right_x = width - 70
        
        # Summary table
        draw.text((left_x, y_position), "Items:", fill=(80, 80, 80), font=fonts['small'])
        draw.text((right_x, y_position), f"${price_str}", fill=(40, 40, 40), font=fonts['small'], anchor="ra")
        y_position += 25
        
        draw.text((left_x, y_position), "Shipping & handling:", fill=(80, 80, 80), font=fonts['small'])
        draw.text((right_x, y_position), f"${shipping_str}", fill=(40, 40, 40), font=fonts['small'], anchor="ra")
        y_position += 25
        
        # Calculate before tax
        try:
            before_tax = float(price_str) + float(shipping_str)
            before_tax_str = f"{before_tax:.2f}"
        except ValueError:
            before_tax_str = "0.00"
            
        draw.text((left_x, y_position), "Total before tax:", fill=(80, 80, 80), font=fonts['small'])
        draw.text((right_x, y_position), f"${before_tax_str}", fill=(40, 40, 40), font=fonts['small'], anchor="ra")
        y_position += 25
        
        draw.text((left_x, y_position), "Estimated tax:", fill=(80, 80, 80), font=fonts['small'])
        draw.text((right_x, y_position), f"${tax_str}", fill=(40, 40, 40), font=fonts['small'], anchor="ra")
        y_position += 25
        
        # Add a line before the total
        draw.line([(left_x, y_position), (right_x, y_position)], fill=(200, 200, 200), width=1)
        y_position += 15
        
        # Order total
        draw.text((left_x, y_position), "Order total:", fill=(40, 40, 40), font=fonts['bold'])
        draw.text((right_x, y_position), f"${total_str}", fill=(40, 40, 40), font=fonts['bold'], anchor="ra")
        
        y_position += 50
        
        # SHIPPING INFORMATION SECTION
        # --------------------------
        draw.text((58, y_position), "Shipping Information:", fill=(40, 40, 40), font=fonts['bold'])
        y_position += 30
        
        # Shipping address (if provided)
        if 'shipping_address' in data and data['shipping_address']:
            address_lines = data['shipping_address'].split('\n')
            for line in address_lines:
                draw.text((70, y_position), line, fill=(80, 80, 80), font=fonts['small'])
                y_position += 25
        
        # Shipping method
        y_position += 10
        draw.text((70, y_position), "Shipping Method: Standard Shipping", fill=(80, 80, 80), font=fonts['small'])
        y_position += 25
        
        # Estimated delivery
        # Calculate an estimated delivery date (7-10 days from order date)
        try:
            date_obj = datetime.strptime(data.get('date', datetime.now().strftime('%m/%d/%Y')), '%m/%d/%Y')
            delivery_date = date_obj + timedelta(days=random.randint(7, 10))
            delivery_date_str = delivery_date.strftime('%B %d, %Y')
        except:
            delivery_date_str = "7-10 business days"
            
        draw.text((70, y_position), f"Estimated Delivery: {delivery_date_str}", fill=(80, 80, 80), font=fonts['small'])
        y_position += 40
        
        # PAYMENT INFORMATION SECTION
        # -------------------------
        draw.text((58, y_position), "Payment Information:", fill=(40, 40, 40), font=fonts['bold'])
        y_position += 30
        
        # Payment method (default to a credit card)
        payment_method = data.get('payment_method', 'Visa ending in ****')
        draw.text((70, y_position), f"Payment Method: {payment_method}", fill=(80, 80, 80), font=fonts['small'])
        y_position += 25
        
        # Billing address - use shipping address if no billing address provided
        draw.text((70, y_position), "Billing Address:", fill=(80, 80, 80), font=fonts['small'])
        y_position += 25
        
        if 'shipping_address' in data and data['shipping_address']:
            address_lines = data['shipping_address'].split('\n')
            for line in address_lines:
                draw.text((90, y_position), line, fill=(80, 80, 80), font=fonts['small'])
                y_position += 20
        
        # FOOTER SECTION
        # -------------
        y_position = height - 100
        draw.text((width//2, y_position), "Thank you for shopping with Amazon!", fill=(80, 80, 80), font=fonts['small'], anchor="mm")
        y_position += 25
        draw.text((width//2, y_position), "Questions? Visit amazon.com/help", fill=(80, 80, 80), font=fonts['small'], anchor="mm")
        y_position += 25
        draw.text((width//2, y_position), "Order details can be viewed at amazon.com/orders", fill=(80, 80, 80), font=fonts['small'], anchor="mm")
        
        # Save the image to a BytesIO object
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)
        
        self.logger.info(f"Amazon receipt generated successfully")
        return img_io
    
    def _generate_apple_receipt(self, image: Image.Image, draw: ImageDraw.Draw, 
                              data: Dict[str, Any], fonts: Dict[str, ImageFont.FreeTypeFont]) -> BytesIO:
        """Generate an Apple-styled receipt."""
        width, height = image.size
        
        # Apple uses a very clean, minimalist design
        # Header with Apple logo text
        draw.text((width//2, 60), "Apple", fill=(0, 0, 0), font=fonts['title'], anchor="mm")
        
        # Add receipt title
        draw.text((width//2, 110), "Order Confirmation", fill=(0, 0, 0), font=fonts['regular'], anchor="mm")
        
        # Draw header separator line
        draw.line([(50, 140), (width-50, 140)], fill=(200, 200, 200), width=1)
        
        # Current position for drawing content
        y_position = 170
        
        # Add greeting if customer name is provided
        if 'customer_name' in data:
            draw.text((50, y_position), f"Hello {data['customer_name']},", fill=(0, 0, 0), font=fonts['regular'])
            y_position += 40
        
        # Thank you message
        draw.text((50, y_position), "Thank you for your order.", fill=(80, 80, 80), font=fonts['small'])
        y_position += 40
        
        # Order date
        order_date = data.get('date', datetime.now().strftime('%m/%d/%Y'))
        draw.text((50, y_position), f"Order Date: {order_date}", fill=(80, 80, 80), font=fonts['small'])
        y_position += 30
        
        # Serial number (specific to Apple)
        if 'serial_number' in data:
            draw.text((50, y_position), f"Serial Number: {data['serial_number']}", fill=(80, 80, 80), font=fonts['small'])
            y_position += 30
        
        # Draw a separator line
        draw.line([(50, y_position), (width-50, y_position)], fill=(200, 200, 200), width=1)
        y_position += 30
        
        # Product details section
        draw.text((50, y_position), "Product:", fill=(0, 0, 0), font=fonts['regular'])
        y_position += 40
        
        # Product name and price
        if 'product' in data:
            product_name = data['product']
            draw.text((70, y_position), product_name, fill=(0, 0, 0), font=fonts['regular'])
            y_position += 40
            
            # Price
            if 'price' in data:
                price = data.get('price', '0.00')
                draw.text((70, y_position), f"Price: ${price}", fill=(0, 0, 0), font=fonts['regular'])
                y_position += 40
        
        # Draw a separator line
        draw.line([(50, y_position), (width-50, y_position)], fill=(200, 200, 200), width=1)
        y_position += 30
        
        # Payment information
        draw.text((50, y_position), "Payment Method:", fill=(0, 0, 0), font=fonts['regular'])
        y_position += 30
        
        # Default to Apple Pay
        payment_method = data.get('payment_method', 'Apple Pay')
        draw.text((70, y_position), payment_method, fill=(80, 80, 80), font=fonts['small'])
        y_position += 40
        
        # Shipping information
        draw.text((50, y_position), "Shipping Address:", fill=(0, 0, 0), font=fonts['regular'])
        y_position += 30
        
        # Shipping address (if provided)
        if 'shipping_address' in data and data['shipping_address']:
            address_lines = data['shipping_address'].split('\n')
            for line in address_lines:
                draw.text((70, y_position), line, fill=(80, 80, 80), font=fonts['small'])
                y_position += 25
        
        # Add a support message
        y_position = height - 120
        draw.text((width//2, y_position), "Need help with your order?", fill=(0, 0, 0), font=fonts['small'], anchor="mm")
        y_position += 30
        draw.text((width//2, y_position), "Visit apple.com/support or call 1-800-MY-APPLE", fill=(80, 80, 80), font=fonts['small'], anchor="mm")
        
        # Save the image to a BytesIO object
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)
        
        self.logger.info(f"Apple receipt generated successfully")
        return img_io
        
    def _generate_default_receipt(self, image: Image.Image, draw: ImageDraw.Draw, data: Dict[str, Any], 
                                store_id: str, fonts: Dict[str, ImageFont.FreeTypeFont]) -> BytesIO:
        """Generate a default receipt template for stores without specific styling."""
        width, height = image.size
        
        # Draw store name at the top
        store_name = data.get('store_name', f"Receipt for {store_id.capitalize()}")
        draw.text((width//2, 50), store_name, fill=(0, 0, 0), font=fonts['title'], anchor="mt")
        
        # Draw a line separator
        draw.line([(50, 100), (width-50, 100)], fill=(0, 0, 0), width=2)
        
        # Draw customer info
        y_position = 150
        
        # Date
        if 'date' in data:
            draw.text((50, y_position), f"Date: {data['date']}", fill=(0, 0, 0), font=fonts['regular'])
            y_position += 30
        
        # Draw a line separator
        draw.line([(50, y_position), (width-50, y_position)], fill=(0, 0, 0), width=1)
        y_position += 20
        
        # Draw product details
        if 'product' in data:
            draw.text((50, y_position), f"Product: {data['product']}", fill=(0, 0, 0), font=fonts['regular'])
            y_position += 30
        
        # Price
        if 'price' in data and 'currency' in data:
            currency = data.get('currency', '$')
            draw.text((50, y_position), f"Price: {currency}{data['price']}", fill=(0, 0, 0), font=fonts['regular'])
            y_position += 30
        
        # Store-specific details
        if store_id == 'apple' and 'serial_number' in data:
            draw.text((50, y_position), f"Serial Number: {data['serial_number']}", fill=(0, 0, 0), font=fonts['regular'])
            y_position += 30
        
        # Draw shipping address
        if 'shipping_address' in data:
            draw.text((50, y_position), "Shipping Address:", fill=(0, 0, 0), font=fonts['regular'])
            y_position += 25
            
            address_lines = data['shipping_address'].split('\n')
            for line in address_lines:
                draw.text((70, y_position), line, fill=(0, 0, 0), font=fonts['small'])
                y_position += 20
        
        # Draw a thank you message at the bottom
        draw.text((width//2, height-100), "Thank you for your purchase!", fill=(0, 0, 0), font=fonts['regular'], anchor="mt")
        
        # Save the image to a BytesIO object
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)
        
        self.logger.info(f"Receipt generation successful for {store_id}")
        return img_io
