"""
Unit tests for authentication functions
"""
import pytest
from app.auth import hash_password, verify_password, create_access_token, verify_token


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test that password hashing produces different hashes for same password"""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different salts should produce different hashes
        assert len(hash1) > 0
        assert len(hash2) > 0
    
    def test_verify_correct_password(self):
        """Test verifying correct password"""
        password = "my_secure_password"
        password_hash = hash_password(password)
        
        assert verify_password(password, password_hash) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password fails verification"""
        password = "correct_password"
        wrong_password = "wrong_password"
        password_hash = hash_password(password)
        
        assert verify_password(wrong_password, password_hash) is False
    
    def test_empty_password(self):
        """Test handling of empty password"""
        password = ""
        password_hash = hash_password(password)
        
        assert verify_password(password, password_hash) is True
        assert verify_password("not_empty", password_hash) is False


class TestJWTTokens:
    """Test JWT token creation and verification"""
    
    def test_create_token(self):
        """Test token creation"""
        user_id = 1
        email = "test@example.com"
        
        token = create_access_token(user_id, email)
        
        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)
    
    def test_verify_valid_token(self):
        """Test verifying a valid token"""
        user_id = 42
        email = "user@test.com"
        
        token = create_access_token(user_id, email)
        token_data = verify_token(token)
        
        assert token_data is not None
        assert token_data.user_id == user_id
        assert token_data.email == email
    
    def test_verify_invalid_token(self):
        """Test that invalid token returns None"""
        invalid_token = "not.a.valid.token"
        
        token_data = verify_token(invalid_token)
        
        assert token_data is None
    
    def test_verify_malformed_token(self):
        """Test handling of malformed tokens"""
        malformed_tokens = [
            "",
            "malformed",
            "too.short",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        ]
        
        for token in malformed_tokens:
            result = verify_token(token)
            assert result is None, f"Token {token} should return None"

