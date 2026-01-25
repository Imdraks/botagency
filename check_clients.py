from app.db.session import SessionLocal
from app.db.models.agency import Client
from app.db.models.billing import BillingClient

db = SessionLocal()

print('=== CRM Clients ===')
for c in db.query(Client).all():
    print(f'  ID: {c.id}, Name: {c.name}, WS: {c.workspace_id}')

print()
print('=== Billing Clients ===')
for c in db.query(BillingClient).all():
    print(f'  ID: {c.id}, Name: {c.name}, WS: {c.workspace_id}')

db.close()
