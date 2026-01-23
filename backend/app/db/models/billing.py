"""
Billing models for quotes (devis) and invoices (factures)
Part of Radar Business add-on
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Date, Enum, ForeignKey,
    Integer, Numeric, JSON
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class QuoteStatus(str, PyEnum):
    """Quote/Devis status"""
    DRAFT = "DRAFT"           # Brouillon
    SENT = "SENT"             # Envoyé au client
    ACCEPTED = "ACCEPTED"     # Accepté
    REJECTED = "REJECTED"     # Refusé
    EXPIRED = "EXPIRED"       # Expiré
    INVOICED = "INVOICED"     # Converti en facture


class InvoiceStatus(str, PyEnum):
    """Invoice/Facture status"""
    DRAFT = "DRAFT"           # Brouillon
    SENT = "SENT"             # Envoyée
    PAID = "PAID"             # Payée
    PARTIAL = "PARTIAL"       # Partiellement payée
    OVERDUE = "OVERDUE"       # En retard
    CANCELLED = "CANCELLED"   # Annulée


class PaymentMethod(str, PyEnum):
    """Payment methods"""
    BANK_TRANSFER = "BANK_TRANSFER"   # Virement bancaire
    CHECK = "CHECK"                   # Chèque
    CASH = "CASH"                     # Espèces
    CARD = "CARD"                     # Carte bancaire
    OTHER = "OTHER"


class Client(Base):
    """Client for quotes and invoices"""
    __tablename__ = "billing_clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="France")
    
    # Business info
    company_name = Column(String(255), nullable=True)
    siret = Column(String(20), nullable=True)
    vat_number = Column(String(30), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quotes = relationship("Quote", back_populates="client", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")


class Quote(Base):
    """Devis (Quote)"""
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False, index=True)
    
    # Reference number (auto-generated)
    reference = Column(String(50), nullable=False, unique=True, index=True)
    
    # Client
    client_id = Column(Integer, ForeignKey('billing_clients.id'), nullable=True)
    
    # Opportunity link (optional)
    opportunity_id = Column(Integer, ForeignKey('opportunities.id'), nullable=True)
    
    # Status
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT, nullable=False)
    
    # Dates
    issue_date = Column(Date, default=date.today, nullable=False)
    validity_date = Column(Date, nullable=True)  # Date de validité
    
    # Title and description
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Amounts (calculated from items)
    subtotal = Column(Numeric(12, 2), default=0)      # HT
    tax_rate = Column(Numeric(5, 2), default=20.00)   # TVA %
    tax_amount = Column(Numeric(12, 2), default=0)    # Montant TVA
    total = Column(Numeric(12, 2), default=0)         # TTC
    
    # Discount
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    
    # Terms and conditions
    terms = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Created invoice (if converted)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=True)
    
    # Metadata
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("Client", back_populates="quotes")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    opportunity = relationship("Opportunity")
    created_by = relationship("User")


class QuoteItem(Base):
    """Quote line item"""
    __tablename__ = "quote_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(Integer, ForeignKey('quotes.id'), nullable=False)
    
    # Position for ordering
    position = Column(Integer, default=0)
    
    # Item details
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit = Column(String(50), default="unité")  # unité, heure, jour, forfait...
    unit_price = Column(Numeric(12, 2), nullable=False)
    
    # Calculated
    line_total = Column(Numeric(12, 2), nullable=False)
    
    # Relationship
    quote = relationship("Quote", back_populates="items")


class Invoice(Base):
    """Facture (Invoice)"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False, index=True)
    
    # Reference number (auto-generated)
    reference = Column(String(50), nullable=False, unique=True, index=True)
    
    # Client
    client_id = Column(Integer, ForeignKey('billing_clients.id'), nullable=True)
    
    # Opportunity link (optional)
    opportunity_id = Column(Integer, ForeignKey('opportunities.id'), nullable=True)
    
    # Source quote (if converted from quote)
    source_quote_id = Column(Integer, ForeignKey('quotes.id'), nullable=True)
    
    # Status
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    
    # Dates
    issue_date = Column(Date, default=date.today, nullable=False)
    due_date = Column(Date, nullable=True)  # Date d'échéance
    paid_date = Column(Date, nullable=True)
    
    # Title and description
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Amounts
    subtotal = Column(Numeric(12, 2), default=0)      # HT
    tax_rate = Column(Numeric(5, 2), default=20.00)   # TVA %
    tax_amount = Column(Numeric(12, 2), default=0)    # Montant TVA
    total = Column(Numeric(12, 2), default=0)         # TTC
    
    # Payments
    amount_paid = Column(Numeric(12, 2), default=0)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    
    # Discount
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    
    # Terms and conditions
    terms = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Metadata
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("Client", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    source_quote = relationship("Quote", foreign_keys=[source_quote_id])
    opportunity = relationship("Opportunity")
    created_by = relationship("User")


class InvoiceItem(Base):
    """Invoice line item"""
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    
    # Position for ordering
    position = Column(Integer, default=0)
    
    # Item details
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit = Column(String(50), default="unité")
    unit_price = Column(Numeric(12, 2), nullable=False)
    
    # Calculated
    line_total = Column(Numeric(12, 2), nullable=False)
    
    # Relationship
    invoice = relationship("Invoice", back_populates="items")
