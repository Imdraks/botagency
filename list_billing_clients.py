from app.db.session import SessionLocal
from app.db.models.billing import BillingClient

db = SessionLocal()
clients = db.query(BillingClient).all()
print(f"Total billing_clients: {len(clients)}")
for c in clients:
    print(f"  ID: {c.id}, Name: {c.name}, Workspace ID: {c.workspace_id}")
db.close()
