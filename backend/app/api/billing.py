"""
Billing API endpoints for quotes (devis) and invoices (factures)
Part of Radar Business add-on
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user, get_current_workspace_id
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.db.models.billing import (
    BillingClient, Quote, QuoteItem, Invoice, InvoiceItem,
    QuoteStatus, InvoiceStatus, PaymentMethod
)
from app.db.models.agency import Client as CRMClient
from app.schemas.billing import (
    ClientCreate, ClientUpdate, ClientResponse,
    QuoteCreate, QuoteUpdate, QuoteResponse, QuoteListResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListResponse,
    InvoicePaymentUpdate, QuoteToInvoiceCreate, BillingDashboard,
    QuoteItemCreate, InvoiceItemCreate
)

router = APIRouter()


# ============ Emitter Info Schema ============

class EmitterInfo(BaseModel):
    """Workspace billing/emitter info for documents"""
    legal_name: Optional[str] = None
    legal_address: Optional[str] = None
    legal_city: Optional[str] = None
    legal_postal_code: Optional[str] = None
    legal_country: Optional[str] = "France"
    legal_phone: Optional[str] = None
    legal_email: Optional[str] = None
    siret: Optional[str] = None
    vat_number: Optional[str] = None
    logo_drive_file_id: Optional[str] = None
    payment_info: Optional[dict] = None
    # Template IDs
    devis_template_doc_id: Optional[str] = None
    facture_template_doc_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class EmitterInfoUpdate(BaseModel):
    """Update emitter info"""
    legal_name: Optional[str] = None
    legal_address: Optional[str] = None
    legal_city: Optional[str] = None
    legal_postal_code: Optional[str] = None
    legal_country: Optional[str] = None
    legal_phone: Optional[str] = None
    legal_email: Optional[str] = None
    siret: Optional[str] = None
    vat_number: Optional[str] = None
    logo_drive_file_id: Optional[str] = None
    payment_info: Optional[dict] = None
    devis_template_doc_id: Optional[str] = None
    facture_template_doc_id: Optional[str] = None


# ============ Helper Functions ============

def generate_quote_reference(db: Session, workspace_id: int) -> str:
    """Generate unique quote reference: DEV-YYYY-XXXX"""
    year = datetime.now().year
    prefix = f"DEV-{year}-"
    
    # Get the last quote number for this workspace and year
    last_quote = db.query(Quote).filter(
        Quote.workspace_id == workspace_id,
        Quote.reference.like(f"{prefix}%")
    ).order_by(Quote.id.desc()).first()
    
    if last_quote:
        try:
            last_num = int(last_quote.reference.split("-")[-1])
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1
    
    return f"{prefix}{new_num:04d}"


def generate_invoice_reference(db: Session, workspace_id: int) -> str:
    """Generate unique invoice reference: FAC-YYYY-XXXX"""
    year = datetime.now().year
    prefix = f"FAC-{year}-"
    
    last_invoice = db.query(Invoice).filter(
        Invoice.workspace_id == workspace_id,
        Invoice.reference.like(f"{prefix}%")
    ).order_by(Invoice.id.desc()).first()
    
    if last_invoice:
        try:
            last_num = int(last_invoice.reference.split("-")[-1])
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1
    
    return f"{prefix}{new_num:04d}"


def calculate_quote_totals(quote: Quote):
    """Calculate and update quote totals"""
    subtotal = sum(item.line_total for item in quote.items)
    discount_amount = subtotal * (quote.discount_percent / 100)
    after_discount = subtotal - discount_amount
    tax_amount = after_discount * (quote.tax_rate / 100)
    total = after_discount + tax_amount
    
    quote.subtotal = subtotal
    quote.discount_amount = discount_amount
    quote.tax_amount = tax_amount
    quote.total = total


def calculate_invoice_totals(invoice: Invoice):
    """Calculate and update invoice totals"""
    subtotal = sum(item.line_total for item in invoice.items)
    discount_amount = subtotal * (invoice.discount_percent / 100)
    after_discount = subtotal - discount_amount
    tax_amount = after_discount * (invoice.tax_rate / 100)
    total = after_discount + tax_amount
    
    invoice.subtotal = subtotal
    invoice.discount_amount = discount_amount
    invoice.tax_amount = tax_amount
    invoice.total = total


# ============ Emitter (Workspace Billing Info) Endpoints ============

@router.get("/emitter", response_model=EmitterInfo)
async def get_emitter_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Get workspace emitter/billing info for documents"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace non trouvé")
    
    return EmitterInfo(
        legal_name=workspace.legal_name or workspace.name,
        legal_address=workspace.legal_address,
        legal_city=workspace.legal_city,
        legal_postal_code=workspace.legal_postal_code,
        legal_country=workspace.legal_country or "France",
        legal_phone=workspace.legal_phone,
        legal_email=workspace.legal_email or workspace.billing_email,
        siret=workspace.siret,
        vat_number=workspace.vat_number,
        logo_drive_file_id=workspace.logo_drive_file_id,
        payment_info=workspace.payment_info,
        devis_template_doc_id=workspace.devis_template_doc_id,
        facture_template_doc_id=workspace.facture_template_doc_id,
    )


@router.patch("/emitter", response_model=EmitterInfo)
async def update_emitter_info(
    emitter_in: EmitterInfoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Update workspace emitter/billing info (Admin only)"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace non trouvé")
    
    # TODO: Check if user is admin
    
    update_data = emitter_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)
    
    db.commit()
    db.refresh(workspace)
    
    return EmitterInfo(
        legal_name=workspace.legal_name or workspace.name,
        legal_address=workspace.legal_address,
        legal_city=workspace.legal_city,
        legal_postal_code=workspace.legal_postal_code,
        legal_country=workspace.legal_country or "France",
        legal_phone=workspace.legal_phone,
        legal_email=workspace.legal_email or workspace.billing_email,
        siret=workspace.siret,
        vat_number=workspace.vat_number,
        logo_drive_file_id=workspace.logo_drive_file_id,
        payment_info=workspace.payment_info,
        devis_template_doc_id=workspace.devis_template_doc_id,
        facture_template_doc_id=workspace.facture_template_doc_id,
    )


# ============ Client Endpoints ============

@router.get("/clients", response_model=List[ClientResponse])
async def list_clients(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """List all clients for the workspace (from both BillingClient and CRM Client)"""
    results = []
    
    # Get BillingClients
    billing_query = db.query(BillingClient).filter(BillingClient.workspace_id == workspace_id)
    if search:
        billing_query = billing_query.filter(
            or_(
                BillingClient.name.ilike(f"%{search}%"),
                BillingClient.email.ilike(f"%{search}%"),
                BillingClient.company_name.ilike(f"%{search}%")
            )
        )
    results.extend(billing_query.all())
    
    # Get CRM Clients and convert to ClientResponse format
    crm_query = db.query(CRMClient).filter(CRMClient.workspace_id == workspace_id)
    if search:
        crm_query = crm_query.filter(CRMClient.name.ilike(f"%{search}%"))
    
    for crm_client in crm_query.all():
        # Check if already exists in BillingClient (by name match)
        exists = any(bc.name == crm_client.name or bc.company_name == crm_client.name for bc in results)
        if not exists:
            # Extract first contact email/phone if available
            email = None
            phone = None
            if crm_client.contacts and len(crm_client.contacts) > 0:
                first_contact = crm_client.contacts[0]
                email = first_contact.get('email')
                phone = first_contact.get('phone')
            
            # Create a fake BillingClient object for response
            fake_client = type('obj', (object,), {
                'id': crm_client.id + 100000,  # Offset ID to avoid collision
                'workspace_id': crm_client.workspace_id,
                'name': crm_client.name,
                'company_name': crm_client.name,
                'email': email,
                'phone': phone,
                'address': None,
                'city': None,
                'postal_code': None,
                'country': 'France',
                'siret': None,
                'vat_number': None,
                'notes': crm_client.notes,
                'created_at': crm_client.created_at,
                'updated_at': crm_client.updated_at,
            })()
            results.append(fake_client)
    
    # Sort by name
    results.sort(key=lambda x: (x.company_name or x.name or '').lower())
    return results


@router.post("/clients", response_model=ClientResponse)
async def create_client(
    client_in: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Create a new client"""
    client = BillingClient(
        workspace_id=workspace_id,
        **client_in.model_dump()
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Get a specific client"""
    client = db.query(BillingClient).filter(
        BillingClient.id == client_id,
        BillingClient.workspace_id == workspace_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    return client


@router.patch("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_in: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Update a client"""
    client = db.query(BillingClient).filter(
        BillingClient.id == client_id,
        BillingClient.workspace_id == workspace_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    update_data = client_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    return client


@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Delete a client"""
    client = db.query(BillingClient).filter(
        BillingClient.id == client_id,
        BillingClient.workspace_id == workspace_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    # Check if client has quotes or invoices
    if client.quotes or client.invoices:
        raise HTTPException(
            status_code=400, 
            detail="Impossible de supprimer un client avec des devis ou factures"
        )
    
    db.delete(client)
    db.commit()
    return {"message": "Client supprimé"}


# ============ Quote Endpoints ============

@router.get("/quotes", response_model=QuoteListResponse)
async def list_quotes(
    status: Optional[QuoteStatus] = None,
    client_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """List all quotes for the workspace"""
    query = db.query(Quote).filter(Quote.workspace_id == workspace_id)
    
    if status:
        query = query.filter(Quote.status == status)
    if client_id:
        query = query.filter(Quote.client_id == client_id)
    if search:
        query = query.filter(
            or_(
                Quote.reference.ilike(f"%{search}%"),
                Quote.title.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    quotes = query.options(
        joinedload(Quote.billing_client),
        joinedload(Quote.items)
    ).order_by(Quote.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return QuoteListResponse(
        items=quotes,
        total=total,
        page=page,
        size=size
    )


@router.post("/quotes", response_model=QuoteResponse)
async def create_quote(
    quote_in: QuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Create a new quote"""
    quote = Quote(
        workspace_id=workspace_id,
        reference=generate_quote_reference(db, workspace_id),
        created_by_id=current_user.id,
        title=quote_in.title,
        description=quote_in.description,
        client_id=quote_in.client_id,
        opportunity_id=quote_in.opportunity_id,
        issue_date=quote_in.issue_date,
        validity_date=quote_in.validity_date,
        tax_rate=quote_in.tax_rate,
        discount_percent=quote_in.discount_percent,
        terms=quote_in.terms,
        notes=quote_in.notes,
        status=QuoteStatus.DRAFT
    )
    db.add(quote)
    db.flush()
    
    # Add items
    for idx, item_data in enumerate(quote_in.items):
        line_total = item_data.quantity * item_data.unit_price
        item = QuoteItem(
            quote_id=quote.id,
            position=item_data.position or idx,
            description=item_data.description,
            quantity=item_data.quantity,
            unit=item_data.unit,
            unit_price=item_data.unit_price,
            line_total=line_total
        )
        db.add(item)
    
    db.flush()
    
    # Refresh to get items
    db.refresh(quote)
    calculate_quote_totals(quote)
    
    db.commit()
    db.refresh(quote)
    
    return quote


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Get a specific quote"""
    quote = db.query(Quote).options(
        joinedload(Quote.billing_client),
        joinedload(Quote.items)
    ).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    return quote


@router.patch("/quotes/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: int,
    quote_in: QuoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Update a quote"""
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote.status == QuoteStatus.INVOICED:
        raise HTTPException(status_code=400, detail="Impossible de modifier un devis déjà facturé")
    
    update_data = quote_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quote, field, value)
    
    calculate_quote_totals(quote)
    db.commit()
    db.refresh(quote)
    
    return quote


@router.post("/quotes/{quote_id}/items", response_model=QuoteResponse)
async def add_quote_item(
    quote_id: int,
    item_in: QuoteItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Add an item to a quote"""
    quote = db.query(Quote).options(
        joinedload(Quote.items)
    ).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote.status == QuoteStatus.INVOICED:
        raise HTTPException(status_code=400, detail="Impossible de modifier un devis facturé")
    
    line_total = item_in.quantity * item_in.unit_price
    item = QuoteItem(
        quote_id=quote.id,
        position=item_in.position,
        description=item_in.description,
        quantity=item_in.quantity,
        unit=item_in.unit,
        unit_price=item_in.unit_price,
        line_total=line_total
    )
    db.add(item)
    db.flush()
    
    db.refresh(quote)
    calculate_quote_totals(quote)
    db.commit()
    db.refresh(quote)
    
    return quote


@router.delete("/quotes/{quote_id}/items/{item_id}")
async def delete_quote_item(
    quote_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Delete an item from a quote"""
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    item = db.query(QuoteItem).filter(
        QuoteItem.id == item_id,
        QuoteItem.quote_id == quote_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    
    db.delete(item)
    db.flush()
    
    db.refresh(quote)
    calculate_quote_totals(quote)
    db.commit()
    
    return {"message": "Ligne supprimée"}


class QuoteItemUpdate(BaseModel):
    """Update quote item"""
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None


@router.patch("/quotes/{quote_id}/items/{item_id}")
async def update_quote_item(
    quote_id: int,
    item_id: int,
    item_in: QuoteItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Update an item in a quote"""
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote.status == QuoteStatus.INVOICED:
        raise HTTPException(status_code=400, detail="Impossible de modifier un devis facturé")
    
    item = db.query(QuoteItem).filter(
        QuoteItem.id == item_id,
        QuoteItem.quote_id == quote_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    
    # Update fields
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    # Recalculate line total
    item.line_total = item.quantity * item.unit_price
    
    db.flush()
    db.refresh(quote)
    calculate_quote_totals(quote)
    db.commit()
    
    return {"message": "Ligne mise à jour", "item": {
        "id": item.id,
        "description": item.description,
        "quantity": item.quantity,
        "unit": item.unit,
        "unit_price": float(item.unit_price),
        "line_total": float(item.line_total)
    }}


@router.delete("/quotes/{quote_id}")
async def delete_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Delete a quote"""
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote.status == QuoteStatus.INVOICED:
        raise HTTPException(status_code=400, detail="Impossible de supprimer un devis facturé")
    
    db.delete(quote)
    db.commit()
    return {"message": "Devis supprimé"}


@router.post("/quotes/{quote_id}/convert", response_model=InvoiceResponse)
async def convert_quote_to_invoice(
    quote_id: int,
    conversion: QuoteToInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Convert a quote to an invoice"""
    quote = db.query(Quote).options(
        joinedload(Quote.items),
        joinedload(Quote.billing_client)
    ).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote.status == QuoteStatus.INVOICED:
        raise HTTPException(status_code=400, detail="Ce devis a déjà été converti en facture")
    
    if quote.status != QuoteStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="Seuls les devis acceptés peuvent être convertis")
    
    # Create invoice
    invoice = Invoice(
        workspace_id=workspace_id,
        reference=generate_invoice_reference(db, workspace_id),
        created_by_id=current_user.id,
        client_id=quote.client_id,
        opportunity_id=quote.opportunity_id,
        source_quote_id=quote.id,
        title=quote.title,
        description=quote.description,
        issue_date=date.today(),
        due_date=conversion.due_date,
        tax_rate=quote.tax_rate,
        discount_percent=quote.discount_percent,
        terms=quote.terms,
        notes=conversion.notes or quote.notes,
        status=InvoiceStatus.DRAFT
    )
    db.add(invoice)
    db.flush()
    
    # Copy items
    for item in quote.items:
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            position=item.position,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            line_total=item.line_total
        )
        db.add(invoice_item)
    
    db.flush()
    db.refresh(invoice)
    calculate_invoice_totals(invoice)
    
    # Update quote status
    quote.status = QuoteStatus.INVOICED
    quote.invoice_id = invoice.id
    
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.get("/quotes/{quote_id}/pdf")
async def generate_quote_pdf(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Generate professional PDF for a quote"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfgen import canvas
    
    quote = db.query(Quote).options(
        joinedload(Quote.billing_client),
        joinedload(Quote.items)
    ).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    # Get workspace for emitter info
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    # Calculs
    subtotal = float(quote.subtotal or 0)
    discount_pct = float(quote.discount_percent or 0)
    discount_amt = float(quote.discount_amount or 0)
    tax_rate = float(quote.tax_rate or 20)
    tax_amt = float(quote.tax_amount or 0)
    total = float(quote.total or 0)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Colors
    PRIMARY_COLOR = colors.HexColor('#0EA5E9')  # Bleu turquoise
    ACCENT_COLOR = colors.HexColor('#F97316')   # Orange
    GRAY_TEXT = colors.HexColor('#6B7280')
    DARK_TEXT = colors.HexColor('#1F2937')
    LIGHT_BG = colors.HexColor('#F9FAFB')
    BORDER_COLOR = colors.HexColor('#E5E7EB')
    
    # Styles personnalisés
    company_name_style = ParagraphStyle(
        'CompanyName', parent=styles['Normal'],
        fontSize=12, fontName='Helvetica-Bold', textColor=DARK_TEXT
    )
    company_info_style = ParagraphStyle(
        'CompanyInfo', parent=styles['Normal'],
        fontSize=8, textColor=GRAY_TEXT, leading=11
    )
    total_big_style = ParagraphStyle(
        'TotalBig', parent=styles['Normal'],
        fontSize=28, fontName='Helvetica-Bold', textColor=DARK_TEXT, alignment=TA_RIGHT
    )
    total_label_style = ParagraphStyle(
        'TotalLabel', parent=styles['Normal'],
        fontSize=9, textColor=GRAY_TEXT, alignment=TA_RIGHT
    )
    section_title_style = ParagraphStyle(
        'SectionTitle', parent=styles['Normal'],
        fontSize=16, fontName='Helvetica-Bold', textColor=PRIMARY_COLOR
    )
    ref_style = ParagraphStyle(
        'RefStyle', parent=styles['Normal'],
        fontSize=10, textColor=GRAY_TEXT, alignment=TA_RIGHT
    )
    address_title_style = ParagraphStyle(
        'AddressTitle', parent=styles['Normal'],
        fontSize=8, textColor=GRAY_TEXT
    )
    address_style = ParagraphStyle(
        'Address', parent=styles['Normal'],
        fontSize=9, textColor=DARK_TEXT, fontName='Helvetica-Bold', leading=12
    )
    address_detail_style = ParagraphStyle(
        'AddressDetail', parent=styles['Normal'],
        fontSize=9, textColor=DARK_TEXT, leading=12
    )
    message_style = ParagraphStyle(
        'Message', parent=styles['Normal'],
        fontSize=9, textColor=GRAY_TEXT, fontStyle='italic', leading=12
    )
    date_label_style = ParagraphStyle(
        'DateLabel', parent=styles['Normal'],
        fontSize=8, textColor=GRAY_TEXT
    )
    date_value_style = ParagraphStyle(
        'DateValue', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica-Bold', textColor=DARK_TEXT
    )
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=7, textColor=GRAY_TEXT, leading=9
    )
    
    # ========== HEADER: Logo + Company Info + Total ==========
    company_lines = []
    if workspace:
        if workspace.legal_name:
            company_lines.append(f"<b>{workspace.legal_name}</b>")
        if hasattr(workspace, 'owner') and workspace.owner:
            # User model uses full_name, not first_name/last_name
            if workspace.owner.full_name:
                company_lines.append(workspace.owner.full_name)
        if workspace.legal_address:
            company_lines.append(workspace.legal_address)
        addr_line = ""
        if workspace.legal_postal_code:
            addr_line += workspace.legal_postal_code
        if workspace.legal_city:
            addr_line += f" {workspace.legal_city}"
        if workspace.legal_country:
            addr_line += f", {workspace.legal_country}"
        if addr_line:
            company_lines.append(addr_line)
        contact_line = ""
        if workspace.legal_phone:
            contact_line += workspace.legal_phone
        if workspace.legal_email:
            if contact_line:
                contact_line += "  |  "
            contact_line += workspace.legal_email
        if contact_line:
            company_lines.append(contact_line)
        if workspace.siret:
            company_lines.append(f"SIRET: {workspace.siret}")
        if workspace.vat_number:
            company_lines.append(f"TVA: {workspace.vat_number}")
    
    # Header table: Company info left, Total right
    header_data = [[
        Paragraph("<br/>".join(company_lines) if company_lines else "Votre entreprise", company_info_style),
        [
            Paragraph("Montant total", total_label_style),
            Paragraph(f"{total:,.0f} €".replace(',', ' '), total_big_style)
        ]
    ]]
    
    header_table = Table(header_data, colWidths=[120*mm, 55*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))
    
    # ========== DEVIS TITLE + REFERENCE ==========
    title_ref_data = [[
        Paragraph("Devis", section_title_style),
        Paragraph(f"#{quote.reference}", ref_style)
    ]]
    title_ref_table = Table(title_ref_data, colWidths=[90*mm, 85*mm])
    title_ref_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(title_ref_table)
    elements.append(Spacer(1, 5*mm))
    
    # ========== ADDRESSES: Delivery + Client ==========
    # Build client info
    client_lines = []
    client_contact_lines = []
    if quote.billing_client:
        c = quote.billing_client
        if c.name:
            client_lines.append(f"<b>{c.name}</b>")
        if c.address_line1:
            client_lines.append(c.address_line1)
        client_addr = ""
        if c.postal_code:
            client_addr += c.postal_code
        if c.city:
            client_addr += f" {c.city}"
        if client_addr:
            client_lines.append(client_addr)
        if c.phone:
            client_contact_lines.append(f"TEL: {c.phone}")
        if c.email:
            client_contact_lines.append(f"EMAIL: {c.email}")
        if c.siret:
            client_contact_lines.append(f"SIRET: {c.siret}")
        if c.vat_number:
            client_contact_lines.append(f"TVA: {c.vat_number}")
    
    address_data = [[
        [
            Paragraph("Adresse de livraison", address_title_style),
            Paragraph("<br/>".join(client_lines) if client_lines else "-", address_detail_style),
        ],
        [
            Paragraph("Devis proposé à", address_title_style),
            Paragraph(f"A l'attention de {quote.billing_client.name if quote.billing_client and quote.billing_client.name else '-'}", address_style),
            Paragraph("<br/>".join(client_lines[1:]) if len(client_lines) > 1 else "", address_detail_style),
            Paragraph("<br/>".join(client_contact_lines), address_detail_style) if client_contact_lines else Paragraph("", address_detail_style),
        ]
    ]]
    
    address_table = Table(address_data, colWidths=[90*mm, 85*mm])
    address_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(address_table)
    elements.append(Spacer(1, 3*mm))
    
    # ========== CUSTOM MESSAGE ==========
    if quote.description:
        elements.append(Paragraph(quote.description, message_style))
        elements.append(Spacer(1, 5*mm))
    
    # ========== DATES ROW ==========
    issue_date_str = quote.issue_date.strftime('%d/%m/%Y') if quote.issue_date else '-'
    validity_date_str = quote.validity_date.strftime('%d/%m/%Y') if quote.validity_date else '-'
    terms_str = quote.terms or "Virement"
    
    dates_data = [[
        [Paragraph("Date de devis", date_label_style), Paragraph(issue_date_str, date_value_style)],
        [Paragraph("Date de livraison", date_label_style), Paragraph("-", date_value_style)],
        [Paragraph("Conditions de règlement", date_label_style), Paragraph(terms_str, date_value_style)],
        [Paragraph("Validité de l'offre", date_label_style), Paragraph(validity_date_str, date_value_style)],
    ]]
    dates_table = Table(dates_data, colWidths=[45*mm, 45*mm, 45*mm, 40*mm])
    dates_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 4*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4*mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
    ]))
    elements.append(dates_table)
    elements.append(Spacer(1, 5*mm))
    
    # ========== ITEMS TABLE ==========
    # Header style with teal background
    items_header = ["N°", "ARTICLE", "QUANTITÉ", "PRIX UNITÉ HT", "TVA", "MONTANT HT", "MONTANT TTC"]
    table_data = [items_header]
    
    for idx, item in enumerate(sorted(quote.items, key=lambda x: x.position), 1):
        item_tax = float(item.line_total) * (tax_rate / 100)
        item_ttc = float(item.line_total) + item_tax
        table_data.append([
            str(idx),
            [
                Paragraph(f"<b>{item.description}</b>", ParagraphStyle('ItemName', fontSize=9, fontName='Helvetica-Bold')),
                Paragraph(item.description if len(item.description) > 30 else "Description du produit", ParagraphStyle('ItemDesc', fontSize=8, textColor=GRAY_TEXT))
            ],
            f"{int(item.quantity)}\n{item.unit or 'Unité(s)'}",
            f"{float(item.unit_price):,.0f} €".replace(',', ' '),
            f"{int(tax_rate)}%",
            f"{float(item.line_total):,.0f} €".replace(',', ' '),
            f"{item_ttc:,.0f} €".replace(',', ' ')
        ])
    
    items_table = Table(table_data, colWidths=[10*mm, 55*mm, 22*mm, 28*mm, 15*mm, 25*mm, 25*mm])
    
    # Style the table
    table_style = [
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Body
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        
        # Grid
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    
    # Alternate row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i), LIGHT_BG))
    
    items_table.setStyle(TableStyle(table_style))
    elements.append(items_table)
    elements.append(Spacer(1, 3*mm))
    
    # ========== TOTALS ==========
    totals_data = [
        ["", "", "", "", "", "Total HT", f"{subtotal:,.0f} €".replace(',', ' ')],
        ["", "", "", "", "", "Total TVA", f"{tax_amt:,.0f} €".replace(',', ' ')],
    ]
    if discount_pct > 0:
        totals_data.insert(1, ["", "", "", "", "", f"Remise ({discount_pct:.0f}%)", f"-{discount_amt:,.0f} €".replace(',', ' ')])
    
    totals_data.append(["", "", "", "", "", "Total TTC", f"{total:,.2f} €".replace(',', ' ').replace('.', ',')])
    
    totals_table = Table(totals_data, colWidths=[10*mm, 55*mm, 22*mm, 28*mm, 15*mm, 25*mm, 25*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (-2, -1), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 10*mm))
    
    # ========== PAYMENT INFO ==========
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    elements.append(Spacer(1, 5*mm))
    
    payment_info = workspace.payment_info if workspace and workspace.payment_info else {}
    iban = payment_info.get('iban', 'FRXX XXXX XXXX XXXX XXXX')
    account_name = payment_info.get('account_name', workspace.legal_name if workspace else '-')
    
    payment_data = [[
        Paragraph("<b>Paiement souhaité par virement bancaire</b>", ParagraphStyle('PayTitle', fontSize=9, fontName='Helvetica-Bold')),
    ], [
        Paragraph(f"Nom associé au compte: <b>{account_name}</b><br/>IBAN: <b>{iban}</b>", ParagraphStyle('PayDetails', fontSize=8, textColor=GRAY_TEXT)),
    ]]
    
    payment_table = Table(payment_data, colWidths=[175*mm])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 4*mm),
    ]))
    elements.append(payment_table)
    elements.append(Spacer(1, 5*mm))
    
    # ========== NOTES ==========
    if quote.notes:
        elements.append(Paragraph(quote.notes, message_style))
        elements.append(Spacer(1, 3*mm))
    
    elements.append(Paragraph("Si vous avez des questions ou des commentaires à propos de ce devis, n'hésitez pas à me contacter.<br/>À très vite.", message_style))
    elements.append(Spacer(1, 5*mm))
    
    # ========== LEGAL FOOTER ==========
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    elements.append(Spacer(1, 3*mm))
    
    legal_text = "Pour tout professionnel, en cas de retard de paiement, seront exigibles, conformément à l'article L 441-6 du code de commerce, une indemnité calculée sur la base de trois fois le taux de l'intérêt légal en vigueur ainsi qu'une indemnité forfaitaire pour frais de recouvrement de 40 euros."
    elements.append(Paragraph(legal_text, footer_style))
    elements.append(Spacer(1, 3*mm))
    
    # Company registration info
    reg_parts = []
    if workspace:
        if workspace.legal_city:
            reg_parts.append(f"Enregistré au RCS de: {workspace.legal_city}")
        if workspace.siret:
            reg_parts.append(f"Agrément n°: {workspace.siret[:9] if len(workspace.siret) >= 9 else workspace.siret}")
    elements.append(Paragraph("    ".join(reg_parts) if reg_parts else "", footer_style))
    
    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.seek(0)
    
    filename = f"{quote.reference}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/quotes/{quote_id}/pdf/drive")
async def upload_quote_pdf_to_drive(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Generate PDF and upload to Google Drive, replacing old version if exists"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from app.services.google_workspace import GoogleWorkspaceService
    from app.db.models.sso import SSOAccount
    
    quote = db.query(Quote).options(
        joinedload(Quote.billing_client),
        joinedload(Quote.items)
    ).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    # Get user's Google account
    google_account = db.query(SSOAccount).filter(
        SSOAccount.user_id == current_user.id,
        SSOAccount.provider == "google"
    ).first()
    
    if not google_account:
        raise HTTPException(status_code=400, detail="Connectez votre compte Google pour sauvegarder sur Drive")
    
    # Get workspace
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    # Generate PDF (same code as above but simplified)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    elements = []
    
    # Colors
    PRIMARY_COLOR = colors.HexColor('#0EA5E9')
    GRAY_TEXT = colors.HexColor('#6B7280')
    DARK_TEXT = colors.HexColor('#1F2937')
    LIGHT_BG = colors.HexColor('#F9FAFB')
    BORDER_COLOR = colors.HexColor('#E5E7EB')
    
    # Calculs
    subtotal = float(quote.subtotal or 0)
    discount_pct = float(quote.discount_percent or 0)
    discount_amt = float(quote.discount_amount or 0)
    tax_rate = float(quote.tax_rate or 20)
    tax_amt = float(quote.tax_amount or 0)
    total = float(quote.total or 0)
    
    # Styles
    company_info_style = ParagraphStyle('CompanyInfo', parent=styles['Normal'], fontSize=8, textColor=GRAY_TEXT, leading=11)
    total_big_style = ParagraphStyle('TotalBig', parent=styles['Normal'], fontSize=28, fontName='Helvetica-Bold', textColor=DARK_TEXT, alignment=TA_RIGHT)
    total_label_style = ParagraphStyle('TotalLabel', parent=styles['Normal'], fontSize=9, textColor=GRAY_TEXT, alignment=TA_RIGHT)
    section_title_style = ParagraphStyle('SectionTitle', parent=styles['Normal'], fontSize=16, fontName='Helvetica-Bold', textColor=PRIMARY_COLOR)
    ref_style = ParagraphStyle('RefStyle', parent=styles['Normal'], fontSize=10, textColor=GRAY_TEXT, alignment=TA_RIGHT)
    address_title_style = ParagraphStyle('AddressTitle', parent=styles['Normal'], fontSize=8, textColor=GRAY_TEXT)
    address_style = ParagraphStyle('Address', parent=styles['Normal'], fontSize=9, textColor=DARK_TEXT, fontName='Helvetica-Bold', leading=12)
    address_detail_style = ParagraphStyle('AddressDetail', parent=styles['Normal'], fontSize=9, textColor=DARK_TEXT, leading=12)
    message_style = ParagraphStyle('Message', parent=styles['Normal'], fontSize=9, textColor=GRAY_TEXT, leading=12)
    date_label_style = ParagraphStyle('DateLabel', parent=styles['Normal'], fontSize=8, textColor=GRAY_TEXT)
    date_value_style = ParagraphStyle('DateValue', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=DARK_TEXT)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, textColor=GRAY_TEXT, leading=9)
    
    # Build company info
    company_lines = []
    if workspace:
        if workspace.legal_name: company_lines.append(f"<b>{workspace.legal_name}</b>")
        if workspace.legal_address: company_lines.append(workspace.legal_address)
        addr = f"{workspace.legal_postal_code or ''} {workspace.legal_city or ''} {workspace.legal_country or ''}".strip()
        if addr: company_lines.append(addr)
        if workspace.siret: company_lines.append(f"SIRET: {workspace.siret}")
    
    # Header
    header_data = [[
        Paragraph("<br/>".join(company_lines) if company_lines else "Entreprise", company_info_style),
        [Paragraph("Montant total", total_label_style), Paragraph(f"{total:,.0f} €".replace(',', ' '), total_big_style)]
    ]]
    header_table = Table(header_data, colWidths=[120*mm, 55*mm])
    header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))
    
    # Title
    title_data = [[Paragraph("Devis", section_title_style), Paragraph(f"#{quote.reference}", ref_style)]]
    title_table = Table(title_data, colWidths=[90*mm, 85*mm])
    title_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
    elements.append(title_table)
    elements.append(Spacer(1, 5*mm))
    
    # Client info
    client_lines = []
    if quote.billing_client:
        c = quote.billing_client
        if c.name: client_lines.append(f"<b>{c.name}</b>")
        if c.address_line1: client_lines.append(c.address_line1)
        if c.postal_code or c.city: client_lines.append(f"{c.postal_code or ''} {c.city or ''}")
    
    address_data = [[
        [Paragraph("Adresse de livraison", address_title_style), Paragraph("<br/>".join(client_lines) if client_lines else "-", address_detail_style)],
        [Paragraph("Devis proposé à", address_title_style), Paragraph(f"A l'attention de {quote.billing_client.name if quote.billing_client else '-'}", address_style)]
    ]]
    address_table = Table(address_data, colWidths=[90*mm, 85*mm])
    address_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(address_table)
    elements.append(Spacer(1, 5*mm))
    
    # Dates
    issue_str = quote.issue_date.strftime('%d/%m/%Y') if quote.issue_date else '-'
    validity_str = quote.validity_date.strftime('%d/%m/%Y') if quote.validity_date else '-'
    dates_data = [[
        [Paragraph("Date de devis", date_label_style), Paragraph(issue_str, date_value_style)],
        [Paragraph("Conditions", date_label_style), Paragraph(quote.terms or "Virement", date_value_style)],
        [Paragraph("Validité", date_label_style), Paragraph(validity_str, date_value_style)],
    ]]
    dates_table = Table(dates_data, colWidths=[60*mm, 60*mm, 55*mm])
    dates_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG), ('TOPPADDING', (0, 0), (-1, -1), 4*mm), ('BOTTOMPADDING', (0, 0), (-1, -1), 4*mm)]))
    elements.append(dates_table)
    elements.append(Spacer(1, 5*mm))
    
    # Items table
    items_header = ["N°", "Article", "Qté", "Prix HT", "TVA", "Total HT"]
    table_data = [items_header]
    for idx, item in enumerate(sorted(quote.items, key=lambda x: x.position), 1):
        table_data.append([str(idx), item.description, f"{int(item.quantity)}", f"{float(item.unit_price):,.0f} €".replace(',', ' '), f"{int(tax_rate)}%", f"{float(item.line_total):,.0f} €".replace(',', ' ')])
    
    items_table = Table(table_data, colWidths=[12*mm, 75*mm, 18*mm, 28*mm, 18*mm, 28*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'), ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 3*mm))
    
    # Totals
    totals_data = [["", "", "", "", "Total HT", f"{subtotal:,.0f} €".replace(',', ' ')], ["", "", "", "", "TVA", f"{tax_amt:,.0f} €".replace(',', ' ')], ["", "", "", "", "Total TTC", f"{total:,.2f} €".replace(',', ' ').replace('.', ',')]]
    totals_table = Table(totals_data, colWidths=[12*mm, 75*mm, 18*mm, 28*mm, 18*mm, 28*mm])
    totals_table.setStyle(TableStyle([('ALIGN', (-2, 0), (-1, -1), 'RIGHT'), ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold')]))
    elements.append(totals_table)
    elements.append(Spacer(1, 5*mm))
    
    # Footer
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    elements.append(Paragraph("Pour tout professionnel, en cas de retard de paiement...", footer_style))
    
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    
    # Initialize Google service
    try:
        google_service = GoogleWorkspaceService(current_user.id)
        
        # Delete old PDF if exists
        if quote.drive_pdf_id:
            try:
                await google_service.delete_file(quote.drive_pdf_id)
            except Exception:
                pass  # Ignore if file doesn't exist
        
        # Find or create Devis folder
        folder_id = quote.drive_folder_id
        if not folder_id:
            # Try to find Radar folder first
            radar_folder = await google_service.find_folder("Radar")
            if radar_folder:
                # Find or create Devis subfolder
                devis_folder = await google_service.find_folder("Devis", radar_folder["id"])
                if devis_folder:
                    folder_id = devis_folder["id"]
                else:
                    devis_folder = await google_service.create_folder("Devis", radar_folder["id"])
                    folder_id = devis_folder["id"]
            else:
                # Create Radar folder
                radar_folder = await google_service.create_folder("Radar")
                devis_folder = await google_service.create_folder("Devis", radar_folder["id"])
                folder_id = devis_folder["id"]
            
            quote.drive_folder_id = folder_id
        
        # Upload new PDF
        filename = f"{quote.reference}.pdf"
        file_metadata = await google_service.upload_file(
            file_content=pdf_bytes,
            filename=filename,
            mime_type="application/pdf",
            parent_folder_id=folder_id
        )
        
        # Store the new file ID
        quote.drive_pdf_id = file_metadata.get('id')
        quote.drive_web_view_link = file_metadata.get('webViewLink')
        
        db.commit()
        
        return {
            "message": "PDF sauvegardé sur Google Drive",
            "drive_file_id": quote.drive_pdf_id,
            "web_view_link": quote.drive_web_view_link
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Google Drive: {str(e)}")


# ============ Invoice Endpoints ============

@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    status: Optional[InvoiceStatus] = None,
    client_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """List all invoices for the workspace"""
    query = db.query(Invoice).filter(Invoice.workspace_id == workspace_id)
    
    if status:
        query = query.filter(Invoice.status == status)
    if client_id:
        query = query.filter(Invoice.client_id == client_id)
    if search:
        query = query.filter(
            or_(
                Invoice.reference.ilike(f"%{search}%"),
                Invoice.title.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    invoices = query.options(
        joinedload(Invoice.billing_client),
        joinedload(Invoice.items)
    ).order_by(Invoice.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return InvoiceListResponse(
        items=invoices,
        total=total,
        page=page,
        size=size
    )


@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    invoice_in: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Create a new invoice"""
    invoice = Invoice(
        workspace_id=workspace_id,
        reference=generate_invoice_reference(db, workspace_id),
        created_by_id=current_user.id,
        title=invoice_in.title,
        description=invoice_in.description,
        client_id=invoice_in.client_id,
        opportunity_id=invoice_in.opportunity_id,
        issue_date=invoice_in.issue_date,
        due_date=invoice_in.due_date,
        tax_rate=invoice_in.tax_rate,
        discount_percent=invoice_in.discount_percent,
        terms=invoice_in.terms,
        notes=invoice_in.notes,
        status=InvoiceStatus.DRAFT
    )
    db.add(invoice)
    db.flush()
    
    # Add items
    for idx, item_data in enumerate(invoice_in.items):
        line_total = item_data.quantity * item_data.unit_price
        item = InvoiceItem(
            invoice_id=invoice.id,
            position=item_data.position or idx,
            description=item_data.description,
            quantity=item_data.quantity,
            unit=item_data.unit,
            unit_price=item_data.unit_price,
            line_total=line_total
        )
        db.add(item)
    
    db.flush()
    db.refresh(invoice)
    calculate_invoice_totals(invoice)
    
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Get a specific invoice"""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.billing_client),
        joinedload(Invoice.items)
    ).filter(
        Invoice.id == invoice_id,
        Invoice.workspace_id == workspace_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    return invoice


@router.patch("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice_in: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Update an invoice"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.workspace_id == workspace_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Impossible de modifier une facture payée")
    
    update_data = invoice_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    calculate_invoice_totals(invoice)
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.post("/invoices/{invoice_id}/items", response_model=InvoiceResponse)
async def add_invoice_item(
    invoice_id: int,
    item_in: InvoiceItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Add an item to an invoice"""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.items)
    ).filter(
        Invoice.id == invoice_id,
        Invoice.workspace_id == workspace_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Impossible de modifier une facture payée")
    
    line_total = item_in.quantity * item_in.unit_price
    item = InvoiceItem(
        invoice_id=invoice.id,
        position=item_in.position,
        description=item_in.description,
        quantity=item_in.quantity,
        unit=item_in.unit,
        unit_price=item_in.unit_price,
        line_total=line_total
    )
    db.add(item)
    db.flush()
    
    db.refresh(invoice)
    calculate_invoice_totals(invoice)
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.delete("/invoices/{invoice_id}/items/{item_id}")
async def delete_invoice_item(
    invoice_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Delete an item from an invoice"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.workspace_id == workspace_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Impossible de modifier une facture payée")
    
    item = db.query(InvoiceItem).filter(
        InvoiceItem.id == item_id,
        InvoiceItem.invoice_id == invoice_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    
    db.delete(item)
    db.flush()
    
    db.refresh(invoice)
    calculate_invoice_totals(invoice)
    db.commit()
    
    return {"message": "Ligne supprimée"}


@router.post("/invoices/{invoice_id}/payment", response_model=InvoiceResponse)
async def record_payment(
    invoice_id: int,
    payment: InvoicePaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Record a payment for an invoice"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.workspace_id == workspace_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    invoice.amount_paid = payment.amount_paid
    invoice.payment_method = payment.payment_method
    invoice.paid_date = payment.paid_date or date.today()
    
    # Update status based on payment
    if invoice.amount_paid >= invoice.total:
        invoice.status = InvoiceStatus.PAID
    elif invoice.amount_paid > 0:
        invoice.status = InvoiceStatus.PARTIAL
    
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.delete("/invoices/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Delete an invoice"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.workspace_id == workspace_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Impossible de supprimer une facture payée")
    
    db.delete(invoice)
    db.commit()
    return {"message": "Facture supprimée"}


# ============ Dashboard Endpoint ============

@router.get("/dashboard", response_model=BillingDashboard)
async def get_billing_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Get billing dashboard statistics"""
    # Quote counts
    quotes_draft = db.query(Quote).filter(
        Quote.workspace_id == workspace_id,
        Quote.status == QuoteStatus.DRAFT
    ).count()
    
    quotes_sent = db.query(Quote).filter(
        Quote.workspace_id == workspace_id,
        Quote.status == QuoteStatus.SENT
    ).count()
    
    quotes_accepted = db.query(Quote).filter(
        Quote.workspace_id == workspace_id,
        Quote.status == QuoteStatus.ACCEPTED
    ).count()
    
    # Invoice counts
    invoices_draft = db.query(Invoice).filter(
        Invoice.workspace_id == workspace_id,
        Invoice.status == InvoiceStatus.DRAFT
    ).count()
    
    invoices_sent = db.query(Invoice).filter(
        Invoice.workspace_id == workspace_id,
        Invoice.status == InvoiceStatus.SENT
    ).count()
    
    invoices_paid = db.query(Invoice).filter(
        Invoice.workspace_id == workspace_id,
        Invoice.status == InvoiceStatus.PAID
    ).count()
    
    invoices_overdue = db.query(Invoice).filter(
        Invoice.workspace_id == workspace_id,
        Invoice.status == InvoiceStatus.OVERDUE
    ).count()
    
    # Amounts
    total_quotes = db.query(func.coalesce(func.sum(Quote.total), 0)).filter(
        Quote.workspace_id == workspace_id,
        Quote.status.in_([QuoteStatus.SENT, QuoteStatus.ACCEPTED])
    ).scalar()
    
    total_invoices = db.query(func.coalesce(func.sum(Invoice.total), 0)).filter(
        Invoice.workspace_id == workspace_id,
        Invoice.status != InvoiceStatus.CANCELLED
    ).scalar()
    
    total_paid = db.query(func.coalesce(func.sum(Invoice.amount_paid), 0)).filter(
        Invoice.workspace_id == workspace_id
    ).scalar()
    
    total_pending = db.query(func.coalesce(func.sum(Invoice.total - Invoice.amount_paid), 0)).filter(
        Invoice.workspace_id == workspace_id,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE])
    ).scalar()
    
    return BillingDashboard(
        quotes_draft=quotes_draft,
        quotes_sent=quotes_sent,
        quotes_accepted=quotes_accepted,
        invoices_draft=invoices_draft,
        invoices_sent=invoices_sent,
        invoices_paid=invoices_paid,
        invoices_overdue=invoices_overdue,
        total_quotes_amount=Decimal(str(total_quotes)),
        total_invoices_amount=Decimal(str(total_invoices)),
        total_paid=Decimal(str(total_paid)),
        total_pending=Decimal(str(total_pending))
    )


# ============ Quote Status Management ============

def add_audit_log(obj, event: str, user_id: int, details: dict = None):
    """Add an audit log entry to a quote or invoice"""
    if obj.audit_log is None:
        obj.audit_log = []
    
    entry = {
        "event": event,
        "at": datetime.utcnow().isoformat(),
        "by": user_id
    }
    if details:
        entry["details"] = details
    
    obj.audit_log = obj.audit_log + [entry]


@router.post("/quotes/{quote_id}/send")
async def send_quote(
    quote_id: int,
    email: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Mark quote as sent"""
    quote = db.query(Quote).options(
        joinedload(Quote.billing_client)
    ).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote.status not in [QuoteStatus.DRAFT, QuoteStatus.SENT]:
        raise HTTPException(status_code=400, detail="Ce devis ne peut pas être envoyé")
    
    quote.status = QuoteStatus.SENT
    quote.sent_at = datetime.utcnow()
    quote.sent_to_email = email or (quote.billing_client.email if quote.billing_client else None)
    
    add_audit_log(quote, "sent", current_user.id, {"email": quote.sent_to_email})
    
    db.commit()
    return {"message": "Devis marqué comme envoyé", "status": quote.status.value}


@router.post("/quotes/{quote_id}/accept")
async def accept_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Mark quote as accepted"""
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote.status not in [QuoteStatus.SENT, QuoteStatus.DRAFT]:
        raise HTTPException(status_code=400, detail="Seuls les devis envoyés peuvent être acceptés")
    
    quote.status = QuoteStatus.ACCEPTED
    add_audit_log(quote, "accepted", current_user.id)
    
    db.commit()
    return {"message": "Devis accepté", "status": quote.status.value}


@router.post("/quotes/{quote_id}/reject")
async def reject_quote(
    quote_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Mark quote as rejected"""
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote.status not in [QuoteStatus.SENT, QuoteStatus.DRAFT]:
        raise HTTPException(status_code=400, detail="Ce devis ne peut pas être refusé")
    
    quote.status = QuoteStatus.REJECTED
    add_audit_log(quote, "rejected", current_user.id, {"reason": reason} if reason else None)
    
    db.commit()
    return {"message": "Devis refusé", "status": quote.status.value}


# ============ Invoice Status Management ============

@router.post("/invoices/{invoice_id}/send")
async def send_invoice(
    invoice_id: int,
    email: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Mark invoice as sent"""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.billing_client)
    ).filter(
        Invoice.id == invoice_id,
        Invoice.workspace_id == workspace_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.SENT]:
        raise HTTPException(status_code=400, detail="Cette facture ne peut pas être envoyée")
    
    invoice.status = InvoiceStatus.SENT
    invoice.sent_at = datetime.utcnow()
    invoice.sent_to_email = email or (invoice.billing_client.email if invoice.billing_client else None)
    
    add_audit_log(invoice, "sent", current_user.id, {"email": invoice.sent_to_email})
    
    db.commit()
    return {"message": "Facture marquée comme envoyée", "status": invoice.status.value}


@router.post("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(
    invoice_id: int,
    payment_method: Optional[PaymentMethod] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Mark invoice as fully paid"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.workspace_id == workspace_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Facture déjà payée")
    
    if invoice.status == InvoiceStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Facture annulée")
    
    invoice.status = InvoiceStatus.PAID
    invoice.amount_paid = invoice.total
    invoice.paid_date = date.today()
    if payment_method:
        invoice.payment_method = payment_method
    
    add_audit_log(invoice, "paid", current_user.id, {
        "amount": str(invoice.total),
        "method": payment_method.value if payment_method else None
    })
    
    db.commit()
    return {"message": "Facture marquée comme payée", "status": invoice.status.value}


@router.post("/invoices/{invoice_id}/cancel")
async def cancel_invoice(
    invoice_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """Cancel an invoice"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.workspace_id == workspace_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Impossible d'annuler une facture payée")
    
    invoice.status = InvoiceStatus.CANCELLED
    add_audit_log(invoice, "cancelled", current_user.id, {"reason": reason} if reason else None)
    
    db.commit()
    return {"message": "Facture annulée", "status": invoice.status.value}


# ============ Document Generation (Google Drive) ============

@router.post("/quotes/{quote_id}/generate-doc")
async def generate_quote_document(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """
    Generate a Google Doc for a quote and store it in the client's Drive folder.
    Structure: Radar / Clients / [ClientName] / Devis / Devis DEV-2026-0001 - ClientName.gdoc
    """
    from app.services.google_workspace import get_google_workspace_service, GoogleAPIError
    
    # Get quote with client
    quote = db.query(Quote).options(
        joinedload(Quote.billing_client),
        joinedload(Quote.items)
    ).filter(
        Quote.id == quote_id,
        Quote.workspace_id == workspace_id
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    # Get workspace for template and emitter info
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace non trouvé")
    
    # Check template exists
    if not workspace.devis_template_doc_id:
        raise HTTPException(
            status_code=400, 
            detail="Aucun template de devis configuré. Configurez le template dans les paramètres émetteur."
        )
    
    # Check workspace has Drive folder
    if not workspace.drive_folder_id:
        raise HTTPException(
            status_code=400,
            detail="Aucun dossier Drive configuré pour ce workspace."
        )
    
    # Get client name
    if quote.billing_client:
        client_name = quote.billing_client.company_name or f"{quote.billing_client.first_name} {quote.billing_client.last_name}"
    else:
        client_name = "Client Inconnu"
    
    # Build replacements dictionary
    replacements = build_quote_replacements(quote, workspace, client_name)
    
    try:
        # Get Google Workspace service for user
        gws = await get_google_workspace_service(current_user.id, db)
        
        # Generate document
        doc_result = await gws.generate_quote_document(
            template_id=workspace.devis_template_doc_id,
            quote_reference=quote.reference,
            client_name=client_name,
            root_folder_id=workspace.drive_folder_id,
            replacements=replacements
        )
        
        # Update quote with Drive info
        quote.drive_doc_id = doc_result["id"]
        quote.drive_web_view_link = doc_result["url"]
        quote.drive_folder_id = doc_result["folder_id"]
        
        add_audit_log(quote, "document_generated", current_user.id, {
            "doc_id": doc_result["id"],
            "url": doc_result["url"]
        })
        
        db.commit()
        
        return {
            "message": "Document généré avec succès",
            "doc_id": doc_result["id"],
            "url": doc_result["url"],
            "folder_id": doc_result["folder_id"]
        }
        
    except GoogleAPIError as e:
        raise HTTPException(status_code=500, detail=f"Erreur Google Drive: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")


@router.post("/invoices/{invoice_id}/generate-doc")
async def generate_invoice_document(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """
    Generate a Google Doc for an invoice and store it in the client's Drive folder.
    Structure: Radar / Clients / [ClientName] / Factures / Facture FAC-2026-0001 - ClientName.gdoc
    """
    from app.services.google_workspace import get_google_workspace_service, GoogleAPIError
    
    # Get invoice with client
    invoice = db.query(Invoice).options(
        joinedload(Invoice.billing_client),
        joinedload(Invoice.items)
    ).filter(
        Invoice.id == invoice_id,
        Invoice.workspace_id == workspace_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    # Get workspace for template and emitter info
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace non trouvé")
    
    # Check template exists
    if not workspace.facture_template_doc_id:
        raise HTTPException(
            status_code=400, 
            detail="Aucun template de facture configuré. Configurez le template dans les paramètres émetteur."
        )
    
    # Check workspace has Drive folder
    if not workspace.drive_folder_id:
        raise HTTPException(
            status_code=400,
            detail="Aucun dossier Drive configuré pour ce workspace."
        )
    
    # Get client name
    if invoice.billing_client:
        client_name = invoice.billing_client.company_name or f"{invoice.billing_client.first_name} {invoice.billing_client.last_name}"
    else:
        client_name = "Client Inconnu"
    
    # Build replacements dictionary
    replacements = build_invoice_replacements(invoice, workspace, client_name)
    
    try:
        # Get Google Workspace service for user
        gws = await get_google_workspace_service(current_user.id, db)
        
        # Generate document
        doc_result = await gws.generate_invoice_document(
            template_id=workspace.facture_template_doc_id,
            invoice_reference=invoice.reference,
            client_name=client_name,
            root_folder_id=workspace.drive_folder_id,
            replacements=replacements
        )
        
        # Update invoice with Drive info
        invoice.drive_doc_id = doc_result["id"]
        invoice.drive_web_view_link = doc_result["url"]
        invoice.drive_folder_id = doc_result["folder_id"]
        
        add_audit_log(invoice, "document_generated", current_user.id, {
            "doc_id": doc_result["id"],
            "url": doc_result["url"]
        })
        
        db.commit()
        
        return {
            "message": "Document généré avec succès",
            "doc_id": doc_result["id"],
            "url": doc_result["url"],
            "folder_id": doc_result["folder_id"]
        }
        
    except GoogleAPIError as e:
        raise HTTPException(status_code=500, detail=f"Erreur Google Drive: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")


def build_quote_replacements(quote: Quote, workspace: Workspace, client_name: str) -> dict:
    """Build placeholder replacements for quote template"""
    client = quote.billing_client
    
    # Format items table
    items_lines = []
    for item in quote.items:
        items_lines.append(
            f"{item.description}\t{item.quantity}\t{item.unit_price:.2f} €\t{item.line_total:.2f} €"
        )
    items_text = "\n".join(items_lines)
    
    # Format client address
    client_address = ""
    if client:
        parts = [client.address, f"{client.postal_code} {client.city}", client.country]
        client_address = "\n".join([p for p in parts if p])
    
    # Format emitter address
    emitter_address = ""
    if workspace.legal_address:
        parts = [
            workspace.legal_address,
            f"{workspace.legal_postal_code or ''} {workspace.legal_city or ''}".strip(),
            workspace.legal_country or "France"
        ]
        emitter_address = "\n".join([p for p in parts if p])
    
    return {
        # Emitter info
        "{{EMITTER_NAME}}": workspace.legal_name or workspace.name or "",
        "{{EMITTER_ADDRESS}}": emitter_address,
        "{{EMITTER_PHONE}}": workspace.legal_phone or "",
        "{{EMITTER_EMAIL}}": workspace.legal_email or workspace.billing_email or "",
        "{{EMITTER_SIRET}}": workspace.siret or "",
        "{{EMITTER_VAT}}": workspace.vat_number or "",
        
        # Client info
        "{{CLIENT_NAME}}": client_name,
        "{{CLIENT_COMPANY}}": client.company_name if client else "",
        "{{CLIENT_ADDRESS}}": client_address,
        "{{CLIENT_EMAIL}}": client.email if client else "",
        "{{CLIENT_PHONE}}": client.phone if client else "",
        "{{CLIENT_VAT}}": client.vat_number if client else "",
        
        # Quote info
        "{{QUOTE_REFERENCE}}": quote.reference,
        "{{QUOTE_TITLE}}": quote.title or "",
        "{{ISSUE_DATE}}": quote.issue_date.strftime("%d/%m/%Y") if quote.issue_date else "",
        "{{VALIDITY_DATE}}": quote.valid_until.strftime("%d/%m/%Y") if quote.valid_until else "",
        "{{NOTES}}": quote.notes or "",
        "{{TERMS}}": quote.terms or "",
        
        # Items table (simplified - template should have actual table)
        "{{ITEMS_TABLE}}": items_text,
        
        # Totals
        "{{SUBTOTAL}}": f"{quote.subtotal:.2f} €",
        "{{DISCOUNT_PERCENT}}": f"{quote.discount_percent:.0f} %",
        "{{DISCOUNT_AMOUNT}}": f"{quote.discount_amount:.2f} €",
        "{{TAX_RATE}}": f"{quote.tax_rate:.0f} %",
        "{{TAX_AMOUNT}}": f"{quote.tax_amount:.2f} €",
        "{{TOTAL}}": f"{quote.total:.2f} €",
    }


def build_invoice_replacements(invoice: Invoice, workspace: Workspace, client_name: str) -> dict:
    """Build placeholder replacements for invoice template"""
    client = invoice.billing_client
    
    # Format items table
    items_lines = []
    for item in invoice.items:
        items_lines.append(
            f"{item.description}\t{item.quantity}\t{item.unit_price:.2f} €\t{item.line_total:.2f} €"
        )
    items_text = "\n".join(items_lines)
    
    # Format client address
    client_address = ""
    if client:
        parts = [client.address, f"{client.postal_code} {client.city}", client.country]
        client_address = "\n".join([p for p in parts if p])
    
    # Format emitter address
    emitter_address = ""
    if workspace.legal_address:
        parts = [
            workspace.legal_address,
            f"{workspace.legal_postal_code or ''} {workspace.legal_city or ''}".strip(),
            workspace.legal_country or "France"
        ]
        emitter_address = "\n".join([p for p in parts if p])
    
    return {
        # Emitter info
        "{{EMITTER_NAME}}": workspace.legal_name or workspace.name or "",
        "{{EMITTER_ADDRESS}}": emitter_address,
        "{{EMITTER_PHONE}}": workspace.legal_phone or "",
        "{{EMITTER_EMAIL}}": workspace.legal_email or workspace.billing_email or "",
        "{{EMITTER_SIRET}}": workspace.siret or "",
        "{{EMITTER_VAT}}": workspace.vat_number or "",
        
        # Client info
        "{{CLIENT_NAME}}": client_name,
        "{{CLIENT_COMPANY}}": client.company_name if client else "",
        "{{CLIENT_ADDRESS}}": client_address,
        "{{CLIENT_EMAIL}}": client.email if client else "",
        "{{CLIENT_PHONE}}": client.phone if client else "",
        "{{CLIENT_VAT}}": client.vat_number if client else "",
        
        # Invoice info
        "{{INVOICE_REFERENCE}}": invoice.reference,
        "{{INVOICE_TITLE}}": invoice.title or "",
        "{{ISSUE_DATE}}": invoice.issue_date.strftime("%d/%m/%Y") if invoice.issue_date else "",
        "{{DUE_DATE}}": invoice.due_date.strftime("%d/%m/%Y") if invoice.due_date else "",
        "{{NOTES}}": invoice.notes or "",
        "{{PAYMENT_TERMS}}": invoice.payment_terms or "",
        
        # Items table
        "{{ITEMS_TABLE}}": items_text,
        
        # Totals
        "{{SUBTOTAL}}": f"{invoice.subtotal:.2f} €",
        "{{DISCOUNT_PERCENT}}": f"{invoice.discount_percent:.0f} %",
        "{{DISCOUNT_AMOUNT}}": f"{invoice.discount_amount:.2f} €",
        "{{TAX_RATE}}": f"{invoice.tax_rate:.0f} %",
        "{{TAX_AMOUNT}}": f"{invoice.tax_amount:.2f} €",
        "{{TOTAL}}": f"{invoice.total:.2f} €",
        "{{AMOUNT_PAID}}": f"{invoice.amount_paid:.2f} €",
        "{{AMOUNT_DUE}}": f"{(invoice.total - invoice.amount_paid):.2f} €",
    }
