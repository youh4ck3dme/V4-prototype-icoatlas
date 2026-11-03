from __future__ import annotations
import logging
from typing import Dict, Any, Optional
import stripe

from ..core.config import settings

logger = logging.getLogger("icoatlas.stripe")

# Product and Tier Configuration
TIER_PRICING: Dict[str, Dict[str, Any]] = {
    "starter": {
        "name": "iCOAtlas STARTER Predplatné",
        "description": "Základné overovanie partnerov a 50 vyhľadávaní mesačne",
        "unit_amount": 999,  # 9.99 EUR in cents
        "currency": "eur",
        "interval": "month",
        "mode": "subscription"
    },
    "pro": {
        "name": "iCOAtlas PRO Predplatné",
        "description": "Neobmedzené vyhľadávanie v registroch, detailné exporty a prioritný scoring",
        "unit_amount": 1999,  # 19.99 EUR in cents
        "currency": "eur",
        "interval": "month",
        "mode": "subscription"
    },
    "enterprise": {
        "name": "iCOAtlas ENTERPRISE Predplatné",
        "description": "Kompletný API prístup, neobmedzené Nexus Intelligence reporty a forenzný OSINT",
        "unit_amount": 9999,  # 99.99 EUR in cents
        "currency": "eur",
        "interval": "month",
        "mode": "subscription"
    },
    # Credit Packages (One-time)
    "single_credit": {
        "name": "iCOAtlas Forenzný Report (1 výpis)",
        "description": "Jednorazové hĺbkové overenie subjektu a stiahnutie kompletného spisu",
        "unit_amount": 500,  # 5.00 EUR in cents
        "currency": "eur",
        "mode": "payment"
    }
}


class StripeService:
    @staticmethod
    def _ensure_api_key():
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY is not configured in backend settings.")
        stripe.api_key = settings.STRIPE_SECRET_KEY

    @classmethod
    def create_checkout_session(
        cls,
        tier: str,
        user_id: Optional[str] = None,
        customer_email: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates a modern Stripe Checkout Session supporting dynamic payment methods
        (Apple Pay, Google Pay, Credit/Debit Cards).
        """
        cls._ensure_api_key()
        tier_key = (tier or "pro").lower().strip()
        plan = TIER_PRICING.get(tier_key, TIER_PRICING["pro"])

        frontend_url = settings.FRONTEND_URL.rstrip("/")
        final_success = success_url or f"{frontend_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        final_cancel = cancel_url or f"{frontend_url}/payment/cancel"

        price_data: Dict[str, Any] = {
            "currency": plan["currency"],
            "product_data": {
                "name": plan["name"],
                "description": plan.get("description", ""),
            },
            "unit_amount": plan["unit_amount"],
        }

        if plan.get("mode") == "subscription":
            price_data["recurring"] = {
                "interval": plan.get("interval", "month")
            }

        session_params: Dict[str, Any] = {
            "line_items": [
                {
                    "price_data": price_data,
                    "quantity": 1,
                }
            ],
            "mode": plan.get("mode", "subscription"),
            "success_url": final_success,
            "cancel_url": final_cancel,
            "metadata": {
                "tier": tier_key,
                "user_id": user_id or "anonymous",
                "app": "icoatlas_v4",
            },
        }

        if customer_email:
            session_params["customer_email"] = customer_email

        logger.info(f"Creating Stripe Checkout Session for tier '{tier_key}' (email: {customer_email})")
        session = stripe.checkout.Session.create(**session_params)

        return {
            "session_id": session.id,
            "checkout_url": session.url,
            "url": session.url,
            "tier": tier_key,
            "amount": plan["unit_amount"] / 100.0,
            "currency": plan["currency"].upper()
        }

    @classmethod
    def retrieve_session(cls, session_id: str) -> Dict[str, Any]:
        """
        Retrieves checkout session state from Stripe.
        """
        cls._ensure_api_key()
        session = stripe.checkout.Session.retrieve(session_id)
        session_dict = session.to_dict() if hasattr(session, "to_dict") else {}
        
        cust_details = session_dict.get("customer_details") or {}
        email = cust_details.get("email") or session_dict.get("customer_email")

        metadata = session_dict.get("metadata") or {}
        tier = metadata.get("tier", "pro")

        amount_total = session_dict.get("amount_total")

        return {
            "id": session_dict.get("id", session.id),
            "status": session_dict.get("status", getattr(session, "status", None)),
            "payment_status": session_dict.get("payment_status", getattr(session, "payment_status", None)),
            "customer_id": session_dict.get("customer"),
            "subscription_id": session_dict.get("subscription"),
            "customer_email": email,
            "tier": tier,
            "amount_total": (amount_total / 100.0) if amount_total else 0.0,
            "currency": (session_dict.get("currency") or "eur").upper()
        }

    @classmethod
    def construct_webhook_event(cls, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Verifies signature and constructs webhook event.
        """
        cls._ensure_api_key()
        secret = settings.STRIPE_WEBHOOK_SECRET
        if not secret:
            logger.warning("STRIPE_WEBHOOK_SECRET is not configured; parsing event payload directly.")
            import json
            return json.loads(payload.decode("utf-8"))

        event = stripe.Webhook.construct_event(payload, sig_header, secret)
        return event

    @classmethod
    def create_customer_portal(cls, customer_id: str, return_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates Stripe Customer Portal session for managing subscriptions, cards and invoices.
        """
        cls._ensure_api_key()
        ret_url = return_url or f"{settings.FRONTEND_URL.rstrip('/')}/dashboard"
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=ret_url
        )
        return {
            "portal_url": portal_session.url,
            "url": portal_session.url
        }
