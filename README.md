# Wien aktuell – Statistik und Zahlen

Interaktive Karte der Wiener Gemeindebezirke mit offenen Daten der Stadt Wien:
Einwohner (Frauen/Männer), Alter (Mädchen/Buben), Geburtsland, Nationalität, Geburten, Sterbefälle, Bildungsstand, Kfz, Hunde,
Fundtiere, Öffis unterwegs laut Fahrplan, Öffi-Störungen (Wiener Linien), Automarken, Müll-Sammelstellen und öffentliche Einrichtungen als Punkte, das antike Wien, das Legionslager Vindobona mit Grabungsbefunden, die mittelalterliche Stadtmauer und Wien-Wahl 2025. Mit Jahresregler, „Wien gesamt“
und Datenstand bei jeder Ebene.

Zuerst Web-App (GitHub Pages), später Android-App im Google Play Store.

## Aufbau

| Ordner | Inhalt |
|---|---|
| `web/template.html` | Die App: eine einzige HTML-Seite, Daten werden beim Bauen eingesetzt |
| `scripts/fetch.sh` | Lädt die Rohdaten der Stadt Wien nach `data/raw` |
| `scripts/build_data.py` | Bereitet die Rohdaten zu `data/data.json` auf |
| `scripts/gtfs_count.py` | Zählt aus dem Fahrplan der Wiener Linien die Fahrten pro Bezirk, alle 10 Minuten, für heute und morgen |
| `live/` | Cloudflare Worker für Live-Störungen, mit Anleitung |
| `scripts/build_geo.py` | Standorte je Bezirk zählen, historische Flächen vereinfachen (`docs/punkte.json`, `docs/befunde.json`, werden bei Bedarf geladen) |
| `scripts/build_page.py` | Baut `docs/index.html` (das ist die veröffentlichte Seite) |
| `data/geo/` | Bezirksgrenzen und berechnete Flächen |
| `data/fundtiere/archiv.json` | Sammelt jede Fundtier-Meldung, auch nach Ablauf der 30 Tage im Feed |
| `.github/workflows/daten-update.yml` | Läuft jede Nacht und aktualisiert Daten und Seite |

## Lokal bauen

```bash
bash scripts/fetch.sh
TZ=Europe/Vienna python3 scripts/gtfs_count.py data/raw/gtfs data/geo/bezirke.json data/raw/fahrten.json
python3 scripts/build_data.py data/raw data/data.json data/geo/flaechen.json data/fundtiere/archiv.json
python3 scripts/build_geo.py data/raw/wfs data/geo/bezirke.json data/geo_punkte.json docs/befunde.json
python3 scripts/build_page.py
```

## Quellen und Lizenz der Daten

- Stadt Wien – data.wien.gv.at, Lizenz CC BY 4.0 (Aufbereitung MA 23 auf Basis Statistik Austria;
  Hundebestand und Fundtiere: MA 60; Hundeattacken: MA 58)
- Bezirksgrenzen: Statistik Austria, über
  [ginseng666/GeoJSON-TopoJSON-Austria](https://github.com/ginseng666/GeoJSON-TopoJSON-Austria) (Stand 2021, vereinfacht)
- Wien-Wahl 2025: vienna.at (Bezirke vorläufig, Wien gesamt amtliches Endergebnis vom 8.5.2025)

## Bekannte Einschränkungen

- Die Kurzlinks `wien.gv.at/gogv/…` aus dem Datenkatalog liefern derzeit 404. Das Skript nutzt die direkten Dateipfade.
- Hundeattacken gibt es nur für ganz Wien (2022, 2023). Der Link für 2024 ist bei der Stadt defekt.
- Öffi-Störungen kommen live über den Cloudflare Worker `wien-stoerungen` (siehe `live/`), weil die Wiener-Linien-Schnittstelle keine direkten Browser-Abfragen erlaubt. Fällt er aus, zeigt die App die Momentaufnahme vom letzten Datenlauf.
- „Öffis unterwegs“ zeigt Fahrten laut Fahrplan, keine echten Positionen: Die Wiener Linien veröffentlichen keine Fahrzeugpositionen. Ausfälle und Verspätungen sind nicht enthalten.
- Die Wien-Wahl ist noch ein Einzeljahr und fest in der Vorlage eingetragen.
- Live-Störungen werden nur abgefragt, solange die Seite sichtbar und die Störungs-Ebene gewählt ist (höchstens einmal pro Minute), um im Gratis-Kontingent des Workers zu bleiben.

## Lizenz

Der Code steht unter der [MIT-Lizenz](LICENSE). Die Daten gehören den jeweiligen Quellen
(Stadt Wien: CC BY 4.0) und fallen nicht unter die MIT-Lizenz.
