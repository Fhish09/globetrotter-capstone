"""Data models – users & itineraries in SQLite/Postgres; destinations in JSON."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON

db = SQLAlchemy()

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_BASE_DIR, "data")
DESTINATIONS_FILE = os.path.join(DATA_DIR, "destinations.json")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    preferences = db.Column(JSON, default=list, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "preferences": self.preferences or [],
        }


class Itinerary(db.Model):
    __tablename__ = "itineraries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    destinations = db.Column(JSON, default=list, nullable=False)
    start_date = db.Column(db.String(20), default="")
    end_date = db.Column(db.String(20), default="")
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "title": self.title,
            "destinations": self.destinations or [],
            "start_date": self.start_date or "",
            "end_date": self.end_date or "",
            "notes": self.notes or "",
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


def get_all_users() -> list:
    return [u.to_dict() for u in User.query.all()]


def get_user_by_username(username: str) -> dict | None:
    user = User.query.filter_by(username=username).first()
    return user.to_dict() if user else None


def save_user(user: dict) -> None:
    record = User(
        id=user.get("id") or str(uuid.uuid4()),
        username=user["username"],
        password_hash=user["password_hash"],
        preferences=user.get("preferences") or [],
    )
    db.session.add(record)
    db.session.commit()


def update_user_preferences(username: str, preferences: list) -> bool:
    user = User.query.filter_by(username=username).first()
    if not user:
        return False
    user.preferences = preferences
    db.session.commit()
    return True


def _read_json(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as fh:
        content = fh.read().strip()
        if not content:
            return []
        return json.loads(content)


def get_all_destinations() -> list:
    return _read_json(DESTINATIONS_FILE)


def get_all_itineraries() -> list:
    return [it.to_dict() for it in Itinerary.query.all()]


def get_itineraries_for_user(username: str) -> list:
    rows = (
        Itinerary.query.filter_by(username=username)
        .order_by(Itinerary.created_at.desc())
        .all()
    )
    return [it.to_dict() for it in rows]


def save_itinerary(itinerary: dict) -> None:
    record = Itinerary(
        id=itinerary.get("id") or str(uuid.uuid4()),
        username=itinerary["username"],
        title=itinerary["title"],
        destinations=itinerary.get("destinations") or [],
        start_date=itinerary.get("start_date") or "",
        end_date=itinerary.get("end_date") or "",
        notes=itinerary.get("notes") or "",
    )
    db.session.add(record)
    db.session.commit()
