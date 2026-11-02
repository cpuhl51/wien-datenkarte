"""Liest die OGD-Dateien der Stadt Wien und schreibt data.json für die Karte.

Aufruf: python3 build_data.py <ordner-mit-rohdaten> <ausgabe.json> <flaechen.json> <fundtier-archiv.json>
Jede Zeitreihe: {jahr: [wien_gesamt, bez1 .. bez23]}  (Index 0 = Wien gesamt)
"""
import csv, json, sys, os, re, html
from datetime import date

src, out, area_path, archive_path = sys.argv[1:5]


def num(s):
    s = (s or "").strip().replace(".", "").replace(",", ".")
    return float(s) if s else None


def read(name):
    with open(os.path.join(src, name + ".csv"), encoding="utf-8-sig", errors="replace") as f:
        lines = f.read().splitlines()
    rows = list(csv.reader(lines[1:], delimiter=";"))
    return [dict(zip(rows[0], r)) for r in rows[1:] if len(r) > 4 and r[1].isdigit()]


def idx(code):
    c = int(code)
    return 0 if c == 90000 else c // 100 - 900


def series(rows, field, agg=False, where=None):
    res, dates, has_total = {}, {}, set()
    for r in rows:
        if where and not where(r):
            continue
        b = idx(r["DISTRICT_CODE"])
        if not 0 <= b <= 23:
            continue
        y = int(r["REF_YEAR"])
        v = num(r[field])
        if v is None:
            continue
        arr = res.setdefault(y, [0.0] * 24)
        arr[b] = arr[b] + v if agg else v
        if b == 0:
            has_total.add(y)
        dates[y] = r["REF_DATE"]
    for y, arr in res.items():          # Wien gesamt fehlt in der Datei -> Summe der Bezirke
        if y not in has_total:
            arr[0] = sum(arr[1:])
    return res, dates


def ratio(num_, den, k=100):
    return {y: [round(k * num_[y][b] / den[y][b], 2) if den[y][b] else 0 for b in range(24)]
            for y in num_ if y in den}


S, D = {}, {}

cob = read("vie-bez-biz-pop-cob-2002f")
S["pop"], D["pop"] = series(cob, "POP_ALL")
parts = {k: series(cob, f)[0] for k, f in [("aut", "POP_COB_AUT"), ("eea", "POP_COB_EEA"), ("tcn", "POP_COB_TCN")]}
for k, v in parts.items():
    S["cob_" + k] = ratio(v, S["pop"])
S["cob_abroad"] = {y: [round(100 - S["cob_aut"][y][b], 2) for b in range(24)] for y in S["cob_aut"]}
D["cob"] = D["pop"]

area = json.load(open(area_path))
area_tot = sum(area.values())
S["dens"] = {y: [round(a[0] / area_tot, 1)] + [round(a[b] / area[str(b)], 1) for b in range(1, 24)] for y, a in S["pop"].items()}

for key, name, field in [("bir", "vie-bez-pop-sex-bir-2002f", "BIR"), ("dea", "vie-bez-pop-sex-dea-2002f", "DEA")]:
    S[key + "_abs"], D[key] = series(read(name), field, agg=True)
    S[key + "_rel"] = ratio(S[key + "_abs"], S["pop"], 1000)   # pro 1.000 Einw. am 1.1. desselben Jahres

edu = read("vie-bez-biz-edu-att-2008f")
for f in ["EDU_ALL", "EDU_LEH", "EDU_BMS", "EDU_AHS", "EDU_BHS", "EDU_KOL", "EDU_ACA", "EDU_UNI", "EDU_AKA"]:
    S["edu_" + f[4:].lower()], D["edu"] = series(edu, f)
S["edu_mat"] = {y: [round(S["edu_ahs"][y][b] + S["edu_bhs"][y][b], 2) for b in range(24)] for y in S["edu_ahs"]}

dog = read("vie-bez-biz-spo-dog-2002f")
S["dog_abs"], D["dog"] = series(dog, "DOG_VALUE")
S["dog_rel"], _ = series(dog, "DOG_DENSITY")

veh = read("veh")
for k, f in [("pkw_abs", "PKW_VALUE"), ("pkw_rel", "PKW_DENSITY"), ("bik_abs", "BIK_VALUE"), ("bik_rel", "BIK_DENSITY")]:
    S[k], D["veh"] = series(veh, f)

age = read("age5")
tot = {}
for grp, sel in [("kid", lambda a: a <= 3), ("sen", lambda a: a >= 14), ("all", lambda a: True)]:
    acc = {}
    for f in ["AUT", "EEA", "REU", "TCN"]:
        s_, D["age"] = series(age, f, agg=True, where=lambda r, sel=sel: sel(int(r["AGE5"])))
        for y, arr in s_.items():
            a = acc.setdefault(y, [0.0] * 24)
            for b in range(24):
                a[b] += arr[b]
    tot[grp] = acc
S["age_kid"] = ratio(tot["kid"], tot["all"])
S["age_sen"] = ratio(tot["sen"], tot["all"])
S["age_avg"], _ = series(read("avgage"), "AGE_AVE")

# Fundtiere: RSS-Feed, Fundort beginnt mit der Bezirksnummer ("15., Auerwelsbachpark")
xml = open(os.path.join(src, "fund.xml"), encoding="utf-8").read()
items = []
for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
    g = lambda tag: html.unescape((re.search(rf"<{tag}>(.*?)</{tag}>", it, re.S) or [None, ""])[1].strip())
    ort = g("vcard:street-address")
    m = re.match(r"\s*(\d{1,2})\.", ort)
    items.append({"id": g("guid"), "t": g("title"), "k": re.sub(r"^\d+_", "", g("description")), "d": g("dc:date"),
                  "s": g("vie:geschlecht"), "f": g("vie:farbe"), "o": ort, "b": int(m.group(1)) if m and 1 <= int(m.group(1)) <= 23 else 0})
# Archiv: jede Fundmeldung bleibt erhalten, auch wenn sie aus dem 30-Tage-Feed fällt
archive = json.load(open(archive_path)) if os.path.exists(archive_path) else []
known = {a["id"] for a in archive}
archive += [i for i in items if i["id"] not in known]
archive.sort(key=lambda i: (i["d"], i["id"]))
json.dump(archive, open(archive_path, "w"), ensure_ascii=False, indent=0)
fund_dates = sorted(i["d"] for i in items if i["d"])


# --- Wiener Linien: aktuelle Störungen, Haltestellen per Punkt-in-Fläche den Bezirken zugeordnet ---
from datetime import datetime, timezone
geo = json.load(open(os.path.join(os.path.dirname(area_path), "bezirke.json")))

def inside(x, y, ring):
    c = False
    for i in range(len(ring)):
        x1, y1 = ring[i]; x2, y2 = ring[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c

def district_of(lon, lat):
    for f in geo["features"]:
        g = f["geometry"]
        for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            if inside(lon, lat, poly[0]) and not any(inside(lon, lat, h) for h in poly[1:]):
                return f["properties"]["b"]
    return 0

stop_bez = {}
hp = os.path.join(src, "haltepunkte.csv")
if os.path.exists(hp):
    for r in csv.DictReader(open(hp, encoding="utf-8-sig"), delimiter=";"):
        try:
            stop_bez[int(r["StopID"])] = district_of(float(r["Longitude"]), float(r["Latitude"]))
        except (ValueError, KeyError):
            pass

wl = None
tp = os.path.join(src, "trafficinfo.json")
if os.path.exists(tp):
    d = json.load(open(tp))["data"]
    cats = {c["id"]: c["name"] for c in d.get("trafficInfoCategories", [])}
    kind = {"stoerungkurz": "kurz", "stoerunglang": "lang", "aufzugsinfo": "aufzug"}
    now = datetime.now(timezone.utc)
    ts = lambda s: datetime.fromisoformat(re.sub(r"([+-]\d\d)(\d\d)$", r"\1:\2", s)) if s else None
    active = []
    for t in d["trafficInfos"]:
        tm = t.get("time") or {}
        st, en = ts(tm.get("start")), ts(tm.get("end"))
        if (st and st > now) or (en and en < now):
            continue                       # nur gerade gültige Meldungen
        bez = sorted({stop_bez.get(s, 0) for s in (t.get("relatedStops") or [])} - {0})
        active.append({"k": kind.get(cats.get(t["refTrafficInfoCategoryId"]), "sonst"),
                       "t": re.sub(r"\s+", " ", t.get("title", "")).strip(),
                       "d": re.sub(r"\s+", " ", t.get("description", "")).strip()[:220],
                       "l": t.get("relatedLines") or (t.get("attributes") or {}).get("relatedLines") or [],
                       "b": bez})
    wl = {"items": active, "fetched": datetime.now().strftime("%Y-%m-%d %H:%M"), "stops": len(stop_bez)}

clean = {k: {str(y): [round(v, 2) for v in arr] for y, arr in sorted(v.items())} for k, v in S.items()}
json.dump({"series": clean,
           "dates": {k: {str(y): d for y, d in v.items()} for k, v in D.items()},
           "fund": {"items": items, "from": fund_dates[0] if fund_dates else "", "to": fund_dates[-1] if fund_dates else "",
                    "fetched": date.today().isoformat(), "archived": len(archive)},
           "wl": wl},
          open(out, "w"), ensure_ascii=False, separators=(",", ":"))
for k, v in clean.items():
    ys = list(v)
    print(f"{k:11s} {ys[0]}–{ys[-1]}  Wien {v[ys[-1]][0]:>10}  Bez.6 {v[ys[-1]][6]}")
print("Störungen aktiv:", len(wl["items"]) if wl else "-", "| Haltestellen zugeordnet:", sum(1 for v in stop_bez.values() if v), "von", len(stop_bez))
print("Fundtiere:", len(items), "ohne Bezirk:", sum(1 for i in items if not i["b"]), fund_dates[:1], fund_dates[-1:])
