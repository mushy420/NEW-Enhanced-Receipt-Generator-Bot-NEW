import logging
from io import BytesIO
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import os
import requests
from datetime import datetime

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
            try:
                # Look for fonts in multiple common locations
                possible_fonts = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                    "/Library/Fonts/Arial.ttf",  # macOS
                    "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                    "/usr/share/fonts/TTF/DejaVuSans.ttf",  # Another Linux path
                    "arial.ttf"  # Fallback
                ]
                font_path = next(font for font in possible_fonts if os.path.exists(font))
                
                # Create different font sizes
                title_font = ImageFont.truetype(font_path, 28)
                regular_font = ImageFont.truetype(font_path, 20)
                small_font = ImageFont.truetype(font_path, 16)
                bold_font_path = next((font for font in [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "/Library/Fonts/Arial Bold.ttf",
                    "C:\\Windows\\Fonts\\arialbd.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
                ] if os.path.exists(font)), font_path)
                bold_font = ImageFont.truetype(bold_font_path, 20)
                
            except (IOError, StopIteration):
                # Absolute fallback to default font
                title_font = ImageFont.load_default()
                regular_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
                bold_font = ImageFont.load_default()
            
            # Create a new image with white background
            width, height = 800, 1100
            
            # For Amazon, use a light cream background
            background_color = (255, 255, 255)  # White for basic template
            if store_id == 'amazon':
                background_color = (252, 252, 248)  # Light cream for Amazon
            
            image = Image.new('RGB', (width, height), color=background_color)
            draw = ImageDraw.Draw(image)
            
            # Use store-specific template
            if store_id == 'amazon':
                return self._generate_amazon_receipt(image, draw, data, {
                    'title': title_font,
                    'regular': regular_font,
                    'small': small_font,
                    'bold': bold_font
                })
            elif store_id == 'apple':
                # Add Apple-specific styling here in the future
                pass
            
            # Default template for any other store
            return self._generate_default_receipt(image, draw, data, store_id, {
                'title': title_font,
                'regular': regular_font,
                'small': small_font,
                'bold': bold_font
            })
            
        except Exception as e:
            self.logger.error(f"Error generating receipt: {str(e)}", exc_info=True)
            return None
    
    def _generate_amazon_receipt(self, image: Image.Image, draw: ImageDraw.Draw, 
                               data: Dict[str, Any], fonts: Dict[str, ImageFont.FreeTypeFont]) -> BytesIO:
        """Generate an Amazon-styled receipt."""
        width, height = image.size
        
        # Header with Amazon logo
        # We'll use text for now, but could use an actual logo image
        draw.text((width//2, 60), "Amazon", fill=(0, 0, 0), font=fonts['title'], anchor="mm")
        # Amazon smile underline
        draw.arc([(width//2 - 60, 70), (width//2 + 60, 90)], 0, 180, fill=(255, 153, 0), width=2)
        
        # Add "Order Confirmation" text
        draw.text((width - 100, 60), "Order Confirmation", fill=(0, 0, 0), font=fonts['regular'], anchor="mm")
        
        # Draw header separator line
        draw.line([(50, 110), (width-50, 110)], fill=(200, 200, 200), width=2)
        
        # Current position for drawing content
        y_position = 150
        
        # Add greeting if customer name is provided
        if 'customer_name' in data:
            draw.text((50, y_position), f"Hello {data['customer_name']},", fill=(230, 125, 35), font=fonts['regular'])
            y_position += 40
            draw.text((50, y_position), "Thank you for shopping with us.", fill=(80, 80, 80), font=fonts['small'])
            y_position += 40
        else:
            # Just add the thank you message
            draw.text((50, y_position), "Thank you for shopping with us.", fill=(80, 80, 80), font=fonts['small'])
            y_position += 40
        
        # Draw a separator line
        draw.line([(50, y_position), (width-50, y_position)], fill=(200, 200, 200), width=1)
        y_position += 20
        
        # Order Details section
        draw.text((50, y_position), "Order Details", fill=(230, 125, 35), font=fonts['regular'])
        y_position += 40
        
        # Order number and date
        order_number = data.get('order_number', '000000')
        order_date = data.get('date', datetime.now().strftime('%m/%d/%Y'))
        
        # Format order number with Amazon style (D01-XXXXXXX-XXXXXXX)
        if len(order_number) <= 6:
            formatted_order_number = f"D01-{order_number.zfill(7)}-{str(hash(order_number))[-7:]}"
        else:
            formatted_order_number = f"D01-{order_number[:7]}-{order_number[-7:]}"
        
        draw.text((50, y_position), f"Order #{formatted_order_number}", fill=(0, 0, 0), font=fonts['regular'])
        y_position += 30
        draw.text((50, y_position), f"Placed on {order_date}", fill=(80, 80, 80), font=fonts['small'])
        y_position += 40
        
        # Add a "View order details" button
        button_coords = [(50, y_position), (300, y_position + 40)]
        draw.rectangle(button_coords, fill=(255, 200, 80))
        button_center = ((button_coords[0][0] + button_coords[1][0]) // 2, 
                         (button_coords[0][1] + button_coords[1][1]) // 2)
        draw.text(button_center, "View order details", fill=(0, 0, 0), font=fonts['small'], anchor="mm")
        
        # Add price information on the right
        price = data.get('price', '0.00')
        
        # Right aligned price information
        right_x = width - 50
        draw.text((right_x, y_position), f"Item Subtotal: ${price}", fill=(0, 0, 0), 
                 font=fonts['small'], anchor="ra")
        y_position += 25
        
        # Calculate tax (approx 8.5%)
        try:
            tax = float(price) * 0.085
            tax_str = f"{tax:.2f}"
        except ValueError:
            tax_str = "0.00"
            
        draw.text((right_x, y_position), f"Total Before Tax: ${price}", fill=(0, 0, 0), 
                 font=fonts['small'], anchor="ra")
        y_position += 25
        draw.text((right_x, y_position), f"Tax Collected: ${tax_str}", fill=(0, 0, 0), 
                 font=fonts['small'], anchor="ra")
        y_position += 25
        
        # Calculate grand total
        try:
            grand_total = float(price) + float(tax_str)
            grand_total_str = f"{grand_total:.2f}"
        except ValueError:
            grand_total_str = price
            
        draw.text((right_x, y_position), f"Grand Total: ${grand_total_str}", fill=(0, 0, 0), 
                 font=fonts['bold'], anchor="ra")
        
        y_position += 60
        
        # Draw a separator line
        draw.line([(50, y_position), (width-50, y_position)], fill=(200, 200, 200), width=1)
        y_position += 30
        
        # Add more Amazon-specific text
        draw.text((50, y_position), "We hope to see you again soon!", fill=(80, 80, 80), font=fonts['small'])
        y_position += 30
        draw.text((50, y_position), "Amazon.com", fill=(0, 0, 0), font=fonts['bold'])
        y_position += 60
        
        # Items from your list section
        draw.text((50, y_position), "Items from Your List", fill=(230, 125, 35), font=fonts['regular'])
        y_position += 40
        
        # Product details with a light gray background
        product_section = [(50, y_position), (width-50, y_position + 150)]
        draw.rectangle(product_section, fill=(245, 245, 245))
        
        # Center the product in the product section
        product_center_y = (product_section[0][1] + product_section[1][1]) // 2
        
        # Product name and price
        if 'product' in data:
            # Truncate product name if too long
            product_name = data['product']
            if len(product_name) > 60:
                product_name = product_name[:57] + "..."
                
            draw.text((70, product_center_y - 30), product_name, fill=(0, 0, 0), font=fonts['small'])
            
            # Price below the product name
            if 'price' in data:
                draw.text((70, product_center_y + 10), f"${price}", fill=(0, 0, 0), font=fonts['regular'])
        
        # Shipping Address section (if provided)
        if 'shipping_address' in data and data['shipping_address']:
            y_position = product_section[1][1] + 40
            draw.text((50, y_position), "Shipping Address:", fill=(0, 0, 0), font=fonts['regular'])
            y_position += 30
            
            # Split address into lines
            address_lines = data['shipping_address'].split('\n')
            for line in address_lines:
                draw.text((70, y_position), line, fill=(80, 80, 80), font=fonts['small'])
                y_position += 25
        
        # Save the image to a BytesIO object
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)
        
        self.logger.info(f"Amazon receipt generated successfully")
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
