// Cloudflare Worker: reicht die Störungsmeldungen der Wiener Linien an die Web-App weiter.
// Nötig, weil die Schnittstelle der Wiener Linien keine direkten Browser-Abfragen erlaubt (kein CORS).
// Nur diese eine Adresse wird weitergereicht, Antworten werden 60 Sekunden zwischengespeichert.
const UPSTREAM = "https://www.wienerlinien.at/ogd_realtime/trafficInfoList";
const ALLOWED_ORIGINS = ["https://app.wien-live-daten.puhl.ch", "https://cpuhl51.github.io"];

export default {
  async fetch(request) {
    const origin = request.headers.get("Origin") || "";
    const cors = {
      "Access-Control-Allow-Origin": ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Vary": "Origin",
    };
    if (request.method === "OPTIONS") return new Response(null, { headers: cors });
    if (request.method !== "GET") return new Response("Nur GET", { status: 405, headers: cors });

    const res = await fetch(UPSTREAM, { cf: { cacheTtl: 60, cacheEverything: true } });
    return new Response(res.body, {
      status: res.status,
      headers: { ...cors, "Content-Type": "application/json; charset=utf-8", "Cache-Control": "public, max-age=60" },
    });
  },
};
