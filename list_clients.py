from app.db.session import SessionLocal
from app.db.models.agency import Client

db = SessionLocal()
clients = db.query(Client).all()
print(f"Total clients: {len(clients)}")
for c in clients:
    print(f"  ID: {c.id}, Name: {c.name}, Workspace ID: {c.workspace_id}")
db.close()
