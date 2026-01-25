from app.db.session import SessionLocal
from app.db.models.agency import Client

db = SessionLocal()
c = db.query(Client).filter(Client.id == 6).first()
if c:
    db.delete(c)
    db.commit()
    print("Client 6 supprime")
else:
    print("Non trouve")
db.close()
