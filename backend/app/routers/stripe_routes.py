from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import stripe

from ..db import get_db
from ..deps import get_current_user
from ..config import settings

router = APIRouter(prefix="/subscriptions", tags=["stripe"])

def _stripe_ready() -> bool:
    return bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_PRICE_ID)

@router.post("/create-checkout-session")
def create_checkout_session(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not _stripe_ready():
        raise HTTPException(status_code=400, detail="Stripe not configured for this deployment")
    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
        customer_email=user.email,
        success_url="http://localhost:5173/success",
        cancel_url="http://localhost:5173/billing",
    )
    return {"url": session.url}

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    if not (settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="Stripe webhook not configured")
    stripe.api_key = settings.STRIPE_SECRET_KEY

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    # MVP: you can expand this to update `subscriptions` table
    return {"received": True, "type": event["type"]}
