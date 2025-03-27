import re
from typing import Dict, Any, Tuple, Union, Optional
import logging

logger = logging.getLogger('validators')

# Regular expressions for validation
PRICE_REGEX = r'^\d+(\.\d{1,2})?$'
DATE_REGEX = r'^(0[1-9]|1[0-2])\/(0[1-9]|[12][0-9]|3[01])\/\d{4}$'
URL_REGEX = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$'

def validate_price(price: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if a string represents a valid price format (e.g., 99.99).
    
    Args:
        price: The price string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not re.match(PRICE_REGEX, price):
        return False, "Invalid price format. Use format like 99.99"
    return True, None

def validate_date(date: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if a string represents a valid date in MM/DD/YYYY format.
    
    Args:
        date: The date string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not re.match(DATE_REGEX, date):
        return False, "Invalid date format. Use MM/DD/YYYY"
    return True, None

def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if a string represents a valid URL.
    
    Args:
        url: The URL string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:  # Empty URL is considered valid (optional)
        return True, None
        
    if not re.match(URL_REGEX, url):
        return False, "Invalid URL format"
    return True, None

def validate_input_dict(data: Dict[str, Any], validators: Dict[str, callable]) -> Tuple[bool, Dict[str, str]]:
    """
    Validate a dictionary of input data against a dictionary of validator functions.
    
    Args:
        data: Dictionary of input data
        validators: Dictionary mapping field names to validator functions
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = {}
    
    for field, validator in validators.items():
        if field in data:
            is_valid, error = validator(data[field])
            if not is_valid:
                errors[field] = error
    
    return len(errors) == 0, errors
