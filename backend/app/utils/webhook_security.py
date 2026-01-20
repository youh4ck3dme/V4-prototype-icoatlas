import hmac
import hashlib
import os
from typing import Optional


def generate_webhook_signature(payload: bytes, secret: Optional[str] = None) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    webhook_secret = secret or os.getenv("WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise ValueError("WEBHOOK_SECRET not configured")
    
    signature = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={signature}"


def verify_webhook_signature(payload: bytes, signature: str, secret: Optional[str] = None) -> bool:
    """Verify HMAC-SHA256 signature of webhook payload."""
    webhook_secret = secret or os.getenv("WEBHOOK_SECRET", "")
    if not webhook_secret:
        return False
    
    expected_signature = generate_webhook_signature(payload, webhook_secret)
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature)
