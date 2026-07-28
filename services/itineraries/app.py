"""
Itineraries microservice – create and list trips for authenticated users.
Port: 5004
"""
import os
import uuid
import datetime

import jwt
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "globetrotter-secret-change-in-prod")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///itineraries.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Itinerary(db.Model):
    __tablename__ = "itineraries"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    destinations = db.Column(JSON, default=list, nullable=False)
    start_date = db.Column(db.String(20), default="")
    end_date = db.Column(db.String(20), default="")
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self):
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


with app.app_context():
    db.create_all()


def get_username_from_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "itineraries"}), 200


@app.post("/itineraries")
def create_itinerary():
    username = get_username_from_token()
    if not username:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    destinations = data.get("destinations", [])

    if not title:
        return jsonify({"error": "title is required"}), 400
    if not isinstance(destinations, list):
        return jsonify({"error": "destinations must be a list"}), 400

    row = Itinerary(
        username=username,
        title=title,
        destinations=destinations,
        start_date=data.get("start_date") or "",
        end_date=data.get("end_date") or "",
        notes=data.get("notes") or "",
    )
    db.session.add(row)
    db.session.commit()
    return jsonify(row.to_dict()), 201


@app.get("/itineraries")
def list_itineraries():
    username = get_username_from_token()
    if not username:
        return jsonify({"error": "authentication required"}), 401

    rows = (
        Itinerary.query.filter_by(username=username)
        .order_by(Itinerary.created_at.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in rows]), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5004)), debug=True)
