import os
from flask import Flask, Response, redirect

app = Flask(__name__)

REDIRECT = "https://www.tashanwin.org/#/register?invitationCode=165813801027"

# Resolve index.html path (located at repo root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")

def _read_index() -> str:
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        # Minimal HTML fallback that redirects
        return f"<!doctype html><meta charset='utf-8'><title>Redirect</title><meta http-equiv='refresh' content='0; url={REDIRECT}'><a href='{REDIRECT}'>Continue</a>"

@app.route("/health")
def health():
    return Response("ok", mimetype="text/plain")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_index(path: str):
    # Serve the static index.html to enable Cosine preview and front-end-only deployment
    html = _read_index()
    return Response(html, headers={"Content-Type": "text/html; charset=utf-8"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)