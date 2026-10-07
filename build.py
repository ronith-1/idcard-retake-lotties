import glob, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "index.html")
V1 = "IDCARDS/Animations/V1/"
V1_JSON = V1 + "IDCardRetake Animations - JSON"
V1_LOTTIE = V1 + "IDCardRetake Animations - dotLotiee"

def clean(path):
    return re.sub(r"\s+", " ", os.path.splitext(os.path.basename(path))[0]).strip()

# v1.0: one entry per animation in the JSON zip
v1 = [{"name": clean(f), "data": json.load(open(f))} for f in sorted(glob.glob(os.path.join(ROOT, V1_JSON, "*.json")))]

# previous set (extracted from the pre-v1.0 index.html)
old = json.load(open(os.path.join(ROOT, "previous.json")))

data = {
    "versions": [
        {"label": "v1.0", "anims": v1,
         "downloads": [{"label": "JSON (.zip)", "href": V1_JSON + ".zip"}, {"label": "dotLottie (.zip)", "href": V1_LOTTIE + ".zip"}]},
        {"label": "Previous", "anims": old},
    ],
    "samples": sorted(os.path.relpath(f, ROOT) for f in glob.glob(os.path.join(ROOT, "IDCARDS", "*.png"))),
}
tpl = open(os.path.join(ROOT, "template.html")).read()
open(OUT, "w").write(tpl.replace("/*__ANIMS__*/null", json.dumps(data, separators=(",", ":"))))
print("wrote", OUT, os.path.getsize(OUT), "bytes;", len(v1), "v1.0 +", len(old), "previous")
