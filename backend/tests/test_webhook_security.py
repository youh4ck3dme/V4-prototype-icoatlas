import pytest
import os
from backend.app.utils.webhook_security import generate_webhook_signature, verify_webhook_signature


def test_generate_webhook_signature():
    """Test webhook signature generation."""
    # Set a test secret
    test_secret = "test_secret_key_12345"
    payload = b'{"event": "test", "data": "value"}'
    
    signature = generate_webhook_signature(payload, test_secret)
    
    # Should return sha256= prefix
    assert signature.startswith("sha256=")
    # Should be hex string
    assert len(signature) > 7  # sha256= + hex


def test_generate_webhook_signature_without_secret():
    """Test that signature generation raises error without secret."""
    payload = b'{"event": "test"}'
    
    # Clear environment variable
    old_secret = os.getenv("WEBHOOK_SECRET")
    os.environ.pop("WEBHOOK_SECRET", None)
    
    try:
        with pytest.raises(ValueError, match="WEBHOOK_SECRET not configured"):
            generate_webhook_signature(payload)
    finally:
        if old_secret:
            os.environ["WEBHOOK_SECRET"] = old_secret


def test_verify_webhook_signature_valid():
    """Test webhook signature verification with valid signature."""
    test_secret = "test_secret_key_12345"
    payload = b'{"event": "test", "data": "value"}'
    
    # Generate signature
    signature = generate_webhook_signature(payload, test_secret)
    
    # Verify it
    is_valid = verify_webhook_signature(payload, signature, test_secret)
    assert is_valid is True


def test_verify_webhook_signature_invalid():
    """Test webhook signature verification with invalid signature."""
    test_secret = "test_secret_key_12345"
    payload = b'{"event": "test", "data": "value"}'
    
    # Use wrong signature
    wrong_signature = "sha256=0000000000000000000000000000000000000000000000000000000000000000"
    
    is_valid = verify_webhook_signature(payload, wrong_signature, test_secret)
    assert is_valid is False


def test_verify_webhook_signature_tampered_payload():
    """Test that signature verification fails for tampered payload."""
    test_secret = "test_secret_key_12345"
    original_payload = b'{"event": "test", "data": "value"}'
    tampered_payload = b'{"event": "test", "data": "modified"}'
    
    # Generate signature for original
    signature = generate_webhook_signature(original_payload, test_secret)
    
    # Try to verify with tampered payload
    is_valid = verify_webhook_signature(tampered_payload, signature, test_secret)
    assert is_valid is False


def test_verify_webhook_signature_different_secret():
    """Test that signature verification fails with different secret."""
    secret1 = "secret_one"
    secret2 = "secret_two"
    payload = b'{"event": "test", "data": "value"}'
    
    # Generate with secret1
    signature = generate_webhook_signature(payload, secret1)
    
    # Try to verify with secret2
    is_valid = verify_webhook_signature(payload, signature, secret2)
    assert is_valid is False


def test_verify_webhook_signature_without_secret():
    """Test that verification returns False without secret."""
    payload = b'{"event": "test"}'
    signature = "sha256=0000000000000000000000000000000000000000000000000000000000000000"
    
    # Clear environment variable
    old_secret = os.getenv("WEBHOOK_SECRET")
    os.environ.pop("WEBHOOK_SECRET", None)
    
    try:
        is_valid = verify_webhook_signature(payload, signature)
        assert is_valid is False
    finally:
        if old_secret:
            os.environ["WEBHOOK_SECRET"] = old_secret


def test_webhook_signature_consistency():
    """Test that same payload always generates same signature."""
    test_secret = "test_secret_key_12345"
    payload = b'{"event": "test", "data": "value"}'
    
    sig1 = generate_webhook_signature(payload, test_secret)
    sig2 = generate_webhook_signature(payload, test_secret)
    
    assert sig1 == sig2
