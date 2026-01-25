from app.db.session import SessionLocal
from app.db.models.agency import Client
from app.db.models.billing import BillingClient

db = SessionLocal()

# Trouver le client CRM
crm_client = db.query(Client).filter(Client.id == 7).first()
if not crm_client:
    print("Client CRM 7 non trouve")
    exit(1)

print(f"Client CRM trouve: {crm_client.name}")

# Verifier si billing_client existe deja
billing_client = db.query(BillingClient).filter(
    BillingClient.workspace_id == crm_client.workspace_id,
    BillingClient.name == crm_client.name
).first()

if billing_client:
    print(f"BillingClient existe deja: ID {billing_client.id}")
else:
    # Creer le BillingClient
    contacts = crm_client.contacts or []
    first_contact = contacts[0] if contacts else {}
    
    billing_client = BillingClient(
        workspace_id=crm_client.workspace_id,
        name=crm_client.name,
        contact_first_name=first_contact.get('role', ''),  # role = prenom maintenant
        contact_last_name=first_contact.get('name', ''),
        contact_email=first_contact.get('email', ''),
        contact_phone=first_contact.get('phone', ''),
        address_line1=crm_client.address_line1,
        address_line2=crm_client.address_line2,
        city=crm_client.city,
        postal_code=crm_client.postal_code,
        country=crm_client.country or 'France',
        siret=crm_client.siret,
        vat_number=crm_client.vat_number,
    )
    db.add(billing_client)
    db.commit()
    db.refresh(billing_client)
    print(f"BillingClient cree avec ID: {billing_client.id}")

db.close()
