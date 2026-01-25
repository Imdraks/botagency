from app.db.session import SessionLocal
from app.db.models.agency import Client
from app.db.models.workspace import Workspace

db = SessionLocal()

# Trouver le workspace Arabic Agency
ws = db.query(Workspace).filter(Workspace.name.ilike('%arabic%')).first()
if not ws:
    # Lister tous les workspaces
    print("Workspaces disponibles:")
    for w in db.query(Workspace).all():
        print(f"  {w.id}: {w.name}")
    exit(1)

print(f"Utilisation du workspace: {ws.id} - {ws.name}")

client = Client(
    workspace_id=ws.id,
    name='Music Factory Paris',
    address_line1='25 Avenue des Champs-Elysees',
    address_line2='Batiment A, 3eme etage',
    city='Paris',
    postal_code='75008',
    country='France',
    siret='12345678901234',
    vat_number='FR12345678901',
    contacts=[
        {
            'name': 'Dupont',
            'role': 'Jean',
            'email': 'jean.dupont@musicfactory.fr',
            'phone': '+33 6 12 34 56 78'
        },
        {
            'name': 'Martin',
            'role': 'Sophie',
            'email': 'sophie.martin@musicfactory.fr',
            'phone': '+33 6 98 76 54 32'
        }
    ],
    notes='Client premium - Label independant specialise en musique electronique'
)

db.add(client)
db.commit()
db.refresh(client)

print(f'Client cree avec ID: {client.id}')
print(f'Nom: {client.name}')
print(f'Entreprise: {client.company}')
print(f'Adresse: {client.address_line1}, {client.postal_code} {client.city}')
print(f'SIRET: {client.siret}')
print(f'TVA: {client.vat_number}')
db.close()
