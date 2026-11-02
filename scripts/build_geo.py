"""Bereitet die Geodaten (Punkte und historische Flächen) der Stadt Wien auf.

Aufruf: python3 build_geo.py <wfs-ordner> <bezirke.json> <ausgabe-geo.json> <ausgabe-befunde.json>
- Punkte (Mistplätze, Trinkbrunnen, …): Zählung je Bezirk per Punkt-in-Fläche, Koordinaten gerundet
- Antike Siedlungen, römische Straßen, mittelalterliche Befestigung: vereinfachte Geometrie
- Archäologische Befunde im Legionslager: eigene Datei, wird erst bei Bedarf geladen
"""
import json, os, sys, re

src, geo_path, out, out_bef = sys.argv[1:5]
geo = json.load(open(geo_path))
polys = []
for f in geo["features"]:
    g = f["geometry"]
    for p in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        xs = [c[0] for c in p[0]]; ys = [c[1] for c in p[0]]
        polys.append((f["properties"]["b"], (min(xs), min(ys), max(xs), max(ys)), p[0], p[1:]))


def inside(x, y, ring):
    c = False
    for i in range(len(ring)):
        x1, y1 = ring[i]; x2, y2 = ring[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def district(x, y):
    for b, (a, b_, c, d), outer, holes in polys:
        if a <= x <= c and b_ <= y <= d and inside(x, y, outer) and not any(inside(x, y, h) for h in holes):
            return b
    return 0


def load(name):
    p = os.path.join(src, name + ".json")
    if not os.path.exists(p):
        return []
    try:
        return json.load(open(p))["features"]
    except (ValueError, KeyError):
        return []


def clean(v):
    v = re.sub(r"\s+", " ", str(v or "")).strip()
    return "" if v in ("None", "null") else v


# Punkt-Datensätze: Schlüssel, Layername, Feld für die Beschriftung (oder None), Ebene
POINTS = [
    ("altstoff", "ALTSTOFFSAMMLUNGOGD", lambda p: " ".join(filter(None, [clean(p.get("STRASSE")), clean(p.get("ONR"))]))),
    ("sackerl", "HUNDESACKERLOGD", lambda p: " ".join(filter(None, [clean(p.get("STRNAM")), clean(p.get("ONRTXT"))]))),
    ("mist", "MISTPLATZOGD", lambda p: clean(p.get("ADRESSE"))),
    ("problem", "PROBLEMSTOFFOGD", lambda p: clean(p.get("ADRESSE"))),
    ("brunnen", "TRINKBRUNNENOGD", lambda p: clean(p.get("BASIS_TYP_TXT"))),
    ("wc", "WCANLAGE2OGD", lambda p: " · ".join(filter(None, [clean(p.get("STRASSE")), clean(p.get("ORTSANGABE")), clean(p.get("OEFFNUNGSZEIT"))]))),
    ("park", "PARKINFOOGD", lambda p: clean(p.get("ANL_NAME"))),
    ("spiel", "SPIELPLATZPUNKTOGD", lambda p: clean(p.get("ANL_NAME"))),
    ("hundezone", "HUNDEZONEOGD", lambda p: " · ".join(filter(None, [clean(p.get("PARK")), clean(p.get("TYP"))]))),
    ("kiga", "KINDERGARTENOGD", lambda p: " · ".join(filter(None, [clean(p.get("BEZEICHNUNG")), clean(p.get("ADRESSE"))]))),
    ("schule", "SCHULEOGD", lambda p: " · ".join(filter(None, [clean(p.get("NAME")), clean(p.get("ART_TXT"))]))),
    ("defi", "DEFIBRILLATOROGD", lambda p: " · ".join(filter(None, [clean(p.get("ADRESSE")), clean(p.get("INFO"))]))),
    ("polizei", "POLIZEIOGD", lambda p: " · ".join(filter(None, [clean(p.get("NAME")), clean(p.get("ADRESSE"))]))),
]
# Altstoff-Sammelstellen zusätzlich je Fraktion (eine Sammelstelle kann mehrere haben)
FRAKTIONEN = [("papier", "FRAKTION_PA"), ("glas", "FRAKTION_G"), ("lvp", "FRAKTION_KV"), ("bio", "FRAKTION_BI")]
alt_label = POINTS[0][2]
for k, fld in FRAKTIONEN:
    POINTS.append((k, ("ALTSTOFFSAMMLUNGOGD", fld), alt_label))

res = {"points": {}, "date": {}}
for key, layer, label in POINTS:
    flt = None
    if isinstance(layer, tuple):
        layer, flt = layer
    fs = load(layer)
    if flt:
        fs = [f for f in fs if str(f["properties"].get(flt)) == "1"]
    if not fs:
        continue
    cnt = [0] * 24
    pts = []
    for f in fs:
        g = f["geometry"]
        if not g or g["type"] != "Point":
            continue
        x, y = g["coordinates"][:2]
        b = district(x, y)
        cnt[b] += 1
        cnt[0] += 1 if b else 0
        pts.append([round(x, 5), round(y, 5), b, label(f["properties"])[:120]])
    res["points"][key] = {"count": cnt, "pts": pts}


def rnd(c, n=5):
    return [rnd(x, n) for x in c] if isinstance(c[0], list) else [round(c[0], n), round(c[1], n)]


def thin(line, d=0.00002):
    """entfernt Punkte, die näher als ~2 m am vorigen liegen"""
    out = [line[0]]
    for p in line[1:]:
        if abs(p[0] - out[-1][0]) > d or abs(p[1] - out[-1][1]) > d:
            out.append(p)
    if out[-1] != line[-1]:
        out.append(line[-1])
    return out


def simp(c, d):
    if isinstance(c[0][0], (int, float)):
        return thin(rnd(c), d)
    return [simp(x, d) for x in c]


HIST = [("siedlung", "ARCHAEOSDLGOGD", ["BEREICH", "INFO"]),
        ("strasse", "ARCHAEOSTRASSENOGD", ["BEZEICHNUNG", "INFO"]),
        ("mittelalter", "MITTELALTBEFESTOGD", ["ANSPRACHE", "ABSCHNITT", "NAME"])]
res["hist"] = {}
for key, layer, props in HIST:
    fs = load(layer)
    res["hist"][key] = [{"t": f["geometry"]["type"], "c": simp(f["geometry"]["coordinates"], 0.00003),
                         "p": [clean(f["properties"].get(k)) for k in props]} for f in fs if f.get("geometry")]

# Fraktionen verweisen auf die Punkte der Altstoff-Sammelstellen statt sie zu kopieren (kleinere Datei)
if "altstoff" in res["points"]:
    pos = {(p[0], p[1], p[3]): i for i, p in enumerate(res["points"]["altstoff"]["pts"])}
    for k, _ in FRAKTIONEN:
        if k in res["points"]:
            res["points"][k] = {"count": res["points"][k]["count"], "ref": "altstoff",
                                "idx": [pos[(p[0], p[1], p[3])] for p in res["points"][k]["pts"]]}

# Orientierung: U-Bahn-Linien und -Stationen, große Gewässer
RIVERS = {"Donau", "Neue Donau", "Donaukanal", "Wienfluss", "Liesingbach"}
res["orient"] = {
    "ubahn": [{"t": f["geometry"]["type"], "c": simp(f["geometry"]["coordinates"], 0.00005), "l": clean(f["properties"].get("LINFO"))}
              for f in load("UBAHNOGD") if f.get("geometry")],
    "stat": [[round(f["geometry"]["coordinates"][0], 5), round(f["geometry"]["coordinates"][1], 5), clean(f["properties"].get("HTXT")), clean(f["properties"].get("LINFO"))]
             for f in load("UBAHNHALTOGD") if f.get("geometry")],
    "fluss": [{"t": f["geometry"]["type"], "c": simp(f["geometry"]["coordinates"], 0.0002), "n": clean(f["properties"].get("NAME"))}
              for f in load("FLIESSGEWOGD") if f.get("geometry") and clean(f["properties"].get("NAME")) in RIVERS],
}

json.dump(res, open(out, "w"), ensure_ascii=False, separators=(",", ":"))

bef = [{"t": f["geometry"]["type"], "c": simp(f["geometry"]["coordinates"], 0.000015),
        "p": clean(f["properties"].get("BEFUND_TYP_TXT"))} for f in load("BEFUNDARCHAEOOGD") if f.get("geometry")]
json.dump(bef, open(out_bef, "w"), ensure_ascii=False, separators=(",", ":"))

for k, v in res["points"].items():
    print(f"{k:10s} {v['count'][0]:5d} Punkte in Wien, ohne Bezirk: {len(v.get('pts', v.get('idx', []))) - v['count'][0]}")
print("historisch:", {k: len(v) for k, v in res["hist"].items()}, "| Befunde:", len(bef),
      "| Größen KB:", os.path.getsize(out) // 1024, os.path.getsize(out_bef) // 1024)
