"""
Billing API endpoints for quotes (devis) and invoices (factures)
Part of Radar Business add-on
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_

from app.api.deps import get_db, get_current_user, get_current_workspace_id
from app.db.models.user import User
from app.db.models.billing import (
    BillingClient, Quote, QuoteItem, Invoice, InvoiceItem,
    QuoteStatus, InvoiceStatus
)
from app.schemas.billing import (
    ClientCreate, ClientUpdate, ClientResponse,
    QuoteCreate, QuoteUpdate, QuoteResponse, QuoteListResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListResponse,
    InvoicePaymentUpdate, QuoteToInvoiceCreate, BillingDashboard,
    QuoteItemCreate, InvoiceItemCreate
)

router = APIRouter()


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


# ============ Client Endpoints ============

@router.get("/clients", response_model=List[ClientResponse])
async def list_clients(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_current_workspace_id)
):
    """List all clients for the workspace"""
    query = db.query(BillingClient).filter(BillingClient.workspace_id == workspace_id)
    
    if search:
        query = query.filter(
            or_(
                BillingClient.name.ilike(f"%{search}%"),
                BillingClient.email.ilike(f"%{search}%"),
                BillingClient.company_name.ilike(f"%{search}%")
            )
        )
    
    return query.order_by(BillingClient.name).all()


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
        joinedload(Quote.client),
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
        joinedload(Quote.client),
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
        joinedload(Quote.client)
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
        joinedload(Invoice.client),
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
        joinedload(Invoice.client),
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
