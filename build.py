import glob, json, os, re, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "index.html")
ANIMS = "animations"          # animations/<Name>/v1.json, v2.json, ... (+ optional vN.lottie)

rel = lambda p: os.path.relpath(p, ROOT)
vnum = lambda p: int(re.search(r"v(\d+)\.json$", p)[1])

def what(a, b):
    """Plain-language list of what changed from animation a (old) to b (new)."""
    out, sec = [], lambda d: (d["op"] - d["ip"]) / d["fr"]
    if round(sec(a), 2) != round(sec(b), 2):
        out.append(f"Duration {sec(a):.2f}s → {sec(b):.2f}s")
    if (a["w"], a["h"]) != (b["w"], b["h"]):
        out.append(f"Canvas {a['w']}×{a['h']} → {b['w']}×{b['h']}")
    la, lb = [l.get("nm") for l in a["layers"]], [l.get("nm") for l in b["layers"]]
    if added := [n for n in lb if n not in la]:
        out.append("Added layers: " + ", ".join(added))
    if removed := [n for n in la if n not in lb]:
        out.append("Removed layers: " + ", ".join(removed))
    ia, ib = ({x["id"] for x in d.get("assets", []) if "p" in x} for d in (a, b))
    if ib - ia:
        out.append("Added images: " + ", ".join(sorted(ib - ia)))
    if not out:
        out.append("Same layers and timing; keyframes or styling tweaked")
    return out

notes = json.load(open(os.path.join(ROOT, "notes.json")))
anims = []
for d in sorted(glob.glob(os.path.join(ROOT, ANIMS, "*", ""))):
    name, prev, versions = os.path.basename(d.rstrip("/")), None, []
    for f in sorted(glob.glob(os.path.join(d, "v*.json")), key=vnum):
        v, data = f"v{vnum(f)}", json.load(open(f))
        lottie = f[:-5] + ".lottie"
        versions.append({"v": v, "data": data, "json": rel(f), "lottie": rel(lottie) if os.path.exists(lottie) else None,
                         "note": notes.get(name, {}).get(v, ""), "what": prev and what(prev, data)})
        prev = data
    if versions:
        anims.append({"name": name, "versions": versions[::-1]})   # newest first

# "Download all" = the latest version of every animation. Fixed timestamps keep the zips byte-stable between builds.
def bundle(path, files):
    with zipfile.ZipFile(os.path.join(ROOT, path), "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in files:
            z.writestr(zipfile.ZipInfo(arc, (2020, 1, 1, 0, 0, 0)), open(os.path.join(ROOT, src), "rb").read(), zipfile.ZIP_DEFLATED)
    return path
latest = [(a["name"], a["versions"][0]) for a in anims]
downloads = [
    {"label": "Latest JSON (.zip)", "href": bundle(f"{ANIMS}/latest-json.zip", [(f"{n}.json", v["json"]) for n, v in latest])},
    {"label": "Latest dotLottie (.zip)", "href": bundle(f"{ANIMS}/latest-dotlottie.zip", [(f"{n}.lottie", v["lottie"]) for n, v in latest if v["lottie"]])},
]

# Production default card: IDCARDS/default.png (or .jpg/.webp) replaces the generated placeholder when present.
default = next((f"IDCARDS/default.{e}" for e in ("png", "jpg", "jpeg", "webp") if os.path.exists(os.path.join(ROOT, f"IDCARDS/default.{e}"))), None)
errors_path = os.path.join(ROOT, "errors.json")   # mobile error-drawer copy
data = {
    "anims": anims,
    "errors": json.load(open(errors_path)) if os.path.exists(errors_path) else {},
    "downloads": downloads,
    "default": default,
    "samples": sorted(rel(f) for f in glob.glob(os.path.join(ROOT, "IDCARDS", "*.png"))),
}
tpl = open(os.path.join(ROOT, "template.html")).read()
open(OUT, "w").write(tpl.replace("/*__ANIMS__*/null", json.dumps(data, separators=(",", ":"))))
print("wrote", OUT, os.path.getsize(OUT), "bytes;", ", ".join(f"{a['name']} {a['versions'][0]['v']}" for a in anims))
