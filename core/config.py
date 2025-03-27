import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
PREFIX = "!"
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "0"))  # Default to 0 if not set
COOLDOWN_SECONDS = 30  # Cooldown period for commands
MAX_REQUESTS_PER_DAY = 25  # Maximum number of receipt requests per user per day

# Store information for receipt generation
STORES: Dict[str, Dict[str, Any]] = {
    "amazon": {
        "name": "Amazon",
        "logo_url": "https://i.ibb.co/M6mBqRn/amazon-logo.png",  # Direct image URL
        "template_path": "templates/amazon_receipt.png",
        "color": 0xFF9900,  # Amazon orange
    },
    "apple": {
        "name": "Apple",
        "logo_url": "https://i.ibb.co/wWPVtrZ/apple-logo.png",  # Direct image URL 
        "template_path": "templates/apple_receipt.png",
        "color": 0x999999,  # Apple silver
    },
    "bestbuy": {
        "name": "Best Buy",
        "logo_url": "https://i.ibb.co/yVV5nTF/bestbuy-logo.png",  # Direct image URL
        "template_path": "templates/bestbuy_receipt.png",
        "color": 0x0A4BBD,  # Best Buy blue
    },
    "walmart": {
        "name": "Walmart",
        "logo_url": "https://i.ibb.co/yFKLDTq/walmart-logo.png",  # Direct image URL
        "template_path": "templates/walmart_receipt.png",
        "color": 0x0071CE,  # Walmart blue
    },
    "goat": {
        "name": "GOAT",
        "logo_url": "https://i.ibb.co/HCWfpvB/goat-logo.png",  # Direct image URL
        "template_path": "templates/goat_receipt.png",
        "color": 0x000000,  # GOAT black
    },
    "stockx": {
        "name": "StockX",
        "logo_url": "https://i.ibb.co/vq9cF5Z/stockx-logo.png",  # Direct image URL
        "template_path": "templates/stockx_receipt.png",
        "color": 0x00FF00,  # StockX green
    },
    "louisvuitton": {
        "name": "Louis Vuitton",
        "logo_url": "https://i.ibb.co/g9N3Qh1/lv-logo.png",  # Direct image URL
        "template_path": "templates/lv_receipt.png",
        "color": 0x964B00,  # LV brown
    }
}

# Validation regex patterns
PRICE_REGEX = r'^\d+(\.\d{1,2})?$'  # Valid price format (e.g., 99.99)
URL_REGEX = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$'  # Basic URL validation
DATE_REGEX = r'^(0[1-9]|1[0-2])\/(0[1-9]|[12][0-9]|3[01])\/\d{4}$'  # MM/DD/YYYY format

# Discord embed theme colors
EMBED_COLOR = 0x9B59B6  # Purple theme color
ERROR_COLOR = 0xFF0000  # Red for errors
SUCCESS_COLOR = 0x00FF00  # Green for success
WARNING_COLOR = 0xFFCC00  # Yellow for warnings

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "bot_logs.log"

# Receipt generator settings
FONT_PATH = "assets/fonts/Arial.ttf"
FONT_SIZE = 20
DEFAULT_QUANTITY = 1
DEFAULT_SHIPPING = "Standard"
DEFAULT_PAYMENT = "Visa"

# Timeout settings (in seconds)
BUTTON_TIMEOUT = 180  # 3 minutes
DROPDOWN_TIMEOUT = 180  # 3 minutes
MODAL_TIMEOUT = 300  # 5 minutes

def get_store_info(store_id: str) -> Optional[Dict[str, Any]]:
    """
    Get store information by store ID.
    
    Args:
        store_id: The ID of the store
        
    Returns:
        Store information dictionary or None if not found
    """
    return STORES.get(store_id)
