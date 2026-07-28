"""
API Gateway – proxies API calls to microservices and serves the frontend.
Port: 5000 (public entry point)
"""
import os

import requests
from flask import Flask, request, jsonify, Response, render_template

app = Flask(__name__, template_folder="templates")

AUTH_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth:5001")
DEST_URL = os.environ.get("DESTINATIONS_SERVICE_URL", "http://destinations:5002")
REC_URL = os.environ.get("RECOMMENDATIONS_SERVICE_URL", "http://recommendations:5003")
ITIN_URL = os.environ.get("ITINERARIES_SERVICE_URL", "http://itineraries:5004")


def _proxy(base_url: str, path: str = ""):
    url = f"{base_url}{path}"
    if request.query_string:
        url = f"{url}?{request.query_string.decode()}"

    headers = {}
    if "Authorization" in request.headers:
        headers["Authorization"] = request.headers["Authorization"]
    if request.content_type:
        headers["Content-Type"] = request.content_type

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            timeout=15,
        )
        excluded = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        response_headers = [
            (k, v) for k, v in resp.headers.items() if k.lower() not in excluded
        ]
        return Response(resp.content, status=resp.status_code, headers=response_headers)
    except requests.RequestException as exc:
        return jsonify({"error": f"upstream unavailable: {exc}"}), 503


@app.get("/health")
def health():
    services = {}
    for name, url in [
        ("auth", AUTH_URL),
        ("destinations", DEST_URL),
        ("recommendations", REC_URL),
        ("itineraries", ITIN_URL),
    ]:
        try:
            r = requests.get(f"{url}/health", timeout=3)
            services[name] = r.json() if r.ok else {"status": "error"}
        except requests.RequestException:
            services[name] = {"status": "down"}
    return jsonify({"status": "ok", "service": "gateway", "upstream": services}), 200


# --- API proxies ---
@app.route("/register", methods=["POST"])
@app.route("/login", methods=["POST"])
@app.route("/me", methods=["GET"])
@app.route("/preferences", methods=["PUT"])
def auth_proxy():
    return _proxy(AUTH_URL, request.path)


@app.route("/destinations", methods=["GET"])
def dest_proxy():
    return _proxy(DEST_URL, "/destinations")


@app.route("/recommendations", methods=["GET"])
def rec_proxy():
    return _proxy(REC_URL, "/recommendations")


@app.route("/itineraries", methods=["GET", "POST"])
def itin_proxy():
    return _proxy(ITIN_URL, "/itineraries")


# --- Frontend pages (same templates as monolith) ---
@app.get("/")
def home():
    return render_template("index.html")


@app.get("/destinations")
def destinations_page():
    # Path conflict: API also uses /destinations.
    # Browser page requests typically Accept: text/html
    accept = request.headers.get("Accept", "")
    if "text/html" in accept and "application/json" not in accept.split(",")[0]:
        return render_template("destinations.html")
    return _proxy(DEST_URL, "/destinations")


@app.get("/destinations/<int:dest_id>")
def destination_detail(dest_id):
    return render_template("destination_detail.html", dest_id=dest_id)


@app.get("/recommendations")
def recommendations_page():
    accept = request.headers.get("Accept", "")
    if "text/html" in accept:
        return render_template("recommendations.html")
    return _proxy(REC_URL, "/recommendations")


@app.get("/itineraries")
def itineraries_page():
    accept = request.headers.get("Accept", "")
    if "text/html" in accept:
        return render_template("itineraries.html")
    return _proxy(ITIN_URL, "/itineraries")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
