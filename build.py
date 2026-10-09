import glob, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "index.html")
JSON_DIR, LOTTIE_DIR = "IDCardRetake Animations - JSON", "IDCardRetake Animations - dotLotiee"

def clean(path):
    return re.sub(r"\s+", " ", os.path.splitext(os.path.basename(path))[0]).strip()

def release(label, folder):
    base = "IDCARDS/Animations/" + folder + "/"
    files = sorted(glob.glob(os.path.join(ROOT, base, JSON_DIR, "*.json")))
    return {"label": label, "anims": [{"name": clean(f), "data": json.load(open(f))} for f in files],
            "downloads": [{"label": "JSON (.zip)", "href": base + JSON_DIR + ".zip"},
                          {"label": "dotLottie (.zip)", "href": base + LOTTIE_DIR + ".zip"}]}

# newest first; "Previous" is the pre-v1.0 set extracted from the old index.html
versions = [
    release("v1.1", "V1.1"),
    release("v1.0", "V1"),
    {"label": "Previous", "anims": json.load(open(os.path.join(ROOT, "previous.json")))},
]

def key(name):
    """Match an animation across versions: 'IDCard - B&W' == 'Black White', 'Forgery v2' == 'Forgery'."""
    k = re.sub(r"^IDCard\s*-\s*", "", name).replace("B&W", "Black White")
    return re.sub(r"\s+v\d+$", "", k).lower()

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
for v, older in zip(versions, versions[1:] + [None]):
    n = notes.get(v["label"], {})
    v["summary"] = n.get("summary", "")
    for x in v["anims"]:
        x["key"] = key(x["name"])
    if older is None:
        continue
    v["vs"] = older["label"]
    prev = {key(x["name"]): x for x in older["anims"]}   # later duplicates win ("Forgery v2" over "Forgery")
    for x in v["anims"]:
        p = prev.pop(x["key"], None)
        x["status"] = "new" if p is None else "same" if p["data"] == x["data"] else "changed"
        if x["status"] != "same":
            x.update(was=p and p["name"], what=["New animation"] if p is None else what(p["data"], x["data"]),
                     why=n.get("why", {}).get(x["name"], ""))
    v["removed"] = sorted(x["name"] for x in prev.values())

data = {
    "versions": versions,
    "samples": sorted(os.path.relpath(f, ROOT) for f in glob.glob(os.path.join(ROOT, "IDCARDS", "*.png"))),
}
tpl = open(os.path.join(ROOT, "template.html")).read()
open(OUT, "w").write(tpl.replace("/*__ANIMS__*/null", json.dumps(data, separators=(",", ":"))))
print("wrote", OUT, os.path.getsize(OUT), "bytes;", ", ".join(f"{v['label']}: {len(v['anims'])}" for v in versions))
for v in versions:
    for x in v["anims"]:
        if "what" in x:
            print(f"  {v['label']} {x['status']:7} {x['name']}: {'; '.join(x['what'])}")
