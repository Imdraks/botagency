from app.db.session import SessionLocal
from app.db.models.agency import Client as CRMClient
from app.db.models.billing import BillingClient

db = SessionLocal()
crm_clients = db.query(CRMClient).all()
print(f"Found {len(crm_clients)} CRM clients")

synced = 0
for c in crm_clients:
    if not db.query(BillingClient).filter(BillingClient.crm_client_id == c.id).first():
        bc = BillingClient(
            workspace_id=c.workspace_id,
            crm_client_id=c.id,
            name=c.name,
            company_name=c.name
        )
        db.add(bc)
        synced += 1
        print(f"Synced: {c.name}")

db.commit()
print(f"Total synced: {synced}")
db.close()
