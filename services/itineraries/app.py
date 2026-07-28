"""
Itineraries microservice – create, list, share trips; popularity stats.
Port: 5004
"""
import os
import sys
import uuid
import datetime
from collections import Counter

import jwt
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

sys.path.insert(0, os.path.dirname(__file__))
try:
    from observability import init_observability
except ImportError:
    def init_observability(app, service_name):
        import logging
        return logging.getLogger(service_name)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "globetrotter-secret-change-in-prod")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///itineraries.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

logger = init_observability(app, "itineraries")
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
    # Sharing
    is_public = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(64), unique=True, nullable=True, index=True)
    shared_with = db.Column(JSON, default=list)  # list of usernames
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self, include_share: bool = True):
        data = {
            "id": self.id,
            "username": self.username,
            "title": self.title,
            "destinations": self.destinations or [],
            "start_date": self.start_date or "",
            "end_date": self.end_date or "",
            "notes": self.notes or "",
            "is_public": bool(self.is_public),
            "shared_with": self.shared_with or [],
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }
        if include_share and self.share_token:
            data["share_token"] = self.share_token
            data["share_url"] = f"/itineraries/shared/{self.share_token}"
        return data


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
        is_public=bool(data.get("is_public", False)),
        shared_with=data.get("shared_with") or [],
    )
    db.session.add(row)
    db.session.commit()
    logger.info("event=itinerary_created username=%s title=%s", username, title)
    return jsonify(row.to_dict()), 201


@app.get("/itineraries")
def list_itineraries():
    username = get_username_from_token()
    if not username:
        return jsonify({"error": "authentication required"}), 401

    owned = Itinerary.query.filter_by(username=username).all()
    # Also itineraries shared with this user
    all_rows = Itinerary.query.all()
    shared = [
        it for it in all_rows
        if username in (it.shared_with or []) and it.username != username
    ]

    result = [it.to_dict() for it in owned]
    for it in shared:
        d = it.to_dict()
        d["shared_from"] = it.username
        result.append(d)

    result.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return jsonify(result), 200


@app.post("/itineraries/<itinerary_id>/share")
def share_itinerary(itinerary_id):
    """Share an itinerary: generate public link and/or add usernames."""
    username = get_username_from_token()
    if not username:
        return jsonify({"error": "authentication required"}), 401

    row = Itinerary.query.filter_by(id=itinerary_id, username=username).first()
    if not row:
        return jsonify({"error": "itinerary not found"}), 404

    data = request.get_json(silent=True) or {}
    make_public = data.get("is_public", True)
    share_with = data.get("shared_with") or []

    if not isinstance(share_with, list):
        return jsonify({"error": "shared_with must be a list of usernames"}), 400

    row.is_public = bool(make_public)
    if row.is_public and not row.share_token:
        row.share_token = uuid.uuid4().hex

    existing = set(row.shared_with or [])
    for u in share_with:
        if isinstance(u, str) and u.strip() and u.strip() != username:
            existing.add(u.strip())
    row.shared_with = list(existing)

    db.session.commit()
    logger.info(
        "event=itinerary_shared id=%s public=%s with=%s",
        itinerary_id, row.is_public, row.shared_with,
    )
    return jsonify(row.to_dict()), 200


@app.get("/itineraries/shared/<token>")
def get_shared_itinerary(token):
    """Public access via share link (no auth required if is_public)."""
    row = Itinerary.query.filter_by(share_token=token).first()
    if not row or not row.is_public:
        return jsonify({"error": "shared itinerary not found"}), 404
    return jsonify(row.to_dict(include_share=False)), 200


@app.get("/internal/past-destinations/<username>")
def past_destinations(username):
    """Destinations that appear in this user's itineraries (for recommendations)."""
    rows = Itinerary.query.filter_by(username=username).all()
    names = []
    for it in rows:
        for d in it.destinations or []:
            if isinstance(d, str) and d.strip():
                names.append(d.strip())
            elif isinstance(d, dict) and d.get("name"):
                names.append(str(d["name"]).strip())
    counts = Counter(names)
    return jsonify({
        "username": username,
        "destinations": [{"name": n, "count": c} for n, c in counts.most_common()],
    }), 200


@app.get("/internal/popular-destinations")
def popular_destinations():
    """Most common destinations across all itineraries."""
    rows = Itinerary.query.all()
    names = []
    for it in rows:
        for d in it.destinations or []:
            if isinstance(d, str) and d.strip():
                names.append(d.strip())
            elif isinstance(d, dict) and d.get("name"):
                names.append(str(d["name"]).strip())
    counts = Counter(names)
    return jsonify([
        {"name": n, "count": c} for n, c in counts.most_common(50)
    ]), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5004)), debug=True)
