"""
Security utilities for password validation and input sanitization.
"""
import re
import bleach
from typing import List, Tuple
from app.core.config import settings

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength based on configured requirements.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check minimum length
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
    
    # Check uppercase requirement
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check lowercase requirement
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check digits requirement
    if settings.PASSWORD_REQUIRE_DIGITS and not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    # Check special characters requirement
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
    
    return (len(errors) == 0, errors)


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Allow only safe HTML tags and attributes
    # For time log context, we allow basic formatting
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
    allowed_attributes = {}
    
    # Clean the HTML
    cleaned = bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return cleaned


def sanitize_string(text: str, max_length: int = 255) -> str:
    """
    Sanitize a plain string (no HTML) by removing dangerous characters.
    
    Args:
        text: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # Remove control characters except newline and tab
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

