"""Local server with note editing: python3 serve.py, then open http://localhost:8765/

Serves the folder like `python3 -m http.server`, plus:
  GET  /__edit  -> 204, tells the page to show edit controls (404 on any static host, e.g. Vercel)
  POST /__notes -> {"version", "summary"} or {"version", "name", "why"}; writes notes.json and reruns build.py
Binds to 127.0.0.1 only, so nothing else on the network can reach it.
"""
import http.server, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(ROOT, "notes.json")


def apply(notes, body):
    """Merge one edit into the notes dict. Raises ValueError on a malformed edit."""
    version = body.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("version required")
    entry = notes.setdefault(version, {"summary": "", "why": {}})
    if "summary" in body:
        if not isinstance(body["summary"], str):
            raise ValueError("summary must be text")
        entry["summary"] = body["summary"].strip()
    elif isinstance(body.get("name"), str) and isinstance(body.get("why"), str):
        why = entry.setdefault("why", {})
        if body["why"].strip():
            why[body["name"]] = body["why"].strip()
        else:
            why.pop(body["name"], None)
    else:
        raise ValueError("send summary, or name + why")
    return notes


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")   # always serve the freshly built index.html
        super().end_headers()

    def do_GET(self):
        if self.path == "/__edit":
            self.send_response(204)
            self.end_headers()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != "/__notes":
            return self.send_error(404)
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            notes = apply(json.load(open(NOTES)), body)
        except (ValueError, json.JSONDecodeError) as e:
            return self.send_error(400, str(e))
        with open(NOTES, "w") as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)
            f.write("\n")
        subprocess.run([sys.executable, os.path.join(ROOT, "build.py")], check=True, capture_output=True)
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    if sys.argv[1:] == ["test"]:
        n = apply({}, {"version": "v9", "summary": " s "})
        n = apply(n, {"version": "v9", "name": "A", "why": " because "})
        assert n == {"v9": {"summary": "s", "why": {"A": "because"}}}, n
        assert apply(n, {"version": "v9", "name": "A", "why": ""})["v9"]["why"] == {}
        for bad in ({}, {"version": "v9"}, {"version": "v9", "summary": 3}):
            try: apply({}, bad); raise AssertionError(bad)
            except ValueError: pass
        print("ok")
    else:
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
        print(f"Editing enabled at http://localhost:{port}/")
        http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
