#!/usr/bin/env bash
# Lädt die Open-Data-Dateien der Stadt Wien nach data/raw.
# Bricht ab, wenn eine Datei fehlt oder statt CSV eine HTML-Fehlerseite kommt,
# damit nie halbe oder falsche Daten veröffentlicht werden.
set -euo pipefail
cd "$(dirname "$0")/../data/raw"

MA23=https://www.wien.gv.at/data/ogd/ma23
declare -A FILES=(
  [vie-bez-biz-pop-cob-2002f.csv]=$MA23/vie-bez-biz-pop-cob-2002f.csv     # Bevölkerung nach Geburtsland
  [vie-bez-pop-sex-bir-2002f.csv]=$MA23/vie-bez-pop-sex-bir-2002f.csv     # Geburten
  [vie-bez-pop-sex-dea-2002f.csv]=$MA23/vie-bez-pop-sex-dea-2002f.csv     # Sterbefälle
  [vie-bez-biz-edu-att-2008f.csv]=$MA23/vie-bez-biz-edu-att-2008f.csv     # Bildungsstand
  [vie-bez-biz-spo-dog-2002f.csv]=$MA23/vie-bez-biz-spo-dog-2002f.csv     # Hundebestand
  [veh.csv]=$MA23/vie-bez-biz-tec-veh-2002f.csv                           # Kraftfahrzeuge
  [age5.csv]=$MA23/vie-bez-pop-sex-age5-stk-cob-geo4-2002f.csv            # Altersgruppen
  [avgage.csv]=$MA23/vie-bez-biz-pop-age-2002f.csv                        # Durchschnittsalter
  [fund.xml]=https://www.wien.gv.at/fundundvergabetiere/internet/rssfeed.xml  # Fundtiere (30 Tage)
  [haltepunkte.csv]=https://www.wienerlinien.at/ogd_realtime/doku/ogd/wienerlinien-ogd-haltepunkte.csv  # Haltestellen
  [trafficinfo.json]=https://www.wienerlinien.at/ogd_realtime/trafficInfoList  # Störungen (Momentaufnahme)
)

for name in "${!FILES[@]}"; do
  url=${FILES[$name]}
  curl -fsS --retry 3 -m 60 -o "$name.tmp" "$url"
  if head -c 400 "$name.tmp" | grep -qi "<!DOCTYPE html"; then
    echo "FEHLER: $url liefert eine HTML-Seite statt Daten" >&2; rm -f "$name.tmp"; exit 1
  fi
  mv "$name.tmp" "$name"
  echo "ok  $name"
done
