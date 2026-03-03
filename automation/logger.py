
from models.database import SessionLocal, SystemLog
from datetime import datetime
import json

def log_action(action_type, entity_type=None, entity_id=None, status="success", message=None, extra_data=None):
    """Utility to log system actions to the database for the dashboard to see"""
    db = SessionLocal()
    try:
        log_entry = SystemLog(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            ai_response=message,
            extra_data=extra_data
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Logging error: {e}")
    finally:
        db.close()
