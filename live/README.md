# Live-Störungen einrichten (Cloudflare Worker, gratis)

1. Konto anlegen auf https://dash.cloudflare.com/sign-up (Free-Plan reicht).
2. Im Dashboard: **Workers & Pages → Create → Worker**, Name z. B. `wien-stoerungen`, **Deploy**.
3. **Edit code**, den Inhalt von `worker.js` hineinkopieren, **Deploy**.
4. Die Adresse des Workers (z. B. `https://wien-stoerungen.<name>.workers.dev`) in
   `web/template.html` bei `const LIVE_URL = "";` eintragen und speichern.

Danach holt die Web-App die Störungen jede Minute neu. Der Worker leitet nur diese eine
Adresse weiter und lässt nur Anfragen von app.wien-live-daten.puhl.ch und cpuhl51.github.io zu.
