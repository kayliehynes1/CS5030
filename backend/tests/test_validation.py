"""
Unit tests for input validation functions.

Tests cover:
- Email validation (format, length)
- Name validation (length limits)
- Title validation (length limits)
- Notes validation (optional, length limits)
- Password validation (length requirements)
- Role validation (valid values)
- String sanitization
"""
import pytest
from fastapi import HTTPException
from app.validation import (
    validate_email,
    validate_name,
    validate_title,
    validate_notes,
    validate_password,
    validate_role,
    sanitize_string,
    MAX_NAME_LENGTH,
    MAX_TITLE_LENGTH,
    MAX_NOTES_LENGTH,
    MIN_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH
)


class TestEmailValidation:
    """Test email validation"""
    
    def test_valid_email(self):
        """Test valid email addresses"""
        valid_emails = [
            "user@example.com",
            "test.user@domain.org",
            "user+tag@company.co.uk",
            "USER@EXAMPLE.COM",  # Should be lowercased
        ]
        for email in valid_emails:
            result = validate_email(email)
            assert result == email.lower().strip()
    
    def test_invalid_email_format(self):
        """Test rejection of invalid email formats"""
        invalid_emails = [
            "not_an_email",
            "@missing_local.com",
            "missing_domain@",
            "spaces in@email.com",
            "double@@at.com",
            "no_tld@domain",
        ]
        for email in invalid_emails:
            with pytest.raises(HTTPException) as exc_info:
                validate_email(email)
            assert exc_info.value.status_code == 400
            assert "Invalid email format" in exc_info.value.detail
    
    def test_empty_email(self):
        """Test rejection of empty email"""
        with pytest.raises(HTTPException) as exc_info:
            validate_email("")
        assert exc_info.value.status_code == 400
    
    def test_email_too_long(self):
        """Test rejection of overly long email"""
        long_email = "a" * 250 + "@test.com"
        with pytest.raises(HTTPException) as exc_info:
            validate_email(long_email)
        assert exc_info.value.status_code == 400
        assert "254" in exc_info.value.detail


class TestNameValidation:
    """Test name validation"""
    
    def test_valid_name(self):
        """Test valid names"""
        assert validate_name("John Doe") == "John Doe"
        assert validate_name("  Spaced  ") == "Spaced"  # Trimmed
    
    def test_name_too_short(self):
        """Test rejection of single character name"""
        with pytest.raises(HTTPException) as exc_info:
            validate_name("A")
        assert exc_info.value.status_code == 400
        assert "at least 2 characters" in exc_info.value.detail
    
    def test_name_too_long(self):
        """Test rejection of overly long name"""
        long_name = "A" * (MAX_NAME_LENGTH + 1)
        with pytest.raises(HTTPException) as exc_info:
            validate_name(long_name)
        assert exc_info.value.status_code == 400
        assert str(MAX_NAME_LENGTH) in exc_info.value.detail
    
    def test_empty_name(self):
        """Test rejection of empty name"""
        with pytest.raises(HTTPException) as exc_info:
            validate_name("")
        assert exc_info.value.status_code == 400


class TestTitleValidation:
    """Test booking title validation"""
    
    def test_valid_title(self):
        """Test valid titles"""
        assert validate_title("Team Meeting") == "Team Meeting"
        assert validate_title("   Trimmed   ") == "Trimmed"
    
    def test_title_too_short(self):
        """Test rejection of very short title"""
        with pytest.raises(HTTPException) as exc_info:
            validate_title("AB")
        assert exc_info.value.status_code == 400
        assert "at least 3 characters" in exc_info.value.detail
    
    def test_title_too_long(self):
        """Test rejection of overly long title"""
        long_title = "A" * (MAX_TITLE_LENGTH + 1)
        with pytest.raises(HTTPException) as exc_info:
            validate_title(long_title)
        assert exc_info.value.status_code == 400
    
    def test_empty_title(self):
        """Test rejection of empty title"""
        with pytest.raises(HTTPException) as exc_info:
            validate_title("")
        assert exc_info.value.status_code == 400


class TestNotesValidation:
    """Test notes validation (optional field)"""
    
    def test_valid_notes(self):
        """Test valid notes"""
        assert validate_notes("Some notes") == "Some notes"
        assert validate_notes("   Trimmed   ") == "Trimmed"
    
    def test_empty_notes_returns_none(self):
        """Test that empty notes return None"""
        assert validate_notes("") is None
        assert validate_notes(None) is None
        assert validate_notes("   ") is None
    
    def test_notes_too_long(self):
        """Test rejection of overly long notes"""
        long_notes = "A" * (MAX_NOTES_LENGTH + 1)
        with pytest.raises(HTTPException) as exc_info:
            validate_notes(long_notes)
        assert exc_info.value.status_code == 400


class TestPasswordValidation:
    """Test password validation"""
    
    def test_valid_password(self):
        """Test valid passwords"""
        assert validate_password("password123") == "password123"
        assert validate_password("12345678") == "12345678"  # Min length
    
    def test_password_too_short(self):
        """Test rejection of short password"""
        with pytest.raises(HTTPException) as exc_info:
            validate_password("1234567")  # 7 chars
        assert exc_info.value.status_code == 400
        assert str(MIN_PASSWORD_LENGTH) in exc_info.value.detail
    
    def test_password_too_long(self):
        """Test rejection of overly long password"""
        long_password = "A" * (MAX_PASSWORD_LENGTH + 1)
        with pytest.raises(HTTPException) as exc_info:
            validate_password(long_password)
        assert exc_info.value.status_code == 400
    
    def test_empty_password(self):
        """Test rejection of empty password"""
        with pytest.raises(HTTPException) as exc_info:
            validate_password("")
        assert exc_info.value.status_code == 400


class TestRoleValidation:
    """Test role validation"""
    
    def test_valid_roles(self):
        """Test valid role values"""
        assert validate_role("attendee") == "attendee"
        assert validate_role("organiser") == "organiser"
        assert validate_role("  organiser  ") == "organiser"  # Trimmed
        # legacy alias support
        assert validate_role("student") == "attendee"
    
    def test_invalid_role(self):
        """Test rejection of invalid role"""
        with pytest.raises(HTTPException) as exc_info:
            validate_role("invalid_role")
        assert exc_info.value.status_code == 400
        assert "Invalid role" in exc_info.value.detail
    
    def test_empty_role_defaults_to_attendee(self):
        """Test that empty role defaults to attendee"""
        assert validate_role("") == "attendee"
        assert validate_role(None) == "attendee"


class TestStringSanitization:
    """Test string sanitization"""
    
    def test_removes_null_bytes(self):
        """Test that null bytes are removed"""
        result = sanitize_string("hello\x00world")
        assert "\x00" not in result
        assert "hello" in result and "world" in result
    
    def test_normalizes_whitespace(self):
        """Test that excessive whitespace is normalized"""
        assert sanitize_string("  too   many   spaces  ") == "too many spaces"
    
    def test_returns_none_for_empty(self):
        """Test that empty strings return None"""
        assert sanitize_string("") is None
        assert sanitize_string(None) is None
        assert sanitize_string("   ") is None
