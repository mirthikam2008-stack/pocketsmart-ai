"""
Authentication, Session Management & Persistence Service for PocketSmart AI.
Provides user account management, password hashing, token verification, and history logs.
"""

import os
import json
import uuid
import hashlib
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pocket_smart_db.json")


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_db() -> Dict[str, Any]:
    if not os.path.exists(DB_FILE):
        default_db = {
            "users": {
                "demo@pocketsmart.ai": {
                    "id": "u-demo-123",
                    "full_name": "Alex Mercer",
                    "email": "demo@pocketsmart.ai",
                    "password_hash": _hash_password("DemoPass123!"),
                    "currency": "$",
                    "created_at": datetime.now().isoformat(),
                    "preferences": {
                        "decor_style": "Modern Minimalist",
                        "favorite_metal": "18K Gold",
                        "budget_range": "Medium"
                    }
                }
            },
            "sessions": {},
            "history": [
                {
                    "id": "rec-hist-1",
                    "user_email": "demo@pocketsmart.ai",
                    "type": "Home Interior",
                    "title": "Minimalist Living Room Makeover",
                    "budget": 650.00,
                    "currency": "$",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "summary": "4 items curated across IKEA & Wayfair saving $110."
                },
                {
                    "id": "rec-hist-2",
                    "user_email": "demo@pocketsmart.ai",
                    "type": "Party Planner",
                    "title": "30th Birthday Garden Gathering",
                    "budget": 850.00,
                    "currency": "$",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "summary": "Rooftop terrace + catering for 30 guests under budget."
                }
            ]
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(default_db, f, indent=2)
        return default_db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": {}, "sessions": {}, "history": []}


def _save_db(data: Dict[str, Any]):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def register_user(full_name: str, email: str, password: str, currency: str = "$") -> Dict[str, Any]:
    db = _get_db()
    clean_email = email.lower().strip()
    if clean_email in db["users"]:
        return {"success": False, "message": "An account with this email already exists."}
    
    user_id = f"u-{uuid.uuid4().hex[:8]}"
    db["users"][clean_email] = {
        "id": user_id,
        "full_name": full_name.strip(),
        "email": clean_email,
        "password_hash": _hash_password(password),
        "currency": currency,
        "created_at": datetime.now().isoformat(),
        "preferences": {}
    }
    _save_db(db)
    
    token = create_session(clean_email)
    return {
        "success": True,
        "message": "Account created successfully.",
        "token": token,
        "user": {
            "id": user_id,
            "full_name": full_name.strip(),
            "email": clean_email,
            "currency": currency
        }
    }


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    db = _get_db()
    clean_email = email.lower().strip()
    user = db["users"].get(clean_email)
    if not user or user.get("password_hash") != _hash_password(password):
        return {"success": False, "message": "Invalid email or password."}
    
    token = create_session(clean_email)
    return {
        "success": True,
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "currency": user.get("currency", "$")
        }
    }


def create_session(email: str) -> str:
    db = _get_db()
    token = f"pkst_{uuid.uuid4().hex}"
    db["sessions"][token] = {
        "email": email.lower().strip(),
        "created_at": time.time(),
        "expires_at": time.time() + (7 * 86400)
    }
    _save_db(db)
    return token


def validate_session(token: Optional[str]) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    db = _get_db()
    session = db["sessions"].get(token)
    if not session:
        return None
    if time.time() > session.get("expires_at", 0):
        del db["sessions"][token]
        _save_db(db)
        return None
    user = db["users"].get(session["email"])
    if not user:
        return None
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "currency": user.get("currency", "$"),
        "preferences": user.get("preferences", {})
    }


def revoke_session(token: str) -> bool:
    db = _get_db()
    if token in db["sessions"]:
        del db["sessions"][token]
        _save_db(db)
        return True
    return False


def save_recommendation_history(
    user_email: str,
    plan_type: str,
    title: str,
    budget: float,
    currency: str,
    summary: str,
    details: Dict[str, Any]
) -> Dict[str, Any]:
    db = _get_db()
    entry_id = f"hist-{uuid.uuid4().hex[:8]}"
    record = {
        "id": entry_id,
        "user_email": user_email.lower().strip() if user_email else "guest@pocketsmart.ai",
        "type": plan_type,
        "title": title,
        "budget": budget,
        "currency": currency,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary": summary,
        "details": details
    }
    db["history"].insert(0, record)
    if len(db["history"]) > 100:
        db["history"] = db["history"][:100]
    _save_db(db)
    return record


def get_user_history(user_email: Optional[str] = None) -> List[Dict[str, Any]]:
    db = _get_db()
    if not user_email:
        return db.get("history", [])
    clean_email = user_email.lower().strip()
    return [h for h in db.get("history", []) if h.get("user_email") == clean_email or h.get("user_email") == "guest@pocketsmart.ai"]
