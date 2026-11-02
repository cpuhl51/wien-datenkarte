"""Setzt Kartengrenzen, Flächen und Daten in die Vorlage ein und schreibt docs/index.html.

Aufruf: python3 scripts/build_page.py
"""
import os
from datetime import date

root = os.path.join(os.path.dirname(__file__), "..")
p = lambda *a: os.path.join(root, *a)

html = open(p("web", "template.html"), encoding="utf-8").read()
for key, path in [("__GEO__", p("data", "geo", "bezirke.json")),
                  ("__AREA__", p("data", "geo", "flaechen.json")),
                  ("__DATA__", p("data", "data.json"))]:
    html = html.replace(key, open(path, encoding="utf-8").read())

d = date.today()
html = html.replace('const ABRUF = "2.11.2026";', f'const ABRUF = "{d.day}.{d.month}.{d.year}";')
open(p("docs", "index.html"), "w", encoding="utf-8").write(html)
print("docs/index.html geschrieben,", len(html) // 1024, "KB")
