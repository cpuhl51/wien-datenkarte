# Wien live: Testversion → Freigabe → Play Store

**Für Claude, zuerst lesen.** Angepasst aus dem bewährten Ablauf von bUntis!
(`cpuhl51/Buntis`) an Wien live. Stand: 18.11.2026.

App: „Wien live - Daten & Zahlen“ · Repo `cpuhl51/wien-datenkarte` (öffentlich, MIT)
· Paket `ch.puhl.wienaktuell` · Live: https://app.wien-live-daten.puhl.ch
· Web-Version derzeit 1.3.1 · Android-Paket 1.3.0 (versionCode 2, mit Widget).

## Was Christoph will

1. **Claude führt ihn Schritt für Schritt.** Kurze Anweisungen: wo klicken, was
   eintragen. Rückfragen am liebsten per Screenshot.
2. **Testumgebung:** Claude ändert und schiebt auf GitHub. Von dort geht es
   automatisch **nur auf die Testadresse**.
3. **Live erst nach seiner Freigabe:** Christoph startet in GitHub
   „Actions → 2 · Testversion freigeben (live)“ und tippt die Versionsnummer ein.
   **Claude gibt nie selbst live frei.**
4. **Play Store gemeinsam:** Play Console, Store-Eintrag, Datenschutz,
   geschlossener Test, Tester.

## Feste Regeln

- **Passwörter und Schlüssel nie im Chat und nie im Repo:** FTP-Zugang (nur in den
  GitHub Secrets), Upload-Schlüssel `upload-key.jks` samt Passwort. Christoph
  bewahrt sie auf; der Schlüssel wird für **jedes** neue App-Paket gebraucht.
  *(Achtung: Beim ersten Paket stand das Passwort in einer Textdatei im ZIP –
  in den Passwort-Manager verschieben und die Datei löschen.)*
- Claude nicht als Collaborator hinzufügen, Zugriff läuft über die Claude-Sitzung.
- App-Texte: „du / dir / dein“ klein, außer am Satzanfang.
- Unsicheres als **Vermutung** kennzeichnen. Angaben zu Google/Play Console vorher
  prüfen.
- Es gilt der **App-Standard** (Skill `app-standard`).

## Was bei Wien live anders ist als bei bUntis!

| Thema | bUntis! | Wien live |
|---|---|---|
| Hosting | All-Inkl per FTP | **GitHub Pages** aus `docs/` (Domain per CNAME bei All-Inkl) |
| Daten | statisch | **jede Nacht automatisch** (Action `daten-update.yml`, 03:17) + Live-Daten im Browser |
| App-Paket | PWABuilder | **Bubblewrap/Gradle-Projekt im Repo (`android/`)**, weil das Widget nativer Code ist – PWABuilder kann das nicht |
| Schlüssel | PWABuilder-Keystore | `upload-key.jks`, Alias `upload` (von Claude erzeugt, bei Christoph) |
| Play-Erkennung | `/?quelle=play` | bisher über den Referrer `android-app://…`; **auf `/?quelle=play` umstellen** (Start-URL im nächsten Paket) |
| Fremddaten | keine | Stadt Wien (data.wien.gv.at, CC BY 4.0), Wiener Linien (CC BY 4.0), nextbike GBFS (CC0), basemap.at → Quellen stehen in der App, Lizenzliste auf der Info-Seite ergänzen |

## Schritt 1 – Testumgebung

**Vorschlag (zu bestätigen):** Live bleibt auf GitHub Pages, die **Testversion kommt
per FTP auf All-Inkl** – so bleibt Live unangetastet, und die Test-Seite läuft wie bei
bUntis!.

**Christoph macht:**
1. Im KAS von All-Inkl die Subdomain **`beta.wien-live-daten.puhl.ch`** mit eigenem
   Ordner anlegen (SSL/Let's Encrypt aktivieren).
2. Im Repo unter **Settings → Secrets and variables → Actions** vier Secrets:
   `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`, `FTP_DIR_TEST` (Ordner der Beta,
   mit `/` am Ende). `FTP_DIR_LIVE` braucht es nicht, solange Live auf GitHub Pages
   bleibt.

**Claude macht:**
- **Branches:** `main` = Entwicklung/Test, neuer Branch **`live`** = was GitHub Pages
  zeigt (Pages-Quelle: Branch `live`, Ordner `/docs` – das stellt Christoph einmal in
  Settings → Pages um, Claude sagt wann).
- **`test.yml` „1 · Testversion hochladen“:** bei jedem Push auf `main`: prüft, dass
  `version.json`, `VERSION` in `index.html` und Cache-Name in `sw.js` übereinstimmen,
  lädt `docs/` per FTPS (`SamKirkland/FTP-Deploy-Action@v4.4.0`) nach `FTP_DIR_TEST`,
  setzt die Markierung `testversion`.
- **`live.yml` „2 · Testversion freigeben (live)“:** nur von Hand, verlangt die
  Versionsnummer, prüft sie gegen die Markierung `testversion` und schiebt genau
  diesen Stand auf den Branch `live` (→ GitHub Pages), setzt die Markierung `live`.
- **Nächtliche Daten:** `daten-update.yml` aktualisiert **beide** Branches (`live`
  und `main`) – Daten gehen ohne Freigabe live, Programmänderungen nie.
- **Cloudflare Worker:** `beta.wien-live-daten.puhl.ch` als erlaubten Ursprung
  ergänzen (Christoph fügt den neuen Code im Cloudflare-Dashboard ein, Anleitung in
  `infos-app-betrieb.md`).
- **Testversion erkennbar:** `IST_TEST` (Hostname enthält „beta“ oder „test“) →
  oranges Band „Testversion“, Rohdaten zur Fehlersuche nur dort, `.htaccess` mit
  `Header set X-Robots-Tag "noindex, nofollow"` und `<meta name="robots"
  content="noindex">`.
- Nach jedem Push prüfen: Ablauf grün, Beta liefert die neue Versionsnummer.
  Dann Christoph sagen, was neu ist und was er testen soll.

## Schritt 2 – App fit für den Play Store

Erledigt: Manifest mit Icons (maskable), Service Worker, eigene Domain,
`/.well-known/assetlinks.json` (bisher nur Upload-Schlüssel), `datenschutz.html`,
`version.json`, Info-Seite mit Versionsgeschichte, Spendenlink in der Play-Version
ausgeblendet.

Offen:
- `/?quelle=play` als Start-URL, `IST_PLAY` per `sessionStorage`, Spendenlinks als
  `.nur-web` – Zahlungsrichtlinie vor Einreichung erneut prüfen.
- `datenschutz.html`: Abschnitt **„Daten löschen“** ergänzen (Einstellungen liegen nur
  im Browser/Gerät → App-Daten löschen bzw. deinstallieren; Widget-Standort ebenso).
  Kontakt: Christoph Puhl, Wien, apps@puhl.ch, ohne Postadresse.
- Kein Login → kein Demo-Modus nötig.
- **App-Standard-Lücken** (Burger-Menü, Einstellungen mit Stil Zönose/Klassisch und
  Sprache DE/EN, Erststart-Hinweis zur Zönose, Stoffl-Schrift): großer Umbau.
  Vorschlag: **nach** der Store-Freigabe in der Testversion umsetzen – Web-Änderungen
  kommen ohne neues App-Paket in der Play-App an.

## Schritt 3 – Play Console (gemeinsam)

Stand klären: Wurde die App schon angelegt? Wurde 1.0.0 (Code 1) hochgeladen?
Für Neues **immer das Paket 1.3.0 (Code 2, mit Widget)** nehmen.

1. **App erstellen:** „Wien live - Daten & Zahlen“ (26 Zeichen), Deutsch (Österreich),
   App, kostenlos. Kostenlos ist danach endgültig.
2. **App-Inhalte:**
   - Datenschutz-URL `https://app.wien-live-daten.puhl.ch/datenschutz.html`
   - App-Zugriff: alles ohne Login nutzbar
   - Werbung: keine · **Werbe-ID:** nein (Vermutung: das Bubblewrap-Gerüst nutzt sie
     nicht – beim Upload zeigt die Console, ob die Berechtigung erkannt wird)
   - IARC-Fragebogen: überall „Nein“
   - Zielgruppe: zu entscheiden (bUntis! ab 13; 18+ ist am einfachsten)
   - **Datensicherheit:** wegen Widget-Standort „ungefährer Standort, flüchtig
     verarbeitet, optional“ (Vermutung, siehe `play-store-anleitung.md`)
   - Behörden-App: nein (privates Projekt, keine App der Stadt Wien)
   - **KI-generierte Inhalte:** zu klären – wurde das Logo mit KI erstellt?
3. **Store-Eintrag:** Texte in `store-texte.md` (Paket), Symbol 512, Titelbild
   1024×500, 6 Handy-Screenshots vorhanden; **Tablet-Screenshot 2560×1600 fehlt** –
   erstellt Claude. Kategorie „Karten & Navigation“, Kontakt apps@puhl.ch.
4. **App-Paket:** `wien-live-1.3.0.aab` (Bubblewrap, signiert mit `upload-key.jks`).
   Jedes neue Paket: `versionCode` +1, `versionName` = App-Version, gebaut aus
   `android/` (Anleitung in `uebergabe-technik.md`).
5. **Digital Asset Links:** in `docs/.well-known/assetlinks.json` den zweiten
   Fingerabdruck ergänzen (Play Console → App-Integrität → App-Signatur → SHA-256 des
   App-Signaturschlüssels). Ohne ihn zeigt die Play-App eine Adressleiste.
6. **Geschlossener Test:** mind. 12 Tester, 14 Tage am Stück (vor Start prüfen).
   Tester über eine **Google Group**, Vorschlag `wien-live-tester@googlegroups.com`
   (jeder darf beitreten, nur Manager posten). Teilnahme-Link im Reiter „Tester“:
   `https://play.google.com/apps/testing/ch.puhl.wienaktuell` (aktiv nach der ersten
   Prüfung). Länder: AT, optional DE.
7. Nach 14 Tagen **Produktion beantragen**, danach Play-Link in `apps.json` auf
   apps.puhl.ch eintragen (Christoph lädt hoch).

## Was Claude laufend pflegt

- `docs/version.json`, `VERSION` in der App, Cache-Name in `docs/sw.js` – immer gleich.
- `PROJEKT.md` (Änderungsprotokoll), `UEBERGABE.md` (Stand, offene Punkte),
  `android/STORE.md` (Checkliste, Texte, Console-Antworten).
- Projekt-Dokumente im Claude-Projekt (`uebergabe-technik.md`,
  `play-store-anleitung.md`, `infos-app-betrieb.md`).

## Offene Fragen an Christoph

1. Testumgebung wie vorgeschlagen (Live auf GitHub Pages, Beta auf All-Inkl)?
2. Subdomain `beta.wien-live-daten.puhl.ch` ok?
3. Stand in der Play Console?
4. Zielgruppe, KI-Logo, Testergruppe.
