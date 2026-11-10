# Wien live - Daten & Zahlen: Betrieb und Updates

Stand: 8.11.2026

## Adressen
- App: https://app.wien-live-daten.puhl.ch
- Alte Adresse (leitet automatisch weiter): https://cpuhl51.github.io/wien-datenkarte
- Code: https://github.com/cpuhl51/wien-datenkarte (öffentlich, MIT-Lizenz)

## Wie die Teile zusammenspielen
- **GitHub (Repo wien-datenkarte):** Code und aufbereitete Daten. GitHub Pages veröffentlicht den Ordner `docs/` als Website.
- **GitHub Actions („Daten aktualisieren“):** Holt jede Nacht um 03:17 Wiener Zeit die offenen Daten der Stadt Wien, baut die Seite neu und speichert. Läuft automatisch, Fehler kommen per Mail von GitHub.
- **Cloudflare Worker `wien-stoerungen`:** Kleiner Weiterleitungsdienst für die Live-Störungen und die Echtzeit-Abfahrten („Nächstes Öffi“, Pfad `/monitor`) der Wiener Linien. Nötig, weil die Wiener Linien keine direkten Abfragen aus dem Browser erlauben. Speichert 60 Sekunden zwischen, kostenlos. Adresse: https://wien-stoerungen.cpuhl51.workers.dev/ – der Code liegt im Repo unter `live/worker.js`.
- **Leihräder (WienMobil Rad):** Die App fragt die Echtzeitdaten direkt bei nextbike ab (GBFS, CC0-Lizenz, Browser-Abfragen erlaubt), ohne Umweg über Cloudflare. Taxistandplätze kommen jede Nacht aus den offenen Daten der Stadt Wien.
- **Verkehrshindernisse:** Baustellen kommen live aus dem Geodatendienst der Stadt Wien (data.wien.gv.at, Ebenen BAUSTELLENPKTOGD und BAUSTELLENLINOGD, Browser-Abfragen erlaubt). Unfälle/Staus: keine frei zugängliche Live-Quelle.
- **all-inkl (DNS von puhl.ch):** Ein CNAME-Eintrag `app.wien-live-daten` → `cpuhl51.github.io.` verbindet die eigene Adresse mit GitHub. puhl.ch, www.puhl.ch und E-Mail sind davon nicht betroffen.

## Updates
- **Neue Ideen, Fehlerbehebungen, Texte, Farben, Daten:** Code ändern und auf GitHub hochladen. Nach 1–2 Minuten online, auch in der späteren Play-Store-App. Kein Store-Update nötig.
- **Daten:** jede Nacht automatisch.
- **Nur bei Icon, App-Name, Berechtigungen oder der jährlichen Android-Vorgabe von Google** (2026: Android 16 / API 36, Frist 31.8.): neue App-Datei (.aab) bauen und in der Play Console hochladen.

## Play Store (geplant)
- Verpackung als Trusted Web Activity mit Googles Werkzeug Bubblewrap.
- Dafür nötig: Datei `/.well-known/assetlinks.json` unter app.wien-live-daten.puhl.ch (wird beim Verpacken erzeugt).
- Neues privates Entwicklerkonto: vor der ersten Veröffentlichung geschlossener Test mit 12 Testern über 14 Tage.
- Logo (überall, ohne Schriftzug): `assets/logo-original.jpg`, Store-Icon: `assets/playstore-icon-512.png`.

## Sicherheit
- Öffentliches Repo: jeder kann lesen und kopieren, ändern nur Konten mit Schreibrecht (Christoph und die freigegebene Claude-App).
- Zwei-Faktor-Anmeldung bei GitHub und Cloudflare einschalten.
- Claude-Zugriff jederzeit widerrufbar: GitHub → Settings → Applications.

## Cloudflare: Worker aktualisieren (Schritt für Schritt)
Wann nötig: wenn sich die Adresse der App ändert oder `live/worker.js` im Repo geändert wurde.
1. https://dash.cloudflare.com öffnen und anmelden.
2. Links „Workers & Pages“ (bzw. „Compute“ → „Workers & Pages“).
3. In der Liste `wien-stoerungen` antippen.
4. Oben rechts „Edit code“ (Code bearbeiten).
5. Den gesamten Code im Editor markieren und löschen.
6. Den Inhalt von https://github.com/cpuhl51/wien-datenkarte/blob/main/live/worker.js einfügen (dort „Raw“ öffnen, alles kopieren).
7. Oben rechts „Deploy“.
8. Prüfen: In der App „Öffi-Störungen“ wählen – unter der Karte steht „Live, zuletzt aktualisiert …“.
