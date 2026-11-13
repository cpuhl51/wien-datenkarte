#!/usr/bin/env bash
# Baut Daten und Seite aus data/raw neu (ohne Herunterladen).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/build_data.py data/raw data/data.json data/geo/flaechen.json data/fundtiere/archiv.json
python3 scripts/build_geo.py data/raw/wfs data/geo/bezirke.json data/geo_punkte.json docs/befunde.json
python3 scripts/build_lines.py data/raw/wfs/OEFFLINIENOGD.json docs/linien.json || echo "Linienverläufe übersprungen"
python3 scripts/build_page.py
python3 scripts/build_widget.py docs/punkte.json docs/widget-punkte.json
