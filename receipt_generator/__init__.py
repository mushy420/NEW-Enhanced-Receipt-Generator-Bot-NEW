import logging
from io import BytesIO
from typing import Dict, Any, Optional

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
            
            # For now, this is a placeholder that creates a dummy image
            # In a real implementation, this would create a proper receipt image
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create a new image with white background
            width, height = 800, 1200
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # Try to load a font, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 20)
                small_font = ImageFont.truetype("arial.ttf", 15)
            except IOError:
                # Use default font if arial.ttf is not available
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Draw store name at the top
            store_name = data.get('store_name', f"Receipt for {store_id.capitalize()}")
            draw.text((width//2, 50), store_name, fill=(0, 0, 0), font=font, anchor="mt")
            
            # Draw a line separator
            draw.line([(50, 100), (width-50, 100)], fill=(0, 0, 0), width=2)
            
            # Draw customer info
            y_position = 150
            
            # Customer name
            if 'full_name' in data:
                draw.text((50, y_position), f"Customer: {data['full_name']}", fill=(0, 0, 0), font=font)
                y_position += 30
            
            # Date
            if 'date' in data:
                draw.text((50, y_position), f"Date: {data['date']}", fill=(0, 0, 0), font=font)
                y_position += 30
            
            # Draw a line separator
            draw.line([(50, y_position), (width-50, y_position)], fill=(0, 0, 0), width=1)
            y_position += 20
            
            # Draw product details
            if 'product' in data:
                draw.text((50, y_position), f"Product: {data['product']}", fill=(0, 0, 0), font=font)
                y_position += 30
            
            # Price
            if 'price' in data and 'currency' in data:
                currency = data.get('currency', '$')
                draw.text((50, y_position), f"Price: {currency}{data['price']}", fill=(0, 0, 0), font=font)
                y_position += 30
            
            # Shipping cost
            if 'shipping_cost' in data and 'currency' in data:
                currency = data.get('currency', '$')
                cost = data.get('shipping_cost', '0.00')
                draw.text((50, y_position), f"Shipping: {currency}{cost}", fill=(0, 0, 0), font=font)
                y_position += 30
            
            # Calculate and show total
            if 'price' in data and 'shipping_cost' in data:
                try:
                    price = float(data['price'])
                    shipping = float(data.get('shipping_cost', '0.00'))
                    total = price + shipping
                    currency = data.get('currency', '$')
                    draw.text((50, y_position), f"Total: {currency}{total:.2f}", fill=(0, 0, 0), font=font)
                    y_position += 40
                except ValueError:
                    # Skip if price is not a valid number
                    pass
            
            # Draw shipping address
            if 'shipping_address' in data:
                draw.text((50, y_position), "Shipping Address:", fill=(0, 0, 0), font=font)
                y_position += 25
                
                address_lines = data['shipping_address'].split('\n')
                for line in address_lines:
                    draw.text((70, y_position), line, fill=(0, 0, 0), font=small_font)
                    y_position += 20
            
            # Draw billing address if different
            if 'billing_address' in data and data.get('billing_address') != data.get('shipping_address'):
                y_position += 10
                draw.text((50, y_position), "Billing Address:", fill=(0, 0, 0), font=font)
                y_position += 25
                
                address_lines = data['billing_address'].split('\n')
                for line in address_lines:
                    draw.text((70, y_position), line, fill=(0, 0, 0), font=small_font)
                    y_position += 20
            
            # Draw a thank you message at the bottom
            draw.text((width//2, height-100), "Thank you for your purchase!", fill=(0, 0, 0), font=font, anchor="mt")
            
            # Save the image to a BytesIO object
            img_io = BytesIO()
            image.save(img_io, format='PNG')
            img_io.seek(0)
            
            self.logger.info(f"Receipt generation successful for {store_id}")
            return img_io
            
        except Exception as e:
            self.logger.error(f"Error generating receipt: {str(e)}", exc_info=True)
            return None
