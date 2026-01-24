"""Billing enhancements: workspace emitter info + quote/invoice Drive fields

Revision ID: 032_billing_enhancements
Revises: 031_subscription_plans
Create Date: 2026-01-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '032_billing_enhancements'
down_revision = '031_subscription_plans'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========== WORKSPACE: Emitter/Billing info ===========
    op.add_column('workspaces', sa.Column('devis_template_doc_id', sa.String(255), nullable=True))
    op.add_column('workspaces', sa.Column('facture_template_doc_id', sa.String(255), nullable=True))
    op.add_column('workspaces', sa.Column('legal_name', sa.String(255), nullable=True))
    op.add_column('workspaces', sa.Column('legal_address', sa.String(500), nullable=True))
    op.add_column('workspaces', sa.Column('legal_city', sa.String(100), nullable=True))
    op.add_column('workspaces', sa.Column('legal_postal_code', sa.String(20), nullable=True))
    op.add_column('workspaces', sa.Column('legal_country', sa.String(100), nullable=True, server_default='France'))
    op.add_column('workspaces', sa.Column('legal_phone', sa.String(50), nullable=True))
    op.add_column('workspaces', sa.Column('legal_email', sa.String(255), nullable=True))
    op.add_column('workspaces', sa.Column('siret', sa.String(20), nullable=True))
    op.add_column('workspaces', sa.Column('vat_number', sa.String(30), nullable=True))
    op.add_column('workspaces', sa.Column('logo_drive_file_id', sa.String(255), nullable=True))
    op.add_column('workspaces', sa.Column('payment_info', JSON, nullable=True))
    
    # =========== QUOTES: Drive integration + audit ===========
    op.add_column('quotes', sa.Column('drive_doc_id', sa.String(255), nullable=True))
    op.add_column('quotes', sa.Column('drive_pdf_id', sa.String(255), nullable=True))
    op.add_column('quotes', sa.Column('drive_web_view_link', sa.String(500), nullable=True))
    op.add_column('quotes', sa.Column('drive_folder_id', sa.String(255), nullable=True))
    op.add_column('quotes', sa.Column('audit_log', JSON, nullable=True, server_default='[]'))
    op.add_column('quotes', sa.Column('sent_at', sa.DateTime(), nullable=True))
    op.add_column('quotes', sa.Column('sent_to_email', sa.String(255), nullable=True))
    
    # =========== INVOICES: Drive integration + audit ===========
    op.add_column('invoices', sa.Column('drive_doc_id', sa.String(255), nullable=True))
    op.add_column('invoices', sa.Column('drive_pdf_id', sa.String(255), nullable=True))
    op.add_column('invoices', sa.Column('drive_web_view_link', sa.String(500), nullable=True))
    op.add_column('invoices', sa.Column('drive_folder_id', sa.String(255), nullable=True))
    op.add_column('invoices', sa.Column('audit_log', JSON, nullable=True, server_default='[]'))
    op.add_column('invoices', sa.Column('sent_at', sa.DateTime(), nullable=True))
    op.add_column('invoices', sa.Column('sent_to_email', sa.String(255), nullable=True))


def downgrade() -> None:
    # Invoices
    op.drop_column('invoices', 'sent_to_email')
    op.drop_column('invoices', 'sent_at')
    op.drop_column('invoices', 'audit_log')
    op.drop_column('invoices', 'drive_folder_id')
    op.drop_column('invoices', 'drive_web_view_link')
    op.drop_column('invoices', 'drive_pdf_id')
    op.drop_column('invoices', 'drive_doc_id')
    
    # Quotes
    op.drop_column('quotes', 'sent_to_email')
    op.drop_column('quotes', 'sent_at')
    op.drop_column('quotes', 'audit_log')
    op.drop_column('quotes', 'drive_folder_id')
    op.drop_column('quotes', 'drive_web_view_link')
    op.drop_column('quotes', 'drive_pdf_id')
    op.drop_column('quotes', 'drive_doc_id')
    
    # Workspaces
    op.drop_column('workspaces', 'payment_info')
    op.drop_column('workspaces', 'logo_drive_file_id')
    op.drop_column('workspaces', 'vat_number')
    op.drop_column('workspaces', 'siret')
    op.drop_column('workspaces', 'legal_email')
    op.drop_column('workspaces', 'legal_phone')
    op.drop_column('workspaces', 'legal_country')
    op.drop_column('workspaces', 'legal_postal_code')
    op.drop_column('workspaces', 'legal_city')
    op.drop_column('workspaces', 'legal_address')
    op.drop_column('workspaces', 'legal_name')
    op.drop_column('workspaces', 'facture_template_doc_id')
    op.drop_column('workspaces', 'devis_template_doc_id')
