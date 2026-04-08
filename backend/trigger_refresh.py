"""One-off script to trigger enrichment refresh for an artist."""
import sys
from app.db.session import SessionLocal
from app.db.models.discovery import DiscoveryEnrichmentJob
from app.workers.discovery_pipeline import run_enrichment_pipeline
from datetime import datetime

artist_id = sys.argv[1]
workspace_id = int(sys.argv[2])
name = sys.argv[3] if len(sys.argv) > 3 else "Unknown"

db = SessionLocal()
j = DiscoveryEnrichmentJob(
    workspace_id=workspace_id,
    artist_id=artist_id,
    input_type="NAME",
    input_value=name,
    status="QUEUED",
    current_step="VIBERATE",
    started_at=datetime.utcnow(),
)
db.add(j)
db.commit()
job_id = str(j.id)
db.close()
print(f"Created job {job_id}, running pipeline...")
run_enrichment_pipeline(job_id)
print("Done!")
