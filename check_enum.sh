#!/bin/bash
cd /opt/radar

# Check enum values
docker compose -f docker-compose.prod.yml exec -T backend python -c "
from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text(\"SELECT unnest(enum_range(NULL::dealstatus))\"))
print('Current dealstatus enum values:')
for row in result:
    print(f'  - {row[0]}')
db.close()
"
