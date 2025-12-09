import json
from pathlib import Path
from typing import List, Dict, Optional

DATABASE_FILE = Path(__file__).parent.parent.parent / "db.json"

def load_db() -> Dict:
    if not DATABASE_FILE.exists():
        return {"conversion_requests": []}
    with open(DATABASE_FILE, "r") as f:
        return json.load(f)

def save_db(db: Dict):
    with open(DATABASE_FILE, "w") as f:
        json.dump(db, f, indent=4)

def add_conversion_request(request_data: Dict) -> Dict:
    db = load_db()
    db["conversion_requests"].append(request_data)
    save_db(db)
    return request_data

def get_all_conversion_requests() -> List[Dict]:
    db = load_db()
    return db.get("conversion_requests", [])

def update_conversion_request_status(request_id: str, status: str, converted_filename: Optional[str] = None, download_url: Optional[str] = None, error: Optional[str] = None):
    db = load_db()
    for req in db["conversion_requests"]:
        if req["id"] == request_id:
            req["status"] = status
            if converted_filename:
                req["converted_filename"] = converted_filename
            if download_url:
                req["download_url"] = download_url
            if error:
                req["error"] = error
            save_db(db)
            return True
    return False

def get_conversion_request_by_id(request_id: str) -> Optional[Dict]:
    db = load_db()
    for req in db["conversion_requests"]:
        if req["id"] == request_id:
            return req
    return None
