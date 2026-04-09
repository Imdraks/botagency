"""
Public contact form endpoint (no auth required)
"""
from html import escape
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.email_service import EmailService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["contact"])


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    company: str = ""
    phone: str = ""
    plan: str = ""
    message: str


@router.post("")
async def submit_contact(data: ContactRequest):
    """Receive a contact form submission and send notification email."""
    email_service = EmailService()

    # Escape all user inputs for safe HTML rendering
    safe_name = escape(data.name)
    safe_email = escape(data.email)
    safe_company = escape(data.company) if data.company else "—"
    safe_phone = escape(data.phone) if data.phone else "—"
    safe_plan = escape(data.plan) if data.plan else "—"
    safe_message = escape(data.message)

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #7c3aed;">Nouveau message de contact — Radar</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="padding: 8px; font-weight: bold; color: #374151;">Nom</td><td style="padding: 8px;">{safe_name}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; color: #374151;">Email</td><td style="padding: 8px;">{safe_email}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; color: #374151;">Société</td><td style="padding: 8px;">{safe_company}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; color: #374151;">Téléphone</td><td style="padding: 8px;">{safe_phone}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; color: #374151;">Pack intéressé</td><td style="padding: 8px;">{safe_plan}</td></tr>
        </table>
        <div style="margin-top: 16px; padding: 16px; background: #f3f4f6; border-radius: 8px;">
            <p style="font-weight: bold; color: #374151; margin: 0 0 8px;">Message :</p>
            <p style="color: #4b5563; margin: 0; white-space: pre-wrap;">{safe_message}</p>
        </div>
    </div>
    """

    result = await email_service.send_email(
        to=settings.admin_email,
        subject=f"[Radar Contact] {data.name} — {data.company or 'Particulier'}",
        html=html,
        text=f"Nom: {data.name}\nEmail: {data.email}\nSociété: {data.company}\nTéléphone: {data.phone}\nPack: {data.plan}\n\nMessage:\n{data.message}",
    )

    if result.get("error"):
        logger.error(f"Failed to send contact email: {result}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi du message")

    logger.info(f"Contact form submitted: {data.name} <{data.email}>")
    return {"status": "ok", "message": "Message envoyé avec succès"}
