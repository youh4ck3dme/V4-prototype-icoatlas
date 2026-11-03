from __future__ import annotations
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query, Header
from pydantic import BaseModel

from ...services.stripe_service import StripeService, TIER_PRICING
from ...core.config import settings

logger = logging.getLogger("icoatlas.payment")
router = APIRouter(prefix="/payment", tags=["payment"])


class CheckoutRequest(BaseModel):
    tier: Optional[str] = "pro"
    customer_email: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@router.get("/config", summary="Získanie verejných Stripe parametrov")
async def get_payment_config():
    return {
        "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "mode": "live" if (settings.STRIPE_SECRET_KEY or "").startswith("rk_live") or (settings.STRIPE_SECRET_KEY or "").startswith("sk_live") else "test",
    }


@router.get("/pricing", summary="Zoznam dostupných predplatiteľských balíčkov")
async def get_pricing_plans():
    return {
        "currency": "EUR",
        "plans": [
            {
                "tier": k,
                "name": v["name"],
                "description": v["description"],
                "price_eur": v["unit_amount"] / 100.0,
                "interval": v.get("interval", "one_time"),
                "mode": v.get("mode", "subscription")
            }
            for k, v in TIER_PRICING.items()
        ]
    }


@router.post("/checkout", summary="Vytvorenie Stripe Checkout Session")
async def create_checkout(
    tier: Optional[str] = Query(None),
    body: Optional[CheckoutRequest] = None,
    authorization: Optional[str] = Header(None)
):
    selected_tier = (tier or (body.tier if body else None) or "pro").lower().strip()
    customer_email = body.customer_email if body else None
    user_id = None

    # Extract user email from token if provided
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split("Bearer ")[-1].strip()
            # If standard decode or JWT payload is present
            import base64, json
            parts = token.split(".")
            if len(parts) >= 2:
                payload_str = base64.b64decode(parts[1] + "==").decode("utf-8")
                payload = json.loads(payload_str)
                user_id = str(payload.get("sub") or payload.get("id") or "")
                if not customer_email and payload.get("email"):
                    customer_email = payload["email"]
        except Exception:
            pass

    try:
        session_data = StripeService.create_checkout_session(
            tier=selected_tier,
            user_id=user_id,
            customer_email=customer_email,
            success_url=body.success_url if body else None,
            cancel_url=body.cancel_url if body else None
        )
        return session_data
    except Exception as e:
        logger.error(f"Failed to create Stripe Checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Chyba pri inicializácii platobnej brány: {str(e)}")


@router.get("/verify-session/{session_id}", summary="Overenie stavu platby po presmerovaní")
async def verify_session(session_id: str):
    try:
        status_data = StripeService.retrieve_session(session_id)
        return status_data
    except Exception as e:
        logger.error(f"Failed to retrieve Stripe session {session_id}: {e}")
        raise HTTPException(status_code=404, detail="Platobná relácia sa nenašla.")


@router.post("/portal", summary="Zákaznícky portál na správu predplatného a kariet")
async def open_customer_portal(
    customer_id: str = Query(...),
    return_url: Optional[str] = None
):
    try:
        portal = StripeService.create_customer_portal(customer_id, return_url)
        return portal
    except Exception as e:
        logger.error(f"Failed to create customer portal session: {e}")
        raise HTTPException(status_code=500, detail="Chyba pri otvorení zákazníckeho portálu.")


@router.post("/webhook", summary="Stripe Webhook prijímač udalostí")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    payload = await request.body()
    try:
        event = StripeService.construct_webhook_event(payload, stripe_signature or "")
        event_type = event.get("type") if isinstance(event, dict) else getattr(event, "type", "")
        data_obj = event.get("data", {}).get("object", {}) if isinstance(event, dict) else getattr(getattr(event, "data", None), "object", {})

        logger.info(f"Received Stripe webhook event: {event_type}")

        if event_type == "checkout.session.completed":
            metadata = data_obj.get("metadata", {}) if isinstance(data_obj, dict) else getattr(data_obj, "metadata", {})
            customer = data_obj.get("customer") if isinstance(data_obj, dict) else getattr(data_obj, "customer", "")
            subscription = data_obj.get("subscription") if isinstance(data_obj, dict) else getattr(data_obj, "subscription", "")
            tier = metadata.get("tier", "pro")
            user_id = metadata.get("user_id")

            logger.info(f"Payment completed! Upgraded user '{user_id}' to tier '{tier}' (Customer: {customer}, Sub: {subscription})")

        elif event_type == "customer.subscription.deleted":
            customer = data_obj.get("customer") if isinstance(data_obj, dict) else getattr(data_obj, "customer", "")
            logger.info(f"Subscription deleted for customer '{customer}'. Downgrading to free tier.")

        return {"received": True, "event": event_type}
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
