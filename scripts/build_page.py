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
# Rahmen der Seite: ohne Viewport-Angabe zeigen Handys die Desktop-Breite verkleinert an
head = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#111715" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#f3f5f4" media="(prefers-color-scheme: light)">
<meta name="description" content="Wiens 23 Bezirke als Karte: Einwohner, Alter, Geburten, Bildung, Öffis und mehr – offene Daten der Stadt Wien.">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font-size:14px}img{max-width:100%}[hidden]{display:none!important}</style>
</head>
<body>
"""
cut = html.index("</style>") + len("</style>")      # Titel, Schriften und Styles gehören in den Kopf
html = head.replace("</head>", html[:cut] + "\n</head>") + html[cut:] + "\n</body>\n</html>\n"
open(p("docs", "index.html"), "w", encoding="utf-8").write(html)
print("docs/index.html geschrieben,", len(html) // 1024, "KB")
