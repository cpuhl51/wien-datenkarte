"""Zählt aus dem Fahrplan (GTFS) der Wiener Linien, wie viele Fahrten laut Plan
gerade in jedem Bezirk unterwegs sind – in 10-Minuten-Schritten für zwei Tage.

Aufruf: python3 gtfs_count.py <gtfs-ordner> <bezirke.json> <ausgabe.json> [YYYY-MM-DD]
Ergebnis: {"days": {"2026-11-03": {"0": [[...24]*144], "1": ..., "3": ...}}, ...}
  Schlüssel = route_type (0 Straßenbahn, 1 U-Bahn, 3 Bus), Liste = 144 Zeitschritte,
  je Zeitschritt [Wien gesamt, Bez. 1 .. 23]. Position zwischen zwei Haltestellen
  wird linear zwischen den Haltestellen-Koordinaten angenommen.
"""
import csv, json, sys, os
from datetime import date, datetime, timedelta

gdir, geo_path, out = sys.argv[1:4]
start = date.fromisoformat(sys.argv[4]) if len(sys.argv) > 4 else datetime.now().date()
DAYS = [start, start + timedelta(days=1)]
STEP = 10                      # Minuten
SLOTS = 24 * 60 // STEP
AGENCY = "04"                  # Wiener Linien
TYPES = {"0", "1", "3"}

geo = json.load(open(geo_path))
polys = []                     # (bezirk, bbox, äußerer Ring, Löcher)
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


rd = lambda name: csv.DictReader(open(os.path.join(gdir, name), encoding="utf-8-sig"))

# Welche Betriebstage gelten an welchem Datum
wd = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
service_days = {}              # service_id -> set(datum)
needed = [DAYS[0] - timedelta(days=1)] + DAYS
for r in rd("calendar.txt"):
    s, e = r["start_date"], r["end_date"]
    for d in needed:
        ds = d.strftime("%Y%m%d")
        if s <= ds <= e and r[wd[d.weekday()]] == "1":
            service_days.setdefault(r["service_id"], set()).add(d)
for r in rd("calendar_dates.txt"):
    d = datetime.strptime(r["date"], "%Y%m%d").date()
    if d in needed:
        if r["exception_type"] == "1":
            service_days.setdefault(r["service_id"], set()).add(d)
        else:
            service_days.get(r["service_id"], set()).discard(d)

rtype = {r["route_id"]: r["route_type"] for r in rd("routes.txt") if r["agency_id"] == AGENCY and r["route_type"] in TYPES}
trips = {}                     # trip_id -> (typ, [servicetage])
for r in rd("trips.txt"):
    t = rtype.get(r["route_id"])
    ds = service_days.get(r["service_id"])
    if t and ds:
        trips[r["trip_id"]] = (t, sorted(ds))

stops = {r["stop_id"]: (float(r["stop_lon"]), float(r["stop_lat"])) for r in rd("stops.txt")}
stop_b = {k: district(*v) for k, v in stops.items()}

res = {d.isoformat(): {t: [[0] * 24 for _ in range(SLOTS)] for t in sorted(TYPES)} for d in DAYS}
mins = lambda s: int(s[:-6]) * 60 + int(s[-5:-3])


def add(svc_day, typ, m, b):
    """m = Minuten ab Mitternacht des Betriebstags (kann > 24 h sein)."""
    d = svc_day + timedelta(days=m // 1440)
    key = d.isoformat()
    if key in res:
        slot = res[key][typ][(m % 1440) // STEP]
        slot[0] += 1
        if b:
            slot[b] += 1


def flush(tid, seq):
    if tid not in trips or len(seq) < 2:
        return
    typ, sdays = trips[tid]
    seq.sort()
    for i in range(len(seq)):
        _, arr, dep, sid = seq[i]
        # Stehzeit an der Haltestelle
        for t in range(-(-arr // STEP) * STEP, dep, STEP):
            for d in sdays:
                add(d, typ, t, stop_b.get(sid, 0))
        if i + 1 < len(seq):
            _, arr2, _, sid2 = seq[i + 1]
            b1, b2 = stop_b.get(sid, 0), stop_b.get(sid2, 0)
            for t in range(-(-dep // STEP) * STEP, arr2, STEP):
                if b1 == b2:
                    b = b1
                else:          # zwischen zwei Bezirken: Position linear schätzen
                    f = (t - dep) / (arr2 - dep) if arr2 > dep else 0
                    (x1, y1), (x2, y2) = stops.get(sid, (0, 0)), stops.get(sid2, (0, 0))
                    b = district(x1 + (x2 - x1) * f, y1 + (y2 - y1) * f)
                for d in sdays:
                    add(d, typ, t, b)


cur, seq = None, []
for r in rd("stop_times.txt"):
    tid = r["trip_id"]
    if tid != cur:
        flush(cur, seq)
        cur, seq = tid, []
    if tid in trips:
        seq.append((int(r["stop_sequence"]), mins(r["arrival_time"]), mins(r["departure_time"]), r["stop_id"]))
flush(cur, seq)

feed = max(datetime.fromtimestamp(os.path.getmtime(os.path.join(gdir, "stop_times.txt"))).date(), date.min)
json.dump({"days": res, "step": STEP, "feed": feed.isoformat(), "trips": len(trips)},
          open(out, "w"), separators=(",", ":"))
for d in DAYS:
    k = d.isoformat()
    for t in sorted(TYPES):
        peak = max(res[k][t], key=lambda s: s[0])
        print(k, "Typ", t, "Spitze Wien:", peak[0], "um", f"{res[k][t].index(peak) * STEP // 60:02d}:{res[k][t].index(peak) * STEP % 60:02d}")
