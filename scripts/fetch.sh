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
  [nat5.csv]=$MA23/vie-bez-pop-sex-age5-stk-nat-geo4-2002f.csv              # Nationalität
  [brand.csv]=$MA23/vie-bez-tec-sex-veh-brd-2011f.csv                       # Pkw nach Marken
  [avgage.csv]=$MA23/vie-bez-biz-pop-age-2002f.csv                        # Durchschnittsalter
  [fund.xml]=https://www.wien.gv.at/fundundvergabetiere/internet/rssfeed.xml  # Fundtiere (30 Tage)
  [gest_woche.csv]=https://data.statistik.gv.at/data/OGD_gest_kalwo_GEST_KALWOCHE_100.csv            # Sterbefälle je Woche (Statistik Austria)
  [gest_woche_kalender.csv]=https://data.statistik.gv.at/data/OGD_gest_kalwo_GEST_KALWOCHE_100_C-KALWOCHE-0.csv  # Wochen-Kalender dazu
  [haltepunkte.csv]=https://www.wienerlinien.at/ogd_realtime/doku/ogd/wienerlinien-ogd-haltepunkte.csv  # Haltestellen
  [trafficinfo.json]=https://www.wienerlinien.at/ogd_realtime/trafficInfoList  # Störungen (Momentaufnahme)
)

for name in "${!FILES[@]}"; do
  url=${FILES[$name]}
  # Fehlerseite (HTML) oder Abbruch: alte Datei behalten; nur wenn es keine gibt, abbrechen
  if curl -fsS --connect-timeout 20 --retry 3 -m 60 -o "$name.tmp" "$url" && ! head -c 400 "$name.tmp" | grep -qiE "<!DOCTYPE html|<html"; then
    mv "$name.tmp" "$name"; echo "ok  $name"
  else
    rm -f "$name.tmp"
    if [ -s "$name" ]; then echo "Warnung: $url liefert gerade keine Daten, alte Datei bleibt"
    else echo "FEHLER: $url liefert keine Daten" >&2; exit 1; fi
  fi
done

# Häufigste Staatsangehörigkeiten je Bezirk (HTML-Tabelle der Stadt Wien, keine Prüfung auf HTML)
# Gemeinderatswahlen 2005–2020 je Wahlsprengel (MA 62)
mkdir -p wahl
for y in 051 101 151 201; do
  [ -s wahl/gr$y.csv ] || curl -fsS --retry 3 -m 60 -o wahl/gr$y.csv "https://www.wien.gv.at/data/ogd/ma62/gr${y}_99999999_9999_spr.csv" || echo "Warnung: Wahl $y nicht geladen"
done
curl -fsS --retry 3 -m 60 -o nat_top5.html "https://www.wien.gv.at/spezial/migration-integration-jugendliche/anhang/top-5-bevolkerungsgruppen-nach-staatsangehorigkeit-in-den-wiener-gemeindebezirken-in-absoluten-zahlen-und-in-percent-der-gesamtbevolkerung-des-bezirks/" || echo "Warnung: Staatsangehörigkeits-Tabelle nicht geladen"

# Geodaten-Server der Stadt (WFS als GeoJSON). Ausfälle brechen den Lauf nicht ab, die alte Datei bleibt.
# Ist der Server nicht erreichbar, werden die restlichen Ebenen übersprungen statt stundenlang zu warten.
WFS="https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&outputFormat=json&typeName=ogdwien:"
wfs_fail=0
wfs_get() {   # $1 = Layer, $2 = Zieldatei
  if [ "$wfs_fail" -ge 2 ]; then echo "Warnung: $1 übersprungen (Geodaten-Server nicht erreichbar), alte Datei bleibt"; return 0; fi
  if curl -fsS --connect-timeout 20 --retry 2 --retry-delay 10 -m 180 -o "$2.tmp" "$WFS$1"; then
    mv "$2.tmp" "$2"; wfs_fail=0
  else
    rm -f "$2.tmp"; wfs_fail=$((wfs_fail+1)); echo "Warnung: $1 nicht geladen, alte Datei bleibt"
  fi
}
# Römisches Legionslager Vindobona
mkdir -p vindobona
for L in FORTIFIKATIONOGD HAUPTSTRARCHOGD KASERNEOGD LAGERBAUOGD; do wfs_get "$L" "vindobona/$L.json"; done
echo "ok  vindobona"
# Standorte und historische Flächen
mkdir -p wfs
for L in MISTPLATZOGD ALTSTOFFSAMMLUNGOGD PROBLEMSTOFFOGD HUNDESACKERLOGD TRINKBRUNNENOGD WCANLAGE2OGD PARKINFOOGD \
         SPIELPLATZPUNKTOGD HUNDEZONEOGD DEFIBRILLATOROGD POLIZEIOGD TAXIOGD \
         ARCHAEOSDLGOGD ARCHAEOSTRASSENOGD MITTELALTBEFESTOGD BEFUNDARCHAEOOGD \
         UBAHNOGD UBAHNHALTOGD FLIESSGEWOGD; do
  wfs_get "$L" "wfs/$L.json"
done
echo "ok  wfs"

# Fahrplan der Wiener Linien (GTFS, ca. 100 MB) – nur für die Fahrplan-Zählung, wird nicht gespeichert
curl -fsS --retry 3 -m 300 -o gtfs.zip https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip
rm -rf gtfs && mkdir gtfs && unzip -q -o gtfs.zip -d gtfs && rm gtfs.zip
echo "ok  gtfs"
