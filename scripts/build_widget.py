#!/usr/bin/env python3
"""Kleine Punktdatei für das Android-Widget: Taxistandplätze und Trinkbrunnen."""
import json, sys

src, dst = sys.argv[1], sys.argv[2]
p = json.load(open(src, encoding="utf-8"))["points"]
out = {k: [[round(x[0], 5), round(x[1], 5), x[3] if len(x) > 3 else ""] for x in p[k]["pts"]] for k in ("taxi", "brunnen") if k in p}
json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print({k: len(v) for k, v in out.items()})
