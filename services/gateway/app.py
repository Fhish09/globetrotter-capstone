"""
API Gateway – proxies API calls to microservices and serves the frontend.
Port: 5000 (public entry point)

Uses shared HTTP client patterns: timeouts, retries, clear upstream errors.
"""
import os
import sys
import time

import requests
from flask import Flask, request, jsonify, Response, render_template

app = Flask(__name__, template_folder="templates")

AUTH_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth:5001").rstrip("/")
DEST_URL = os.environ.get("DESTINATIONS_SERVICE_URL", "http://destinations:5002").rstrip("/")
REC_URL = os.environ.get("RECOMMENDATIONS_SERVICE_URL", "http://recommendations:5003").rstrip("/")
ITIN_URL = os.environ.get("ITINERARIES_SERVICE_URL", "http://itineraries:5004").rstrip("/")

PROXY_TIMEOUT = float(os.environ.get("PROXY_TIMEOUT", "12"))
PROXY_RETRIES = int(os.environ.get("PROXY_RETRIES", "1"))


def _wants_html() -> bool:
    accept = request.headers.get("Accept", "")
    # Browser navigation sends text/html; fetch/XHR usually prefers application/json
    return "text/html" in accept and "application/json" not in accept.split(",")[0]


def _proxy(base_url: str, path: str = ""):
    url = f"{base_url}{path}"
    if request.query_string:
        url = f"{url}?{request.query_string.decode()}"

    headers = {}
    if "Authorization" in request.headers:
        headers["Authorization"] = request.headers["Authorization"]
    if request.content_type:
        headers["Content-Type"] = request.content_type

    last_err = None
    for attempt in range(PROXY_RETRIES + 1):
        try:
            resp = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.get_data(),
                timeout=PROXY_TIMEOUT,
            )
            excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
            response_headers = [
                (k, v) for k, v in resp.headers.items() if k.lower() not in excluded
            ]
            return Response(resp.content, status=resp.status_code, headers=response_headers)
        except requests.Timeout:
            last_err = "upstream timeout"
        except requests.ConnectionError:
            last_err = "upstream connection refused"
        except requests.RequestException as exc:
            last_err = str(exc)

        if attempt < PROXY_RETRIES:
            time.sleep(0.3 * (attempt + 1))

    return jsonify({
        "error": last_err or "upstream unavailable",
        "upstream": base_url,
    }), 503


@app.get("/health")
def health():
    services = {}
    overall = "ok"
    for name, url in [
        ("auth", AUTH_URL),
        ("destinations", DEST_URL),
        ("recommendations", REC_URL),
        ("itineraries", ITIN_URL),
    ]:
        try:
            r = requests.get(f"{url}/health", timeout=2)
            if r.ok:
                services[name] = r.json()
            else:
                services[name] = {"status": "error", "code": r.status_code}
                overall = "degraded"
        except requests.RequestException:
            services[name] = {"status": "down"}
            overall = "degraded"
    return jsonify({"status": overall, "service": "gateway", "upstream": services}), 200


@app.route("/register", methods=["POST"])
@app.route("/login", methods=["POST"])
@app.route("/me", methods=["GET"])
@app.route("/preferences", methods=["PUT"])
def auth_proxy():
    return _proxy(AUTH_URL, request.path)


@app.route("/destinations", methods=["GET"])
def destinations():
    if _wants_html():
        return render_template("destinations.html")
    return _proxy(DEST_URL, "/destinations")


@app.route("/recommendations", methods=["GET"])
def recommendations():
    if _wants_html():
        return render_template("recommendations.html")
    return _proxy(REC_URL, "/recommendations")


@app.route("/itineraries", methods=["GET", "POST"])
def itineraries():
    if request.method == "GET" and _wants_html():
        return render_template("itineraries.html")
    return _proxy(ITIN_URL, "/itineraries")


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/destinations/<int:dest_id>")
def destination_detail(dest_id):
    return render_template("destination_detail.html", dest_id=dest_id)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
