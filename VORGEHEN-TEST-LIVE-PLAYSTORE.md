# Wien live: Testversion → Freigabe → Play Store

**Für Claude, zuerst lesen.** Angepasst aus dem bewährten Ablauf von bUntis!
(`cpuhl51/Buntis`) an Wien live. Stand: 18.11.2026.

App: „Wien live - Daten & Zahlen“ · Repo `cpuhl51/wien-datenkarte` (öffentlich, MIT)
· Paket `ch.puhl.wienaktuell` · Live: https://app.wien-live-daten.puhl.ch
· Web-Version 1.3.2 · Android-Paket 1.3.2 (versionCode 2, mit Widget, Start-URL `/?quelle=play`).

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
| Hosting | All-Inkl per FTP | bisher GitHub Pages → **wird auf All-Inkl umgezogen** |
| Daten | statisch | **jede Nacht automatisch** (Action `daten-update.yml`, 03:17) + Live-Daten im Browser |
| App-Paket | PWABuilder | **Bubblewrap/Gradle-Projekt im Repo (`android/`)**, weil das Widget nativer Code ist – PWABuilder kann das nicht |
| Schlüssel | PWABuilder-Keystore | `upload-key.jks`, Alias `upload` (von Claude erzeugt, bei Christoph) |
| Play-Erkennung | `/?quelle=play` | `/?quelle=play` (seit 1.3.2) plus Referrer `android-app://…` |
| Fremddaten | keine | Stadt Wien (data.wien.gv.at, CC BY 4.0), Wiener Linien (CC BY 4.0), nextbike GBFS (CC0), basemap.at → Quellen stehen in der App, Lizenzliste auf der Info-Seite ergänzen |

## Stand 18.11. abends
- Erledigt: Ordner `/wien-live/` + `/wien-live-test/`, Subdomain `beta.` → `/wien-live-test/`
  (SSL wird ausgestellt), `wien-live-daten.puhl.ch` → `/wien-live/`, fünf FTP-Secrets,
  Cloudflare-Worker neu eingesetzt (Beta erlaubt), „1 · Testversion hochladen“ grün.
- Nächstes: Beta prüfen → Schritt 1b (Umzug Live) → Burger-Menü-Entwurf auf Beta →
  Play Console „App erstellen“.
- **Wichtig für den Umzug:** All-Inkl leitet die Adresse `/icons/` auf eigene Server-Symbole um
  → der Bilder-Ordner heißt auf `beta` jetzt `docs/bilder/` (1.4.1). `main` vor dem
  Live-Umzug auf diesen Stand bringen (beta übernehmen), sonst fehlen live alle Symbole.
- Entwurf Burger-Menü (1.4.x) liegt auf Branch `beta`, Christoph findet ihn gut.
- **Achtung bis zum Umzug:** GitHub Pages zeigt noch `main` – jeder Push auf `main`
  ist dort sofort live. Bis zum Umzug nichts Unfertiges auf `main` pushen.

## Schritt 1 – Testumgebung (entschieden: alles auf All-Inkl wie bUntis!)

Live und Test laufen per FTP auf All-Inkl. GitHub Pages wird nach dem Umzug abgeschaltet.

**Christoph macht (KAS von All-Inkl):**
1. Zwei Ordner: `/wien-live/` (Live) und `/wien-live-test/` (Test) – angelegt 18.11.
2. Subdomain **`beta.wien-live-daten.puhl.ch`** anlegen → Ordner `/wien-live-test/`,
   SSL (Let's Encrypt) einschalten.
3. **Noch nicht** die Live-Subdomain umstellen – das machen wir gemeinsam, wenn die
   Live-Dateien schon im Ordner liegen (Schritt 1b).
4. Im Repo unter **Settings → Secrets and variables → Actions** fünf Secrets:
   `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`, `FTP_DIR_TEST`, `FTP_DIR_LIVE`
   (Ordner mit `/` am Ende, so wie der FTP-Zugang sie sieht).

**Claude hat vorbereitet (im Repo):**
- **`test.yml` „1 · Testversion hochladen“:** bei jedem Push auf `main`: prüft
  `version.json` = `VERSION` in `index.html` = Cache-Name in `sw.js`, lädt `docs/` per
  FTPS nach `FTP_DIR_TEST`, setzt die Markierung `testversion`. Ohne Secrets nur ein
  Hinweis, kein Fehler.
- **`live.yml` „2 · Testversion freigeben (live)“:** nur von Hand, mit Versionsnummer;
  holt genau `testversion`, prüft die Nummer, lädt nach `FTP_DIR_LIVE`, setzt den
  Branch `live` und die Markierung `live-version`.
- **`daten-update.yml`:** jede Nacht für `main` (→ Test) **und** `live` (→ Live):
  Daten laden, bauen, speichern, hochladen. Daten gehen ohne Freigabe live,
  Programmänderungen nie.
- `docs/.htaccess`: HTTPS-Umleitung, `X-Robots-Tag: noindex` für `beta.`,
  frische Auslieferung von `index.html`, `sw.js`, `version.json`, Manifest.
- In der App: `VERSION`, `IST_TEST` (oranges Band „Testversion“, noindex),
  `IST_PLAY` über `/?quelle=play`.
- Cloudflare Worker: `beta.wien-live-daten.puhl.ch` als erlaubter Ursprung
  (Christoph fügt `live/worker.js` neu ein, Anleitung in `infos-app-betrieb.md`).

**Schritt 1b – Umzug Live (gemeinsam):**
1. Christoph startet einmal „2 · Testversion freigeben (live)“ → Live-Ordner gefüllt.
2. Im KAS die Subdomain `app.wien-live-daten.puhl.ch` vom CNAME (GitHub) auf den
   Ordner `/wien-live/` umstellen, SSL einschalten. Kurz kann HTTPS fehlen, bis das
   Zertifikat da ist (Vermutung: Minuten).
3. Prüfen: App, `/.well-known/assetlinks.json`, Live-Daten.
4. GitHub → Settings → Pages abschalten, `docs/CNAME` entfernt Claude.

## Schritt 2 – App fit für den Play Store

Erledigt: Manifest mit Icons (maskable), Service Worker, eigene Domain,
`/.well-known/assetlinks.json` (bisher nur Upload-Schlüssel), `datenschutz.html`,
`version.json`, Info-Seite mit Versionsgeschichte, Spendenlink in der Play-Version
ausgeblendet.

Offen:
- Erledigt in 1.3.2: `/?quelle=play`, `IST_PLAY`, Spendenlink in der Play-Version aus;
  `datenschutz.html` mit „Daten löschen“. Zahlungsrichtlinie vor Einreichung prüfen.
- Kein Login → kein Demo-Modus nötig.
- **App-Standard bei Wien live (Entscheidung 18.11.):** Zönose-Stil ist **nicht**
  geplant. Burger-Menü vermutlich nicht – außer ein Entwurf überzeugt: Kategorien
  (mit Farben) ins Burger-Menü, Unterkategorien als Auswahl direkt unter der Karte.
  Entwurf zuerst in der Testversion zeigen.

## Schritt 3 – Play Console (gemeinsam)

Stand 18.11.: in der Play Console ist noch nichts angelegt. Hochladen: **`wien-live-1.3.2.aab`** (Code 2).

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
4. **App-Paket:** `wien-live-1.3.2.aab` (Bubblewrap, signiert mit `upload-key.jks`).
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

- Entschieden 18.11.: Zielgruppe **ab 13**; Logo **mit KI erstellt** → in der Console
  „KI-generierte Inhalte“ angeben.
- Offen: Testergruppe anlegen (`wien-live-tester@googlegroups.com`)?
