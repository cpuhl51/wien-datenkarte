// Cloudflare Worker: reicht Echtzeitdaten der Wiener Linien an die Web-App weiter.
// Nötig, weil die Schnittstelle der Wiener Linien keine direkten Browser-Abfragen erlaubt (kein CORS).
//   /            → aktuelle Störungen (trafficInfoList), 60 Sekunden zwischengespeichert
//   /monitor?stopId=…&stopId=…  → Abfahrten an bis zu 20 Haltepunkten, 20 Sekunden zwischengespeichert
const BASE = "https://www.wienerlinien.at/ogd_realtime/";
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

    const url = new URL(request.url);
    let upstream = BASE + "trafficInfoList", ttl = 60;
    if (url.pathname === "/monitor") {
      // nur Zahlen als Haltepunkt-Nummern, höchstens 20, sortiert (gleiche Anfrage = gleicher Zwischenspeicher)
      const ids = [...new Set(url.searchParams.getAll("stopId").filter(s => /^\d{1,6}$/.test(s)))].sort().slice(0, 20);
      if (!ids.length) return new Response("stopId fehlt", { status: 400, headers: cors });
      upstream = BASE + "monitor?" + ids.map(i => "stopId=" + i).join("&");
      ttl = 20;
    }
    const res = await fetch(upstream, { cf: { cacheTtl: ttl, cacheEverything: true } });
    return new Response(res.body, {
      status: res.status,
      headers: { ...cors, "Content-Type": "application/json; charset=utf-8", "Cache-Control": `public, max-age=${ttl}` },
    });
  },
};
