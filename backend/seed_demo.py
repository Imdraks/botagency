"""
Script pour créer des données de démo dans Radar
"""
from app.db.session import SessionLocal
from app.db.models import Lead, Project, Client, Task
from datetime import datetime, timedelta
import random

def seed_demo_data():
    db = SessionLocal()
    workspace_id = 5
    user_id = 5  # Admin user
    
    try:
        # Créer des clients de démo
        clients_data = [
            {'name': 'Studio Neon', 'email': 'contact@studioneon.fr', 'company': 'Studio Neon SARL'},
            {'name': 'Agence Pulse', 'email': 'hello@pulse.agency', 'company': 'Pulse Agency'},
            {'name': 'MediaLab Paris', 'email': 'pro@medialab.paris', 'company': 'MediaLab SAS'},
            {'name': 'Creative House', 'email': 'team@creativehouse.com', 'company': 'Creative House'},
            {'name': 'Brand Factory', 'email': 'contact@brandfactory.io', 'company': 'Brand Factory'},
        ]
        
        clients = []
        for c in clients_data:
            existing = db.query(Client).filter(Client.email == c['email'], Client.workspace_id == workspace_id).first()
            if not existing:
                client = Client(
                    workspace_id=workspace_id,
                    name=c['name'],
                    email=c['email'],
                    company=c.get('company', c['name'])
                )
                db.add(client)
                db.flush()
                clients.append(client)
                print(f"Client créé: {c['name']}")
            else:
                clients.append(existing)
                print(f"Client existant: {c['name']}")
        
        db.commit()
        
        # Créer des leads de démo
        leads_data = [
            {'title': 'Refonte site e-commerce', 'value': 15000, 'status': 'qualified', 'priority': 'high'},
            {'title': 'Campagne Social Media Q1', 'value': 8000, 'status': 'proposal', 'priority': 'medium'},
            {'title': 'Vidéo corporate', 'value': 12000, 'status': 'negotiation', 'priority': 'high'},
            {'title': 'Branding startup', 'value': 6000, 'status': 'qualified', 'priority': 'medium'},
            {'title': 'Application mobile MVP', 'value': 25000, 'status': 'discovery', 'priority': 'low'},
        ]
        
        for i, l in enumerate(leads_data):
            existing = db.query(Lead).filter(Lead.title == l['title'], Lead.workspace_id == workspace_id).first()
            if not existing:
                lead = Lead(
                    workspace_id=workspace_id,
                    client_id=clients[i % len(clients)].id if clients else None,
                    title=l['title'],
                    estimated_value=l['value'],
                    status=l['status'],
                    priority=l['priority'],
                    created_by_id=user_id
                )
                db.add(lead)
                print(f"Lead créé: {l['title']}")
        
        db.commit()
        
        # Créer des projets de démo
        projects_data = [
            {'name': 'Site Vitrine Studio Neon', 'status': 'in_progress', 'budget': 8000},
            {'name': 'Campagne Pulse Hiver 2026', 'status': 'in_progress', 'budget': 12000},
            {'name': 'Motion Design MediaLab', 'status': 'review', 'budget': 5000},
            {'name': 'Identité Visuelle Brand Factory', 'status': 'in_progress', 'budget': 9000},
        ]
        
        for i, p in enumerate(projects_data):
            existing = db.query(Project).filter(Project.name == p['name'], Project.workspace_id == workspace_id).first()
            if not existing:
                project = Project(
                    workspace_id=workspace_id,
                    client_id=clients[i % len(clients)].id if clients else None,
                    name=p['name'],
                    status=p['status'],
                    budget=p['budget'],
                    start_date=datetime.now() - timedelta(days=random.randint(5, 30)),
                    due_date=datetime.now() + timedelta(days=random.randint(10, 60)),
                    created_by_id=user_id
                )
                db.add(project)
                db.flush()
                
                # Ajouter des tâches au projet
                tasks = [
                    {'title': 'Brief client', 'status': 'done'},
                    {'title': 'Maquettes V1', 'status': 'done'},
                    {'title': 'Développement', 'status': 'in_progress'},
                    {'title': 'Recette', 'status': 'todo'},
                    {'title': 'Livraison', 'status': 'todo'},
                ]
                for t in tasks:
                    task = Task(
                        workspace_id=workspace_id,
                        project_id=project.id,
                        title=t['title'],
                        status=t['status'],
                        created_by_id=user_id
                    )
                    db.add(task)
                
                print(f"Projet créé: {p['name']}")
        
        db.commit()
        print("\n✅ Données de démo créées avec succès!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
