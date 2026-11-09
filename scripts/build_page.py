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
import time
_iv = str(int(time.time()))
html = html.replace('const IV = "?v=dev";', f'const IV = "?v={_iv}";')
html = html.replace('const ABRUF = "2.11.2026";', f'const ABRUF = "{d.day}.{d.month}.{d.year}";')
# Rahmen der Seite: ohne Viewport-Angabe zeigen Handys die Desktop-Breite verkleinert an
head = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#111715" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#f3f5f4" media="(prefers-color-scheme: light)">
<link rel="manifest" href="manifest.webmanifest?v=__IV__">
<link rel="icon" type="image/png" sizes="48x48" href="icons/favicon-48.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Wien live">
<script>try{var th=localStorage.getItem("theme");if(th==="light"||th==="dark")document.documentElement.setAttribute("data-theme",th)}catch(e){}</script>
<meta name="description" content="Wiens 23 Bezirke als Karte: Einwohner, Alter, Geburten, Bildung, Öffis und mehr – offene Daten der Stadt Wien.">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font-size:14px}img{max-width:100%}[hidden]{display:none!important}</style>
</head>
<body>
"""
head = head.replace('__IV__', _iv)
cut = html.index("</style>") + len("</style>")      # Titel, Schriften und Styles gehören in den Kopf
html = head.replace("</head>", html[:cut] + "\n</head>") + html[cut:] + "\n</body>\n</html>\n"
open(p("docs", "index.html"), "w", encoding="utf-8").write(html)
# Standorte und historische Flächen werden von der Seite erst bei Bedarf geladen
import shutil
if os.path.exists(p("data", "geo_punkte.json")):
    shutil.copyfile(p("data", "geo_punkte.json"), p("docs", "punkte.json"))
if os.path.exists(p("data", "haltestellen.json")):
    shutil.copyfile(p("data", "haltestellen.json"), p("docs", "haltestellen.json"))
print("docs/index.html geschrieben,", len(html) // 1024, "KB")
