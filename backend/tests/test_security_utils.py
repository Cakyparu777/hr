"""
Tests for security utilities.
"""
import pytest
from app.core.security_utils import validate_password_strength, sanitize_string, sanitize_input

def test_validate_password_strength_valid():
    """Test password strength validation with valid password."""
    is_valid, errors = validate_password_strength("StrongPass123!")
    assert is_valid is True
    assert len(errors) == 0

def test_validate_password_strength_too_short():
    """Test password strength validation with too short password."""
    is_valid, errors = validate_password_strength("Short1!")
    assert is_valid is False
    assert any("at least" in error.lower() for error in errors)

def test_validate_password_strength_no_uppercase():
    """Test password strength validation without uppercase."""
    is_valid, errors = validate_password_strength("lowercase123!")
    assert is_valid is False
    assert any("uppercase" in error.lower() for error in errors)

def test_validate_password_strength_no_digits():
    """Test password strength validation without digits."""
    is_valid, errors = validate_password_strength("NoDigits!")
    assert is_valid is False
    assert any("digit" in error.lower() for error in errors)

def test_sanitize_string():
    """Test string sanitization."""
    input_text = "  Test String  "
    result = sanitize_string(input_text)
    assert result == "Test String"

def test_sanitize_string_max_length():
    """Test string sanitization with max length."""
    input_text = "a" * 300
    result = sanitize_string(input_text, max_length=255)
    assert len(result) == 255

def test_sanitize_input():
    """Test input sanitization."""
    input_text = "<script>alert('xss')</script>Safe text"
    result = sanitize_input(input_text)
    assert "script" not in result.lower()
    assert "Safe text" in result

