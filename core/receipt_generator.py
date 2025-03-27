import logging
from io import BytesIO
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import os
import requests
from datetime import datetime, timedelta
import hashlib
import random
import traceback

# Import core configuration
from core.config import FONT_PATH, FONT_SIZE

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
            elif store_id == 'bestbuy':
                return self._generate_bestbuy_receipt(image, draw, data, fonts)
            elif store_id == 'walmart':
                return self._generate_walmart_receipt(image, draw, data, fonts)
            
            # Default template for any other store
            return self._generate_default_receipt(image, draw, data, store_id, fonts)
            
        except Exception as e:
            error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            self.logger.error(f"Error generating receipt: {str(e)}\n{error_traceback}")
            return None
    
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts needed for receipt generation."""
        try:
            # Create fonts directory if it doesn't exist
            os.makedirs("./assets/fonts", exist_ok=True)
            
            # Look for fonts in multiple common locations
            possible_fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/Library/Fonts/Arial.ttf",  # macOS
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                "/usr/share/fonts/TTF/DejaVuSans.ttf",  # Another Linux path
                "arial.ttf",  # Fallback
                "./assets/fonts/Arial.ttf"  # Project fonts directory
            ]
            
            # Find the first available font
            font_path = None
            for path in possible_fonts:
                if os.path.exists(path):
                    font_path = path
                    break
                
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
                    "./assets/fonts/Arial-Bold.ttf"
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
        
        # APPLE HEADER SECTION
        # -------------------
        # Apple logo (simple Apple text for now)
        draw.text((width//2, 50), "Apple", fill=(0, 0, 0), font=fonts['title'], anchor="mm")
        
        # Receipt title
        draw.text((width//2, 100), "Purchase Receipt", fill=(0, 0, 0), font=fonts['regular'], anchor="mm")
        
        # Draw header separator line
        draw.line([(50, 130), (width-50, 130)], fill=(220, 220, 220), width=1)
        
        # Current position for drawing content
        y_position = 160
        
        # CUSTOMER INFORMATION SECTION
        # ---------------------------
        if 'customer_name' in data:
            draw.text((58, y_position), f"Customer: {data['customer_name']}", fill=(40, 40, 40), font=fonts['regular'])
            y_position += 30
        
        # Serial number if available
        if 'serial_number' in data:
            draw.text((58, y_position), f"Serial Number: {data['serial_number']}", fill=(40, 40, 40), font=fonts['regular'])
            y_position += 30
        
        # Add date
        order_date = data.get('date', datetime.now().strftime('%m/%d/%Y'))
        try:
            date_obj = datetime.strptime(order_date, '%m/%d/%Y')
            formatted_date = date_obj.strftime('%B %d, %Y')
        except:
            formatted_date = order_date
            
        draw.text((58, y_position), f"Date: {formatted_date}", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 40
        
        # Order number (generate if not provided)
        order_number = data.get('order_number', f"APPL{random.randint(10000000, 99999999)}")
        draw.text((58, y_position), f"Order Number: {order_number}", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 50
        
        # PRODUCT DETAILS SECTION
        # ----------------------
        # Draw a separator line
        draw.line([(50, y_position), (width-50, y_position)], fill=(220, 220, 220), width=1)
        y_position += 30
        
        draw.text((58, y_position), "Product Details", fill=(40, 40, 40), font=fonts['bold'])
        y_position += 40
        
        # Product information
        if 'product' in data:
            # Product name
            product_name = data['product']
            if len(product_name) > 60:
                product_name = product_name[:57] + "..."
            
            draw.text((70, y_position), product_name, fill=(0, 0, 0), font=fonts['bold'])
            y_position += 40
            
            # Price information
            if 'price' in data:
                price = data.get('price', '0.00')
                
                # Calculate values
                try:
                    price_float = float(price)
                    tax = price_float * 0.0725  # 7.25% tax (typical for Apple products)
                    total = price_float + tax
                    
                    # Format as strings
                    price_str = f"{price_float:.2f}"
                    tax_str = f"{tax:.2f}"
                    total_str = f"{total:.2f}"
                except ValueError:
                    price_str = price
                    tax_str = "0.00"
                    total_str = price
                
                # Product price table
                draw.text((70, y_position), f"Product Price: ${price_str}", fill=(40, 40, 40), font=fonts['regular'])
                y_position += 30
                
                draw.text((70, y_position), f"Tax: ${tax_str}", fill=(40, 40, 40), font=fonts['regular'])
                y_position += 30
                
                # Line before total
                draw.line([(70, y_position), (300, y_position)], fill=(200, 200, 200), width=1)
                y_position += 15
                
                draw.text((70, y_position), f"Total: ${total_str}", fill=(0, 0, 0), font=fonts['bold'])
                y_position += 50
        
        # SHIPPING & PAYMENT SECTION
        # -------------------------
        draw.text((58, y_position), "Shipping & Payment Information", fill=(40, 40, 40), font=fonts['bold'])
        y_position += 40
        
        # Shipping address
        if 'shipping_address' in data and data['shipping_address']:
            draw.text((70, y_position), "Shipping Address:", fill=(40, 40, 40), font=fonts['regular'])
            y_position += 25
            
            address_lines = data['shipping_address'].split('\n')
            for line in address_lines:
                draw.text((90, y_position), line, fill=(80, 80, 80), font=fonts['small'])
                y_position += 20
        
        y_position += 20
        
        # Payment method
        payment_method = data.get('payment_method', 'Apple Pay')
        draw.text((70, y_position), f"Payment Method: {payment_method}", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 50
        
        # FOOTER SECTION
        # -------------
        footer_y = height - 120
        
        draw.line([(50, footer_y), (width-50, footer_y)], fill=(220, 220, 220), width=1)
        footer_y += 30
        
        draw.text((width//2, footer_y), "Thank you for shopping with Apple", fill=(40, 40, 40), font=fonts['regular'], anchor="mm")
        footer_y += 30
        
        draw.text((width//2, footer_y), "For support visit apple.com/support", fill=(80, 80, 80), font=fonts['small'], anchor="mm")
        footer_y += 20
        
        draw.text((width//2, footer_y), "or call 1-800-MY-APPLE", fill=(80, 80, 80), font=fonts['small'], anchor="mm")
        
        # Save the image to a BytesIO object
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)
        
        self.logger.info(f"Apple receipt generated successfully")
        return img_io
    
    def _generate_bestbuy_receipt(self, image: Image.Image, draw: ImageDraw.Draw, 
                                data: Dict[str, Any], fonts: Dict[str, ImageFont.FreeTypeFont]) -> BytesIO:
        """Generate a Best Buy-styled receipt."""
        # Implement Best Buy receipt
        # Create a basic Best Buy receipt template
        width, height = image.size
        
        # Set Best Buy colors
        bb_blue = (10, 75, 189)  # Best Buy blue
        bb_yellow = (255, 242, 0)  # Best Buy yellow
        
        # HEADER SECTION
        # --------------
        # Best Buy logo (text and yellow tag)
        draw.text((width//2, 50), "BEST BUY", fill=bb_blue, font=fonts['title'], anchor="mm")
        
        # Draw a yellow tag next to the text
        draw.rectangle([(width//2 + 85, 40), (width//2 + 105, 60)], fill=bb_yellow)
        
        # Receipt title
        draw.text((width//2, 100), "Sales Receipt", fill=(0, 0, 0), font=fonts['regular'], anchor="mm")
        
        # Draw header separator line
        draw.line([(50, 130), (width-50, 130)], fill=bb_blue, width=2)
        
        # Current position for drawing content
        y_position = 160
        
        # STORE INFORMATION
        # ----------------
        draw.text((58, y_position), "Store #1234", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 25
        draw.text((58, y_position), "123 Main Street", fill=(40, 40, 40), font=fonts['small'])
        y_position += 20
        draw.text((58, y_position), "Anytown, USA 12345", fill=(40, 40, 40), font=fonts['small'])
        y_position += 20
        draw.text((58, y_position), "Phone: (555) 123-4567", fill=(40, 40, 40), font=fonts['small'])
        y_position += 40
        
        # RECEIPT DETAILS
        # --------------
        # Date
        order_date = data.get('date', datetime.now().strftime('%m/%d/%Y'))
        try:
            date_obj = datetime.strptime(order_date, '%m/%d/%Y')
            formatted_date = date_obj.strftime('%m/%d/%Y %I:%M %p')
        except:
            formatted_date = f"{order_date} 2:30 PM"
        
        draw.text((58, y_position), f"Date: {formatted_date}", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 25
        
        # Transaction ID
        transaction_id = data.get('order_number', f"BBY{random.randint(1000000, 9999999)}")
        draw.text((58, y_position), f"Transaction #: {transaction_id}", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 25
        
        # Associate ID (random)
        associate_id = f"A{random.randint(100000, 999999)}"
        draw.text((58, y_position), f"Associate ID: {associate_id}", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 40
        
        # SEPARATOR LINE
        draw.line([(50, y_position), (width-50, y_position)], fill=(180, 180, 180), width=1)
        y_position += 30
        
        # PURCHASED ITEMS SECTION
        # ----------------------
        draw.text((58, y_position), "PURCHASED ITEMS", fill=bb_blue, font=fonts['bold'])
        y_position += 30
        
        # Column headers
        draw.text((58, y_position), "Description", fill=(40, 40, 40), font=fonts['small_bold'])
        draw.text((width-150, y_position), "Price", fill=(40, 40, 40), font=fonts['small_bold'], anchor="ra")
        draw.text((width-70, y_position), "Total", fill=(40, 40, 40), font=fonts['small_bold'], anchor="ra")
        y_position += 20
        
        # Separator line
        draw.line([(50, y_position), (width-50, y_position)], fill=(180, 180, 180), width=1)
        y_position += 25
        
        # Product information
        if 'product' in data:
            # Product name and SKU
            product_name = data['product']
            if len(product_name) > 50:
                product_name = product_name[:47] + "..."
            
            draw.text((58, y_position), product_name, fill=(0, 0, 0), font=fonts['regular'])
            y_position += 25
            
            # Generate random SKU
            sku = f"{random.randint(1000000, 9999999)}"
            draw.text((70, y_position), f"SKU: {sku}", fill=(80, 80, 80), font=fonts['small'])
            y_position += 20
            
            # Quantity and price
            quantity = data.get('quantity', 1)
            price = data.get('price', '0.00')
            
            draw.text((70, y_position), f"Qty: {quantity}", fill=(80, 80, 80), font=fonts['small'])
            
            # Price and total calculations
            try:
                price_float = float(price)
                total = price_float * int(quantity)
                
                # Format as strings
                price_str = f"{price_float:.2f}"
                total_str = f"{total:.2f}"
            except ValueError:
                price_str = price
                total_str = price
            
            draw.text((width-150, y_position), f"${price_str}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
            draw.text((width-70, y_position), f"${total_str}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
            y_position += 40
        
        # SEPARATOR LINE
        draw.line([(50, y_position), (width-50, y_position)], fill=(180, 180, 180), width=1)
        y_position += 25
        
        # TOTAL SECTION
        # ------------
        # Calculate subtotal, tax, and total
        price = data.get('price', '0.00')
        try:
            price_float = float(price)
            subtotal = price_float
            tax = subtotal * 0.0825  # 8.25% tax
            total = subtotal + tax
            
            # Format as strings
            subtotal_str = f"{subtotal:.2f}"
            tax_str = f"{tax:.2f}"
            total_str = f"{total:.2f}"
        except ValueError:
            subtotal_str = price
            tax_str = "0.00"
            total_str = price
        
        # Display totals
        draw.text((width-150, y_position), "Subtotal:", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        draw.text((width-70, y_position), f"${subtotal_str}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        y_position += 25
        
        draw.text((width-150, y_position), "Tax:", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        draw.text((width-70, y_position), f"${tax_str}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        y_position += 25
        
        # Total line
        draw.text((width-150, y_position), "Total:", fill=(0, 0, 0), font=fonts['bold'], anchor="ra")
        draw.text((width-70, y_position), f"${total_str}", fill=(0, 0, 0), font=fonts['bold'], anchor="ra")
        y_position += 40
        
        # PAYMENT INFORMATION
        # ------------------
        draw.text((58, y_position), "PAYMENT INFORMATION", fill=bb_blue, font=fonts['bold'])
        y_position += 30
        
        # Payment method
        payment_method = data.get('payment_method', 'Visa')
        if 'xxxx' not in payment_method.lower() and 'ending in' not in payment_method.lower():
            payment_method = f"{payment_method} ending in {''.join(random.choices('0123456789', k=4))}"
        
        draw.text((58, y_position), payment_method, fill=(40, 40, 40), font=fonts['regular'])
        draw.text((width-70, y_position), f"${total_str}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        y_position += 40
        
        # CUSTOMER INFORMATION (if available)
        # -------------------
        if 'customer_name' in data or 'shipping_address' in data:
            draw.text((58, y_position), "CUSTOMER INFORMATION", fill=bb_blue, font=fonts['bold'])
            y_position += 30
            
            if 'customer_name' in data:
                draw.text((58, y_position), f"Name: {data['customer_name']}", fill=(40, 40, 40), font=fonts['regular'])
                y_position += 25
            
            if 'shipping_address' in data and data['shipping_address']:
                draw.text((58, y_position), "Address:", fill=(40, 40, 40), font=fonts['regular'])
                y_position += 20
                
                address_lines = data['shipping_address'].split('\n')
                for line in address_lines:
                    draw.text((70, y_position), line, fill=(80, 80, 80), font=fonts['small'])
                    y_position += 20
                
                y_position += 10
        
        # FOOTER
        # ------
        footer_y = height - 150
        
        # MyBestBuy info
        draw.text((width//2, footer_y), "MyBestBuy Rewards", fill=bb_blue, font=fonts['bold'], anchor="mm")
        footer_y += 25
        draw.text((width//2, footer_y), "Earn 1 point for every $1 spent", fill=(40, 40, 40), font=fonts['small'], anchor="mm")
        footer_y += 20
        draw.text((width//2, footer_y), "Visit BestBuy.com/Rewards to learn more", fill=(40, 40, 40), font=fonts['small'], anchor="mm")
        footer_y += 30
        
        # Return policy
        draw.text((width//2, footer_y), "Return Policy: 15 days for most items", fill=(40, 40, 40), font=fonts['small'], anchor="mm")
        footer_y += 20
        draw.text((width//2, footer_y), "Thank you for shopping at Best Buy!", fill=(40, 40, 40), font=fonts['small'], anchor="mm")
        
        # Save the image to a BytesIO object
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)
        
        self.logger.info(f"Best Buy receipt generated successfully")
        return img_io
    
    def _generate_walmart_receipt(self, image: Image.Image, draw: ImageDraw.Draw, 
                                data: Dict[str, Any], fonts: Dict[str, ImageFont.FreeTypeFont]) -> BytesIO:
        """Generate a Walmart-styled receipt."""
        # Create a basic Walmart receipt template
        width, height = image.size
        
        # Walmart blue
        walmart_blue = (0, 113, 206)
        
        # HEADER
        # ------
        # Walmart logo
        draw.text((width//2, 50), "Walmart", fill=walmart_blue, font=fonts['title'], anchor="mm")
        
        # Store information
        draw.text((width//2, 90), "Save money. Live better.", fill=(40, 40, 40), font=fonts['small'], anchor="mm")
        draw.text((width//2, 120), "Store #1234", fill=(40, 40, 40), font=fonts['regular'], anchor="mm")
        draw.text((width//2, 145), "123 Main Street, Anytown, USA 12345", fill=(40, 40, 40), font=fonts['small'], anchor="mm")
        draw.text((width//2, 170), "Phone: (555) 123-4567", fill=(40, 40, 40), font=fonts['small'], anchor="mm")
        
        # Draw header separator line
        draw.line([(50, 200), (width-50, 200)], fill=walmart_blue, width=1)
        
        # Current position for drawing content
        y_position = 220
        
        # RECEIPT DETAILS
        # --------------
        # Date and time
        order_date = data.get('date', datetime.now().strftime('%m/%d/%Y'))
        try:
            date_obj = datetime.strptime(order_date, '%m/%d/%Y')
            formatted_date = date_obj.strftime('%m/%d/%Y')
            formatted_time = date_obj.strftime('%I:%M:%S %p')
        except:
            formatted_date = order_date
            formatted_time = "12:00:00 PM"
        
        draw.text((58, y_position), f"Date: {formatted_date}", fill=(40, 40, 40), font=fonts['regular'])
        draw.text((width-58, y_position), f"Time: {formatted_time}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        y_position += 25
        
        # Transaction ID and cashier
        transaction_id = data.get('order_number', f"TC#{random.randint(100000000, 999999999)}")
        cashier_id = random.randint(1000, 9999)
        
        draw.text((58, y_position), f"Transaction #: {transaction_id}", fill=(40, 40, 40), font=fonts['regular'])
        draw.text((width-58, y_position), f"Cashier: {cashier_id}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        y_position += 40
        
        # PURCHASED ITEMS
        # --------------
        draw.text((width//2, y_position), "PURCHASED ITEMS", fill=walmart_blue, font=fonts['bold'], anchor="mm")
        y_position += 30
        
        # Draw a double-line separator
        draw.line([(50, y_position), (width-50, y_position)], fill=(180, 180, 180), width=1)
        y_position += 3
        draw.line([(50, y_position), (width-50, y_position)], fill=(180, 180, 180), width=1)
        y_position += 20
        
        # Product information
        if 'product' in data:
            # Product name
            product_name = data['product']
            if len(product_name) > 55:
                product_name = product_name[:52] + "..."
            
            # Generate UPC
            upc = ''.join([str(random.randint(0, 9)) for _ in range(12)])
            
            # Price and quantity
            quantity = data.get('quantity', 1)
            price = data.get('price', '0.00')
            
            try:
                price_float = float(price)
                total = price_float * int(quantity)
                
                # Format as strings
                price_str = f"{price_float:.2f}"
                total_str = f"{total:.2f}"
            except ValueError:
                price_str = price
                total_str = price
            
            # Display product info
            draw.text((58, y_position), product_name, fill=(0, 0, 0), font=fonts['regular'])
            y_position += 25
            
            draw.text((70, y_position), f"UPC: {upc}", fill=(80, 80, 80), font=fonts['small'])
            y_position += 20
            
            if int(quantity) > 1:
                draw.text((70, y_position), f"{quantity} @ ${price_str}", fill=(40, 40, 40), font=fonts['regular'])
                draw.text((width-58, y_position), f"${total_str}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
            else:
                draw.text((width-58, y_position), f"${price_str}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
            
            y_position += 40
        
        # Separator line
        draw.line([(50, y_position), (width-50, y_position)], fill=(180, 180, 180), width=1)
        y_position += 20
        
        # SUBTOTAL, TAX, AND TOTAL
        # -----------------------
        # Calculate values
        price = data.get('price', '0.00')
        try:
            price_float = float(price)
            subtotal = price_float
            tax = subtotal * 0.0625  # 6.25% tax
            total = subtotal + tax
            
            # Format as strings
            subtotal_str = f"{subtotal:.2f}"
            tax_str = f"{tax:.2f}"
            total_str = f"{total:.2f}"
        except ValueError:
            subtotal_str = price
            tax_str = "0.00"
            total_str = price
        
        # Subtotal
        draw.text((width-180, y_position), "SUBTOTAL", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        draw.text((width-58, y_position), f"${subtotal_str}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        y_position += 25
        
        # Tax
        draw.text((width-180, y_position), "TAX 6.25%", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        draw.text((width-58, y_position), f"${tax_str}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        y_position += 25
        
        # Draw a double-line separator
        draw.line([(width-220, y_position), (width-58, y_position)], fill=(180, 180, 180), width=1)
        y_position += 3
        draw.line([(width-220, y_position), (width-58, y_position)], fill=(180, 180, 180), width=1)
        y_position += 20
        
        # Total
        draw.text((width-180, y_position), "TOTAL", fill=(0, 0, 0), font=fonts['bold'], anchor="ra")
        draw.text((width-58, y_position), f"${total_str}", fill=(0, 0, 0), font=fonts['bold'], anchor="ra")
        y_position += 40
        
        # PAYMENT INFORMATION
        # ------------------
        draw.text((58, y_position), "PAYMENT INFORMATION", fill=walmart_blue, font=fonts['bold'])
        y_position += 30
        
        # Payment method
        payment_method = data.get('payment_method', 'VISA')
        if 'xxxx' not in payment_method.lower() and 'ending in' not in payment_method.lower():
            payment_method = f"{payment_method.upper()} **** **** **** {''.join(random.choices('0123456789', k=4))}"
        
        draw.text((58, y_position), payment_method, fill=(40, 40, 40), font=fonts['regular'])
        draw.text((width-58, y_position), f"${total_str}", fill=(40, 40, 40), font=fonts['regular'], anchor="ra")
        
        # Approval code
        approval_code = ''.join(random.choices('0123456789', k=6))
        y_position += 25
        draw.text((58, y_position), f"Approval: {approval_code}", fill=(40, 40, 40), font=fonts['small'])
        y_position += 40
        
        # CUSTOMER SECTION
        # ---------------
        if 'customer_name' in data or 'shipping_address' in data:
            draw.text((58, y_position), "CUSTOMER INFORMATION", fill=walmart_blue, font=fonts['bold'])
            y_position += 30
            
            if 'customer_name' in data:
                draw.text((58, y_position), f"Name: {data['customer_name']}", fill=(40, 40, 40), font=fonts['regular'])
                y_position += 25
            
            if 'shipping_address' in data and data['shipping_address']:
                draw.text((58, y_position), "Ship To:", fill=(40, 40, 40), font=fonts['regular'])
                y_position += 20
                
                address_lines = data['shipping_address'].split('\n')
                for line in address_lines:
                    draw.text((70, y_position), line, fill=(80, 80, 80), font=fonts['small'])
                    y_position += 20
        
        # FOOTER
        # ------
        footer_y = height - 120
        
        # Return policy
        draw.text((width//2, footer_y), "RETURN POLICY", fill=walmart_blue, font=fonts['small_bold'], anchor="mm")
        footer_y += 20
        draw.text((width//2, footer_y), "90 days for most items. Some electronics: 30 days.", fill=(40, 40, 40), font=fonts['small'], anchor="mm")
        footer_y += 30
        
        # Walmart slogan and thanks
        draw.text((width//2, footer_y), "Thank you for shopping at Walmart", fill=(40, 40, 40), font=fonts['regular'], anchor="mm")
        footer_y += 25
        draw.text((width//2, footer_y), "Save Money. Live Better. Walmart.", fill=walmart_blue, font=fonts['small'], anchor="mm")
        
        # Save the image to a BytesIO object
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)
        
        self.logger.info(f"Walmart receipt generated successfully")
        return img_io
    
    def _generate_default_receipt(self, image: Image.Image, draw: ImageDraw.Draw, data: Dict[str, Any], 
                                store_id: str, fonts: Dict[str, ImageFont.FreeTypeFont]) -> BytesIO:
        """Generate a default receipt template for stores without specific styling."""
        from core.config import STORES
        
        width, height = image.size
        store_info = STORES.get(store_id, {})
        store_name = store_info.get('name', 'Store')
        store_color = store_info.get('color', 0x000000)
        
        # Convert hex color to RGB tuple
        r = (store_color >> 16) & 0xFF
        g = (store_color >> 8) & 0xFF
        b = store_color & 0xFF
        color = (r, g, b)
        
        # HEADER SECTION
        # -------------
        # Store logo (text for now)
        draw.text((width//2, 50), store_name.upper(), fill=color, font=fonts['title'], anchor="mm")
        
        # Receipt title
        draw.text((width//2, 100), "Purchase Receipt", fill=(0, 0, 0), font=fonts['regular'], anchor="mm")
        
        # Draw header separator line
        draw.line([(50, 130), (width-50, 130)], fill=color, width=1)
        
        # Current position for drawing content
        y_position = 160
        
        # ORDER INFORMATION
        # ----------------
        # Date and Order ID
        order_date = data.get('date', datetime.now().strftime('%m/%d/%Y'))
        order_number = data.get('order_number', f"ORD-{random.randint(10000, 99999)}")
        
        draw.text((58, y_position), f"Date: {order_date}", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 30
        draw.text((58, y_position), f"Order #: {order_number}", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 50
        
        # CUSTOMER INFORMATION
        # -------------------
        if 'customer_name' in data:
            draw.text((58, y_position), f"Customer: {data['customer_name']}", fill=(40, 40, 40), font=fonts['regular'])
            y_position += 30
        
        # Shipping address if provided
        if 'shipping_address' in data and data['shipping_address']:
            draw.text((58, y_position), "Ship To:", fill=(40, 40, 40), font=fonts['regular'])
            y_position += 25
            
            address_lines = data['shipping_address'].split('\n')
            for line in address_lines:
                draw.text((70, y_position), line, fill=(80, 80, 80), font=fonts['small'])
                y_position += 20
            
            y_position += 10
        
        # PRODUCT SECTION
        # --------------
        # Draw separator line
        draw.line([(50, y_position), (width-50, y_position)], fill=(200, 200, 200), width=1)
        y_position += 30
        
        draw.text((58, y_position), "ORDER DETAILS", fill=color, font=fonts['bold'])
        y_position += 30
        
        # Display product information
        if 'product' in data:
            # Product name
            product_name = data['product']
            if len(product_name) > 60:
                product_name = product_name[:57] + "..."
            
            draw.text((70, y_position), product_name, fill=(0, 0, 0), font=fonts['bold'])
            y_position += 40
            
            # Price and quantity
            quantity = data.get('quantity', 1)
            price = data.get('price', '0.00')
            
            draw.text((70, y_position), f"Quantity: {quantity}", fill=(40, 40, 40), font=fonts['regular'])
            y_position += 25
            
            draw.text((70, y_position), f"Price: ${price}", fill=(40, 40, 40), font=fonts['regular'])
            y_position += 40
            
            # Calculate totals
            try:
                price_float = float(price)
                subtotal = price_float * int(quantity)
                tax = subtotal * 0.08  # 8% tax
                total = subtotal + tax
                
                # Format as strings
                subtotal_str = f"{subtotal:.2f}"
                tax_str = f"{tax:.2f}"
                total_str = f"{total:.2f}"
            except ValueError:
                subtotal_str = price
                tax_str = "0.00"
                total_str = price
            
            # Subtotal
            draw.text((70, y_position), f"Subtotal: ${subtotal_str}", fill=(40, 40, 40), font=fonts['regular'])
            y_position += 25
            
            # Tax
            draw.text((70, y_position), f"Tax: ${tax_str}", fill=(40, 40, 40), font=fonts['regular'])
            y_position += 25
            
            # Line before total
            draw.line([(70, y_position), (300, y_position)], fill=(200, 200, 200), width=1)
            y_position += 15
            
            # Total
            draw.text((70, y_position), f"Total: ${total_str}", fill=(0, 0, 0), font=fonts['bold'])
            y_position += 50
        
        # PAYMENT INFORMATION
        # ------------------
        draw.text((58, y_position), "PAYMENT INFORMATION", fill=color, font=fonts['bold'])
        y_position += 30
        
        # Payment method
        payment_method = data.get('payment_method', 'Credit Card')
        draw.text((70, y_position), f"Payment Method: {payment_method}", fill=(40, 40, 40), font=fonts['regular'])
        y_position += 40
        
        # FOOTER
        # ------
        footer_y = height - 100
        
        # Draw footer separator line
        draw.line([(50, footer_y), (width-50, footer_y)], fill=(200, 200, 200), width=1)
        footer_y += 30
        
        # Store name and thanks
        draw.text((width//2, footer_y), f"Thank you for shopping with {store_name}", fill=(40, 40, 40), font=fonts['regular'], anchor="mm")
        footer_y += 30
        
        # Contact info
        draw.text((width//2, footer_y), f"Visit {store_name.lower()}.com or call 1-800-123-4567", fill=(80, 80, 80), font=fonts['small'], anchor="mm")
        
        # Save the image to a BytesIO object
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)
        
        self.logger.info(f"Default receipt generated for {store_id}")
        return img_io
