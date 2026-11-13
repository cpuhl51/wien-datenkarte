# Übergabe: technischer Stand „Wien live - Daten & Zahlen“

Stand: 11.11.2026 · Für neue Chats in diesem Projekt (z. B. Widget). Zuerst lesen, dann `git pull`.

## Quellen der Wahrheit
- **Repo:** github.com/cpuhl51/wien-datenkarte (main). Immer vor Änderungen `git pull`, kleine Commits, sofort pushen – es arbeiten ggf. mehrere Chats am selben Repo.
- **Web-App:** https://app.wien-live-daten.puhl.ch (GitHub Pages aus `docs/`, Domain per CNAME bei all-inkl)
- **Betrieb/Server/Cloudflare:** Projekt-Doc `claude/infos-app-betrieb.md`
- **Play Store Schritte:** Projekt-Doc `claude/play-store-anleitung.md`

## Web-App
- Quelltext: `web/template.html` (eine Datei, SVG-Karte, Vanilla JS). Bauen: `scripts/build_page.py` → `docs/index.html`. Gesamt: `scripts/build_all.sh` (Daten, Geo, Seite).
- Nächtlich: GitHub Action `daten-update.yml` (03:17 Wien) holt Open Data und baut neu.
- Live-Quellen im Browser: Cloudflare Worker `wien-stoerungen.cpuhl51.workers.dev` (`/` Störungen, `/monitor?stopId=` Abfahrten; Code `live/worker.js`), nextbike GBFS (Leihräder), data.wien.gv.at WFS (Baustellen).
- Service Worker `docs/sw.js`, Manifest `docs/manifest.webmanifest` (Version per `?v=`).
- Datenschutz: `docs/datenschutz.html` und Info-Seite in der App (#info) – bei neuen Datenflüssen beide anpassen.
- Testen: lokal `docs/` per http-Server, Playwright (Chromium vorinstalliert); Testbilder nie ins Repo legen.

## Android (Trusted Web Activity)
- Projekt im Repo unter `android/` (Bubblewrap-Gerüst, android-browser-helper). Paketname **ch.puhl.wienaktuell**, App-Name „Wien live - Daten & Zahlen“, Launcher „Wien live“.
- Aktuell: **versionName 1.3.0, versionCode 2** (mit Widget; 1.0.0/Code 1 war die erste Play-Einreichung), minSdk 24, targetSdk und compileSdk 36. Fallback ohne TWA-Browser: Custom Tabs.
- **Für jede neue .aab versionCode erhöhen** (in `android/app/build.gradle` und `android/twa-manifest.json`).
- Bauen (Cloud-Container): JDK 17 (`apt install openjdk-17-jdk-headless`), Android cmdline-tools + `platforms;android-36`, `build-tools;35.0.0`; `local.properties` mit `sdk.dir`; `./gradlew bundleRelease`. Maven Central blockt mit 429 → im `build.gradle` Mirror `https://maven-central.storage-download.googleapis.com/maven2/` statt `mavenCentral()` (bereits so im Repo).
- Signieren: `jarsigner -sigalg SHA256withRSA -digestalg SHA-256` mit **upload-key.jks**, Alias `upload`. Schlüssel + Passwort sind **nicht im Repo**, sondern bei Christoph (ZIP „wien-live-playstore“); für einen neuen Build muss er sie hochladen.
- Upload-Schlüssel SHA-256: `79:4B:83:5C:5B:2C:F7:FF:A6:98:4A:51:15:C2:79:E9:A6:F2:C5:84:A4:44:A9:52:6D:18:83:8B:29:AB:11:5C`
- `docs/.well-known/assetlinks.json` enthält bisher nur den Upload-Schlüssel. **Offen:** SHA-256 des Google-App-Signaturschlüssels (Play Console → App-Integrität) ergänzen, sonst Adressleiste in der Play-Version.

## Home-Screen-Widget (seit 1.3.0 eingebaut)
- Code: `WienWidget.java` (Provider, Knöpfe), `WidgetRefreshActivity.java` (Standort nur beim Tippen auf ↻), `WidgetData.java` (Daten + Kartenbild aus basemap-Kacheln). Layout `res/layout/widget_wien.xml`.
- Daten: `docs/haltestellen.json`, `docs/widget-punkte.json` (Taxi, Trinkbrunnen; `scripts/build_widget.py`), Wiener-Linien-Monitor direkt, nextbike GBFS.
- Testen ohne Emulator: `./gradlew testReleaseUnitTest` (Robolectric, zeichnet Bilder nach `app/build/widget-test/`).
- App-Direktaufruf: `#ebene=next|taxi|bike|infra:brunnen`.

## Frühere Überlegungen zum Widget
- Ein Android-Widget ist **nativer Code** (AppWidgetProvider, Layout, ggf. WorkManager) im `android/`-Projekt – die TWA allein kann keine Widgets. Daten am besten direkt von denselben Quellen/Worker holen (JSON), Klick auf das Widget öffnet die TWA mit passender URL (z. B. `/#layer=next`).
- Braucht eine neue .aab (versionCode 2) und neue Prüfung durch Google; neue Datenflüsse in Datenschutzerklärung und Play-„Datensicherheit“ nachtragen.
- Standort im Widget würde eine Android-Standortberechtigung in der App erfordern (bisher keine) → Datenschutz/Play-Angaben ändern sich.

## Laufende Punkte (Stand 11.11.)
- Play Console: App angelegt/Upload durch Christoph; geschlossener Test (12 Tester, 14 Tage) steht an.
- Entscheidung: App gratis (kein Gewerbeschein nötig); Preis ist nach Gratis-Veröffentlichung nicht mehr änderbar.
- Avast meldete die selbst installierte APK als „verdächtig“ (Erkennungs-ID 0bdb783da0e2) – vermutlich wegen Sideload/neuer Signatur; nach Play-Installation prüfen.
