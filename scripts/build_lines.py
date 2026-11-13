#!/usr/bin/env python3
"""Linienverläufe der Wiener Linien (Stadt Wien OEFFLINIENOGD) für „Nächstes Öffi“.
Ausgabe: {"seg": [[[lon,lat],...],...], "lines": {"tram:25": [i,...], ...}} – vereinfacht und gerundet."""
import json, sys

GROUP = {"Straßenbahn": "tram", "U-Bahn": "metro", "Stadtbus": "bus", "Rufbus Tag": "bus",
         "Nachtbus": "night", "Rufbus Nacht": "night", "Badner Bahn": "wlb"}


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = (dx * dx + dy * dy) ** 0.5 or 1e-12
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[: idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def main(src, dst):
    feats = json.load(open(src, encoding="utf-8"))["features"]
    seg, lines = [], {}
    for f in feats:
        p, g = f["properties"], f.get("geometry")
        grp = GROUP.get(p.get("LTYPTXT"))
        if not grp or not g or g["type"] != "LineString":
            continue
        c = rdp([(x * 1.5, y) for x, y in g["coordinates"]], 0.00004)  # Länge grob entzerrt
        c = [[round(x / 1.5, 5), round(y, 5)] for x, y in c]
        i = len(seg)
        seg.append(c)
        for n in str(p.get("LBEZEICHNUNG") or "").split(","):
            n = n.strip()
            if n:
                lines.setdefault(f"{grp}:{n}", []).append(i)
    json.dump({"seg": seg, "lines": lines}, open(dst, "w", encoding="utf-8"), separators=(",", ":"))
    print(f"{len(lines)} Linien, {len(seg)} Abschnitte, {sum(len(s) for s in seg)} Punkte")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
