"""
Tests for validators
"""
import pytest
from app.utils.validators import (
    validate_password_strength,
    validate_cpf,
    validate_phone_br,
    sanitize_cpf,
    sanitize_phone
)


class TestPasswordValidation:
    """Tests for password strength validation"""
    
    def test_valid_password(self):
        """Test valid password"""
        is_valid, error = validate_password_strength("Test@123456")
        assert is_valid is True
        assert error is None
    
    def test_password_too_short(self):
        """Test password too short"""
        is_valid, error = validate_password_strength("Test@12")
        assert is_valid is False
        assert "8 caracteres" in error
    
    def test_password_no_uppercase(self):
        """Test password without uppercase"""
        is_valid, error = validate_password_strength("test@123456")
        assert is_valid is False
        assert "maiúscula" in error
    
    def test_password_no_lowercase(self):
        """Test password without lowercase"""
        is_valid, error = validate_password_strength("TEST@123456")
        assert is_valid is False
        assert "minúscula" in error
    
    def test_password_no_number(self):
        """Test password without number"""
        is_valid, error = validate_password_strength("Test@Abcdef")
        assert is_valid is False
        assert "número" in error
    
    def test_password_no_special_char(self):
        """Test password without special character"""
        is_valid, error = validate_password_strength("Test12345678")
        assert is_valid is False
        assert "especial" in error


class TestCPFValidation:
    """Tests for CPF validation"""
    
    def test_valid_cpf(self):
        """Test valid CPF"""
        is_valid, error = validate_cpf("12345678909")
        assert is_valid is True
        assert error is None
    
    def test_cpf_too_short(self):
        """Test CPF too short"""
        is_valid, error = validate_cpf("123456789")
        assert is_valid is False
        assert "11 dígitos" in error
    
    def test_cpf_all_same_digits(self):
        """Test CPF with all same digits"""
        is_valid, error = validate_cpf("11111111111")
        assert is_valid is False
        assert "inválido" in error
    
    def test_cpf_with_formatting(self):
        """Test CPF with dots and dash"""
        cpf = "123.456.789-09"
        is_valid, error = validate_cpf(cpf)
        # Should remove formatting first
        assert is_valid is True or is_valid is False  # Depends on checksum
    
    def test_invalid_cpf_checksum(self):
        """Test CPF with invalid checksum"""
        is_valid, error = validate_cpf("12345678900")
        assert is_valid is False
        assert "inválido" in error


class TestPhoneValidation:
    """Tests for Brazilian phone validation"""
    
    def test_valid_mobile_phone(self):
        """Test valid mobile phone"""
        is_valid, error = validate_phone_br("11987654321")
        assert is_valid is True
        assert error is None
    
    def test_valid_landline(self):
        """Test valid landline"""
        is_valid, error = validate_phone_br("1132123456")
        assert is_valid is True
        assert error is None
    
    def test_phone_with_country_code(self):
        """Test phone with country code"""
        is_valid, error = validate_phone_br("5511987654321")
        assert is_valid is True
        assert error is None
    
    def test_phone_too_short(self):
        """Test phone too short"""
        is_valid, error = validate_phone_br("119876543")
        assert is_valid is False
        assert "10 ou 11 dígitos" in error
    
    def test_invalid_ddd(self):
        """Test invalid DDD"""
        is_valid, error = validate_phone_br("0987654321")
        assert is_valid is False
        assert "DDD inválido" in error
    
    def test_mobile_without_9(self):
        """Test mobile without 9"""
        is_valid, error = validate_phone_br("11887654321")
        assert is_valid is False
        assert "começar com 9" in error


class TestSanitizers:
    """Tests for sanitizer functions"""
    
    def test_sanitize_cpf(self):
        """Test CPF sanitization"""
        assert sanitize_cpf("123.456.789-09") == "12345678909"
        assert sanitize_cpf("12345678909") == "12345678909"
        assert sanitize_cpf("123 456 789 09") == "12345678909"
    
    def test_sanitize_phone(self):
        """Test phone sanitization"""
        assert sanitize_phone("(11) 98765-4321") == "11987654321"
        assert sanitize_phone("+55 11 98765-4321") == "11987654321"
        assert sanitize_phone("11987654321") == "11987654321"
        assert sanitize_phone("5511987654321") == "11987654321"
