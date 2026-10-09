"""Local server with note editing: python3 serve.py, then open http://localhost:8765/

Serves the folder like `python3 -m http.server`, plus:
  GET  /__edit  -> 204, tells the page to show edit controls (404 on any static host, e.g. Vercel)
  POST /__notes -> {"name", "version", "note"}; writes notes.json and reruns build.py
Binds to 127.0.0.1 only, so nothing else on the network can reach it.
"""
import http.server, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(ROOT, "notes.json")


def apply(notes, body):
    """Set one animation version's changelog note. Raises ValueError on a malformed edit."""
    name, version, note = body.get("name"), body.get("version"), body.get("note")
    if not (isinstance(name, str) and name and isinstance(version, str) and version and isinstance(note, str)):
        raise ValueError("send name, version and note")
    entry = notes.setdefault(name, {})
    if note.strip():
        entry[version] = note.strip()
    else:
        entry.pop(version, None)
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
        n = apply({}, {"name": "A", "version": "v2", "note": " because "})
        assert n == {"A": {"v2": "because"}}, n
        assert apply(n, {"name": "A", "version": "v2", "note": ""}) == {"A": {}}
        for bad in ({}, {"name": "A"}, {"name": "A", "version": "v1"}, {"name": "A", "version": "v1", "note": 3}):
            try: apply({}, bad); raise AssertionError(bad)
            except ValueError: pass
        print("ok")
    else:
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
        print(f"Editing enabled at http://localhost:{port}/")
        http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
