from app.db.session import SessionLocal
from app.db.models.billing import BillingClient

db = SessionLocal()
client = db.query(BillingClient).filter(BillingClient.id == 1).first()
if client:
    print(f"Suppression de BillingClient: {client.name}")
    db.delete(client)
    db.commit()
    print("Supprime!")
else:
    print("Non trouve")
db.close()
