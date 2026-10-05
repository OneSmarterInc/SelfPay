"""Read-only local operator view of pending correction reports."""
import json
import core
if not core.DB.exists():
    print('Run server.py once to initialize the local POC.')
else:
    with core.connect() as db:
        rows=db.execute('SELECT id,offer_id,batch_id,category,description,created,status FROM corrections ORDER BY created DESC').fetchall()
    print(json.dumps([dict(r) for r in rows],indent=2))
