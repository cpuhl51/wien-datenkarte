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

GROUPS = ["AUT", "EEA", "REU", "TCN"]


def agg5(rows, cols=GROUPS, where=None):
    """Summe über Geschlecht/Altersgruppen; je Jahr [Wien, Bez1..23]."""
    acc = {}
    for f in cols:
        s_, _ = series(rows, f, agg=True, where=where)
        for y, arr in s_.items():
            a = acc.setdefault(y, [0.0] * 24)
            for i in range(24):
                a[i] += arr[i]
    return acc


age = read("age5")
nat = read("nat5")
_, D["age"] = series(age, "AUT", agg=True)
kid = lambda r: int(r["AGE5"]) <= 3
allp = agg5(age)
S["age_kid"] = ratio(agg5(age, where=kid), allp)
S["age_sen"] = ratio(agg5(age, where=lambda r: int(r["AGE5"]) >= 14), allp)
# Geschlecht (1 = Männer, 2 = Frauen) – so in den Daten der Stadt Wien geführt
S["pop_f"] = agg5(age, where=lambda r: r["SEX"] == "2")
S["pop_m"] = agg5(age, where=lambda r: r["SEX"] == "1")
S["pop_fpct"] = ratio(S["pop_f"], allp)
S["kid_f"] = agg5(age, where=lambda r: kid(r) and r["SEX"] == "2")
S["kid_m"] = agg5(age, where=lambda r: kid(r) and r["SEX"] == "1")
# Geburtsland und Nationalität, je 4 Gruppen, Anteil an allen Einwohnern
for pre, rows in [("cob4", age), ("nat4", nat)]:
    tot = agg5(rows)
    for g in GROUPS:
        S[f"{pre}_{g.lower()}"] = ratio(agg5(rows, [g]), tot)
    S[f"{pre}_notaut"] = {y: [round(100 - S[f"{pre}_aut"][y][i], 2) for i in range(24)] for y in tot}
D["nat"] = D["age"]
S["age_avg"], _ = series(read("avgage"), "AGE_AVE")

# Fundtiere: RSS-Feed, Fundort beginnt mit der Bezirksnummer ("15., Auerwelsbachpark")
xml = open(os.path.join(src, "fund.xml"), encoding="utf-8").read()
items = []
for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
    g = lambda tag: html.unescape((re.search(rf"<{tag}(?:\s[^>]*)?>(.*?)</{tag}>", it, re.S) or [None, ""])[1].strip())
    ort = g("vcard:street-address")
    m = re.match(r"\s*(\d{1,2})\.", ort)
    items.append({"id": g("guid"), "t": g("title"), "k": re.sub(r"^\d+_", "", g("description")), "d": g("dc:date"),
                  "s": g("vie:geschlecht"), "f": g("vie:farbe"), "o": ort, "b": int(m.group(1)) if m and 1 <= int(m.group(1)) <= 23 else 0})
# Archiv: jede Fundmeldung bleibt erhalten, auch wenn sie aus dem 30-Tage-Feed fällt
archive = json.load(open(archive_path)) if os.path.exists(archive_path) else []
# frühere Einträge ohne Kennung (Fehler bis 3.11.2026): Kennung aus dem Feed übernehmen oder aus Datum/Tier/Ort bilden
_fid = {(i["d"], i["t"], i["o"]): i["id"] for i in items}
for a_ in archive:
    if not a_.get("id"):
        a_["id"] = _fid.get((a_["d"], a_["t"], a_["o"])) or f'{a_["d"]}|{a_["t"]}|{a_["o"]}'
_seen = set(); archive = [a_ for a_ in archive if not (a_["id"] in _seen or _seen.add(a_["id"]))]
known = {a["id"] for a in archive}
archive += [i for i in items if i["id"] not in known]
archive.sort(key=lambda i: (i["d"], i["id"]))
json.dump(archive, open(archive_path, "w"), ensure_ascii=False, indent=0)
# Ungefähre Lage der Fundorte: Straße/Park über den Adress-Service der Stadt Wien (OGD), Ergebnis wird zwischengespeichert.
# Der Fundort nennt nur Straße oder Park, keine Hausnummer: der Punkt ist daher die Mitte der Straße bzw. des Parks.
import urllib.request, urllib.parse
geo_cache_path = os.path.join(os.path.dirname(archive_path), "geocache.json")
geo_cache = json.load(open(geo_cache_path)) if os.path.exists(geo_cache_path) else {}
geo_fail, geo_new = 0, 0
def geocode(o, b):
    global geo_fail, geo_new
    if o in geo_cache:
        return geo_cache[o]
    if geo_fail >= 3 or geo_new >= 200:
        return None
    name = re.sub(r"^\s*\d{1,2}\.,\s*", "", o).strip()
    if not name:
        return None
    q = name + (f", 1{b:02d}0" if b else "")
    url = "https://data.wien.gv.at/daten/OGDAddressService.svc/GetAddressInfo?" + urllib.parse.urlencode({"Address": q, "crs": "EPSG:4326"})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "wien-datenkarte"}), timeout=15) as r:
            f = json.load(r).get("features") or []
        geo_fail = 0; geo_new += 1
    except Exception:
        geo_fail += 1
        return None
    # nur Treffer im genannten Bezirk (Straßen über mehrere Bezirke: Bezirksliste des Treffers)
    ok = [g for g in f if not b or str(b) in re.split(r"\s*,\s*", str(g.get("properties", {}).get("Bezirk", "")))]
    xy = [round(ok[0]["geometry"]["coordinates"][0], 5), round(ok[0]["geometry"]["coordinates"][1], 5)] if ok else None
    geo_cache[o] = xy
    return xy
for it_ in archive + items:
    if it_.get("o") and "xy" not in it_:
        xy = geocode(it_["o"], it_.get("b", 0))
        if xy:
            it_["xy"] = xy
json.dump(geo_cache, open(geo_cache_path, "w"), ensure_ascii=False, indent=0)
json.dump(archive, open(archive_path, "w"), ensure_ascii=False, indent=0)
print("Fundorte verortet:", sum(1 for i in items if i.get("xy")), "von", len(items), "| neu abgefragt:", geo_new)

fund_stale = False
if not items and archive:
    # Feed gerade leer oder gestört: die letzten 30 Tage aus dem Archiv zeigen
    from datetime import timedelta
    last = max(a["d"][:10] for a in archive if a["d"])
    cut = (date.fromisoformat(last) - timedelta(days=30)).isoformat()
    items = [a for a in archive if a["d"][:10] >= cut]
    fund_stale = True
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
stop_xy = {}
hp = os.path.join(src, "haltepunkte.csv")
if os.path.exists(hp):
    for r in csv.DictReader(open(hp, encoding="utf-8-sig"), delimiter=";"):
        try:
            stop_bez[int(r["StopID"])] = district_of(float(r["Longitude"]), float(r["Latitude"]))
            stop_xy[r["StopID"]] = [round(float(r["Longitude"]), 5), round(float(r["Latitude"]), 5), r["StopText"]]
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
                       "b": bez, "s": sorted({s for s in (t.get("relatedStops") or [])})})
    wl = {"items": active, "fetched": datetime.now().strftime("%Y-%m-%d %H:%M"), "stops": len(stop_bez),
          "stopb": {str(k): v for k, v in stop_bez.items() if v}}

# Haltestellen-Koordinaten für die Karte der Störungen (wird von der Seite erst bei Bedarf geladen)
if stop_xy:
    json.dump(stop_xy, open(os.path.join(os.path.dirname(out), "haltestellen.json"), "w"), ensure_ascii=False, separators=(",", ":"))

# Sterbefälle Wien je Monat: aus Wochenzahlen von Statistik Austria (Wohnort Wien, ohne Auslandssterbefälle).
# Jede Woche wird gleichmäßig auf ihre 7 Tage verteilt; nur vollständig abgedeckte Monate werden ausgegeben.
dea_month = None
wp, kp = os.path.join(src, "gest_woche.csv"), os.path.join(src, "gest_woche_kalender.csv")
if os.path.exists(wp) and os.path.exists(kp):
    from datetime import timedelta
    start = {}
    for r in csv.reader(open(kp, encoding="utf-8-sig"), delimiter=";"):
        m = re.search(r"von (\d+)\.(\d+)\.(\d+)", r[1] if len(r) > 1 else "")
        if m:
            start[r[0]] = date(int(m[3]), int(m[2]), int(m[1]))
    wk = {}
    for r in csv.DictReader(open(wp, encoding="utf-8-sig"), delimiter=";"):
        if r["C-B00-0"] == "B00-9":
            wk[r["C-KALWOCHE-0"]] = wk.get(r["C-KALWOCHE-0"], 0) + int(r["F-ANZ-1"])
    last = max((k for k, v in wk.items() if v > 0), default=None)
    covered_to = start[last] + timedelta(days=6) if last else None
    mon = {}
    for k, v in wk.items():
        if k in start and k <= last:
            for i in range(7):
                d = start[k] + timedelta(days=i)
                mon[(d.year, d.month)] = mon.get((d.year, d.month), 0) + v / 7
    first_day = min(start[k] for k in wk if k in start)
    out_m = {}
    for (y, m), v in mon.items():
        nxt = date(y + (m == 12), m % 12 + 1, 1)
        if date(y, m, 1) >= first_day and nxt - timedelta(days=1) <= covered_to:
            out_m.setdefault(str(y), [None] * 12)[m - 1] = round(v)
    dea_month = {"years": out_m, "to": covered_to.isoformat() if covered_to else ""}

# Pkw-Bestand nach Marken (Stand 31.12.), Anteil der Marke am Pkw-Bestand des Bezirks
brand_rows = read("brand") if os.path.exists(os.path.join(src, "brand.csv")) else []
brands = None
if brand_rows:
    tot, per = {}, {}
    for r in brand_rows:
        b_ = idx(r["DISTRICT_CODE"]); y = int(r["REF_YEAR"]); v = num(r["BRAND_TOTAL"]) or 0
        if not 1 <= b_ <= 23:
            continue
        for key in (b_, 0):
            tot.setdefault(y, [0] * 24)[key] += v
            per.setdefault(r["BRAND"], {}).setdefault(y, [0] * 24)[key] += v
    last = max(tot)
    top = sorted(per, key=lambda k: -per[k].get(last, [0])[0])[:10]
    brands = {"top": top, "date": max(r["REF_DATE"] for r in brand_rows), "share": {}, "ranking": {}}
    for k in top:
        brands["share"][k] = {str(y): [round(100 * per[k].get(y, [0] * 24)[i] / tot[y][i], 2) if tot[y][i] else 0 for i in range(24)] for y in sorted(tot)}
    for i in range(24):              # Top 10 je Bezirk im letzten Jahr
        rk = sorted(((per[k].get(last, [0] * 24)[i], k) for k in per), reverse=True)[:10]
        brands["ranking"][i] = [[k, int(v), round(100 * v / tot[last][i], 1)] for v, k in rk]
    brands["year"] = last

# Häufigste Staatsangehörigkeiten je Bezirk (Stadt Wien, Bericht „Wiener Bevölkerung“, Anhang 7.5)
nat_top = None
tp = os.path.join(src, "nat_top5.html")
if os.path.exists(tp):
    s = open(tp, encoding="utf-8", errors="replace").read()
    nat_top = {}
    for tb in re.findall(r"<table.*?</table>", s, re.S):
        rows = [[html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S)]
                for r in re.findall(r"<tr.*?</tr>", tb, re.S)]
        rows = [r for r in rows if len(r) >= 2 and r[0]]
        if not rows:
            continue
        m = re.match(r"(\d+)\.", rows[0][0])
        key = int(m.group(1)) if m else (0 if rows[0][0].startswith("Wien") else None)
        if key is None:
            continue
        nat_top[key] = [[r[0], int(r[1].replace(".", "")), r[2]] for r in rows[1:] if r[1].replace(".", "").isdigit()]

# Römisches Legionslager Vindobona (Stadtarchäologie Wien): Geometrien kompakt, Koordinaten auf ~1 m gerundet
vin = None
# Gemeinderatswahlen 2005–2020: Stadt Wien (MA 62), Ergebnisse je Wahlsprengel inkl. Wahlkarten, je Bezirk summiert
VOTE_KEYS = {"SPOE": "SPÖ", "FPOE": "FPÖ", "OEVP": "ÖVP", "GRUE": "Grüne", "NEOS": "NEOS"}
votes = {}
for code, year in [("051", 2005), ("101", 2010), ("151", 2015), ("201", 2020)]:
    fp_ = os.path.join(src, "wahl", f"gr{code}.csv")
    if not os.path.exists(fp_):
        continue
    rows = list(csv.reader(open(fp_, encoding="latin1"), delimiter=";"))
    h = [c.strip() for c in rows[0]]
    gi, pi = h.index("ABG."), h.index("UNG.")
    parties = [(i, c) for i, c in enumerate(h) if i > pi and c]
    tot = [dict() for _ in range(24)]
    for r in rows[1:]:
        if len(r) <= pi or not r[7].strip():
            continue
        b = int(r[7])
        for i, c in parties:
            v = int(r[i] or 0) if r[i].strip() else 0
            for k in (0, b):
                tot[k][c] = tot[k].get(c, 0) + v
    for k, name in list(VOTE_KEYS.items()) + [("_", "Sonstige")]:
        arr = []
        for b in range(24):
            g = sum(tot[b].values())
            v = sum(x for c, x in tot[b].items() if c not in VOTE_KEYS) if k == "_" else tot[b].get(k)
            arr.append(round(100 * v / g, 1) if g and v is not None else None)
        votes.setdefault(name, {})[str(year)] = arr

vd = os.path.join(src, "vindobona")
if os.path.isdir(vd):
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], list) else [round(c[0], 5), round(c[1], 5)]

    def dedup(c):
        if isinstance(c[0], list) and not isinstance(c[0][0], list):
            out = [c[0]]
            for p in c[1:]:
                if p != out[-1]:
                    out.append(p)
            return out
        return [dedup(x) for x in c]
    vin = {"date": ""}
    for key, layer_name, props in [("fort", "FORTIFIKATIONOGD", ["BEZEICHNUNG", "ANSPRACHE_TXT", "KATEGORIE_TXT"]),
                                   ("via", "HAUPTSTRARCHOGD", ["BEZEICHNUNG"]),
                                   ("kas", "KASERNEOGD", ["LAGE_TXT", "KOHORTE_TXT"]),
                                   ("bau", "LAGERBAUOGD", ["ANSPRACHE_TXT"])]:
        p = os.path.join(vd, layer_name + ".json")
        if not os.path.exists(p):
            continue
        fs = json.load(open(p))["features"]
        vin[key] = [{"t": f["geometry"]["type"], "c": dedup(rnd(f["geometry"]["coordinates"])),
                     "p": [f["properties"].get(k) for k in props]} for f in fs]
        vin["date"] = max(vin["date"], max((f["properties"].get("UPDATE_DATUM") or "")[:10] for f in fs))

# Fahrplan-Zählung (scripts/gtfs_count.py), optional
fp = os.path.join(src, "fahrten.json")
fahrten = json.load(open(fp)) if os.path.exists(fp) else None

clean = {k: {str(y): [round(v, 2) for v in arr] for y, arr in sorted(v.items())} for k, v in S.items()}
json.dump({"series": clean,
           "dates": {k: {str(y): d for y, d in v.items()} for k, v in D.items()},
           "fund": {"items": items, "from": fund_dates[0] if fund_dates else "", "to": fund_dates[-1] if fund_dates else "",
                    "fetched": date.today().isoformat(), "archived": len(archive), "stale": fund_stale},
           "wl": wl, "fahrten": fahrten, "dea_month": dea_month, "brands": brands, "nat_top": nat_top, "vindobona": vin, "votes": votes},
          open(out, "w"), ensure_ascii=False, separators=(",", ":"))
for k, v in clean.items():
    ys = list(v)
    print(f"{k:11s} {ys[0]}–{ys[-1]}  Wien {v[ys[-1]][0]:>10}  Bez.6 {v[ys[-1]][6]}")
print("Störungen aktiv:", len(wl["items"]) if wl else "-", "| Haltestellen zugeordnet:", sum(1 for v in stop_bez.values() if v), "von", len(stop_bez))
print("Fundtiere:", len(items), "ohne Bezirk:", sum(1 for i in items if not i["b"]), fund_dates[:1], fund_dates[-1:])
