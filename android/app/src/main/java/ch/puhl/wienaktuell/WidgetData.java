package ch.puhl.wienaktuell;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Typeface;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** Lädt die Daten für das Widget und zeichnet den Kartenausschnitt. Alles bleibt auf dem Gerät. */
final class WidgetData {
    private WidgetData() { }

    static final int W = 720, H = 480;          // Bildgröße des Kartenausschnitts
    static final double SCALE = 1.6;            // Kacheln vergrößert, damit Schrift am Handy lesbar ist
    static final String TILE = "https://mapsneu.wien.gv.at/basemap/bmapgrau/normal/google3857/%d/%d/%d.png";
    static final String WL = "https://www.wienerlinien.at/ogd_realtime/monitor?";
    static final String GBFS = "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_wr/de/";
    static final int[] STOP_COL = {0xFF1098AD, 0xFF2F9E44, 0xFF9C36B5, 0xFFE8590C, 0xFF1C7ED6, 0xFFC2255C, 0xFF5C940D};

    static class Pt {
        double lon, lat, d; String name, text; int col = 0xFF1C7ED6; String label;
        Pt(double lon, double lat, String name) { this.lon = lon; this.lat = lat; this.name = name; }
    }

    // ---------- Netz und Zwischenspeicher ----------
    static byte[] get(String u, int timeout) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(u).openConnection();
        c.setConnectTimeout(timeout); c.setReadTimeout(timeout);
        c.setRequestProperty("User-Agent", "WienLive-Widget/1.3 (Android)");
        try (InputStream in = c.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            if (c.getResponseCode() != 200) throw new Exception("HTTP " + c.getResponseCode());
            byte[] buf = new byte[16384]; int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            return out.toByteArray();
        } finally { c.disconnect(); }
    }

    static String cached(Context ctx, String url, String name, long maxAgeMs) throws Exception {
        File f = new File(ctx.getCacheDir(), name);
        if (f.exists() && System.currentTimeMillis() - f.lastModified() < maxAgeMs) return read(f);
        try {
            byte[] b = get(url, 15000);
            try (FileOutputStream o = new FileOutputStream(f)) { o.write(b); }
            return new String(b, StandardCharsets.UTF_8);
        } catch (Exception e) {
            if (f.exists()) return read(f); // offline: alte Daten
            throw e;
        }
    }

    static String read(File f) throws Exception {
        byte[] b = new byte[(int) f.length()];
        try (InputStream in = new java.io.FileInputStream(f)) { int o = 0, n; while (o < b.length && (n = in.read(b, o, b.length - o)) > 0) o += n; }
        return new String(b, StandardCharsets.UTF_8);
    }

    // ---------- Geometrie ----------
    static double wx(double lon, int z) { return (lon + 180) / 360 * 256 * Math.pow(2, z); }
    static double wy(double lat, int z) {
        double s = Math.sin(Math.toRadians(lat));
        return (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * 256 * Math.pow(2, z);
    }
    static double dist(double lon1, double lat1, double lon2, double lat2) {
        double x = Math.toRadians(lon2 - lon1) * Math.cos(Math.toRadians((lat1 + lat2) / 2)), y = Math.toRadians(lat2 - lat1);
        return Math.sqrt(x * x + y * y) * 6371000;
    }
    static String fmt(double m) { return m < 1000 ? Math.round(m / 10) * 10 + " m" : String.format(Locale.GERMAN, "%.1f km", m / 1000); }

    // ---------- Hauptablauf ----------
    static void render(Context ctx, int id, boolean refetch) throws Exception {
        SharedPreferences p = WienWidget.prefs(ctx);
        String mode = WienWidget.mode(ctx, id);
        boolean hasLoc = p.contains("lat");
        double lat = p.getFloat("lat", 48.2085f), lon = p.getFloat("lon", 16.3731f);
        int z = hasLoc ? p.getInt("z" + id, 16) : Math.min(p.getInt("z" + id, 13), 13);
        if (hasLoc && !p.getBoolean("zman" + id, false)) {
            // Ausschnitt automatisch so wählen, dass die nächsten Treffer zu sehen sind
            double d = nearestDist(ctx, mode, lon, lat);
            double mpp = 156543.03 * Math.cos(Math.toRadians(lat)); // Meter je Pixel bei Zoom 0
            double half = (H / 2.0 / SCALE) * 0.8;
            z = d <= 0 ? 16 : (int) Math.floor(Math.log(mpp * half / d) / Math.log(2));
            z = Math.max(13, Math.min(17, z));
            p.edit().putInt("z" + id, z).apply();
        }
        double cx = wx(lon, z) + p.getInt("px" + id, 0) / SCALE, cy = wy(lat, z) + p.getInt("py" + id, 0) / SCALE;

        List<Pt> pts = new ArrayList<>();
        String info;
        if (!hasLoc) {
            info = "Tippe ↻, um deinen Standort zu holen. Tippe auf die Karte, um die App zu öffnen.";
        } else {
            switch (mode) {
                case "taxi": info = points(ctx, "taxi", lon, lat, z, cx, cy, pts, 0xFFE0A800, "Taxistandplatz"); break;
                case "brunnen": info = points(ctx, "brunnen", lon, lat, z, cx, cy, pts, 0xFF1C7ED6, "Trinkbrunnen"); break;
                case "bike": info = bikes(ctx, lon, lat, z, cx, cy, pts); break;
                default: info = departures(ctx, lon, lat, pts); break;
            }
        }

        Bitmap bmp = Bitmap.createBitmap(W, H, Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(bmp);
        cv.drawColor(0xFFEDEFEE);
        drawTiles(ctx, cv, z, cx, cy);
        double ox = cx - W / 2.0 / SCALE, oy = cy - H / 2.0 / SCALE;
        Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG), stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
        stroke.setStyle(Paint.Style.STROKE); stroke.setColor(Color.WHITE); stroke.setStrokeWidth(4);
        List<RectF> used = new ArrayList<>();
        float ux = (float) ((wx(lon, z) - ox) * SCALE), uy = (float) ((wy(lat, z) - oy) * SCALE);
        if (hasLoc) used.add(new RectF(ux - 16, uy - 16, ux + 16, uy + 16));
        for (Pt t : pts) { // erst alle Punkte …
            float x = (float) ((wx(t.lon, z) - ox) * SCALE), y = (float) ((wy(t.lat, z) - oy) * SCALE);
            if (x < -20 || y < -20 || x > W + 20 || y > H + 20) continue;
            fill.setColor(t.col);
            cv.drawCircle(x, y, 13, fill); cv.drawCircle(x, y, 13, stroke);
            used.add(new RectF(x - 14, y - 14, x + 14, y + 14));
        }
        for (Pt t : pts) { // … dann die Beschriftungen, ohne Punkte zu verdecken
            if (t.label == null) continue;
            float x = (float) ((wx(t.lon, z) - ox) * SCALE), y = (float) ((wy(t.lat, z) - oy) * SCALE);
            if (x < 0 || y < 0 || x > W || y > H) continue;
            label(cv, t.label, t.name, x, y, t.col, used);
        }
        if (hasLoc) {
            float x = ux, y = uy;
            fill.setColor(0x331C7ED6); cv.drawCircle(x, y, 30, fill);
            fill.setColor(0xFF1C7ED6); cv.drawCircle(x, y, 13, fill);
            stroke.setStrokeWidth(5); cv.drawCircle(x, y, 13, stroke);
        }
        Paint attr = new Paint(Paint.ANTI_ALIAS_FLAG); attr.setTextSize(17); attr.setColor(0xCC333333);
        cv.drawText("basemap.at", W - attr.measureText("basemap.at") - 8, H - 8, attr);

        try (FileOutputStream o = new FileOutputStream(new File(ctx.getCacheDir(), "widget_" + id + ".png"))) {
            bmp.compress(Bitmap.CompressFormat.PNG, 100, o);
        }
        String hm = new SimpleDateFormat("HH:mm", Locale.GERMAN).format(new Date());
        String loc = hasLoc ? " · Standort von " + new SimpleDateFormat("HH:mm", Locale.GERMAN).format(new Date(p.getLong("locTime", 0))) : "";
        p.edit().putString("info" + id, info).putString("time" + id, "Stand " + hm + loc + " · ↻ = neu orten").apply();
    }

    /** Entfernung, die der Ausschnitt mindestens zeigen soll (3. nächster Treffer bzw. 3. nächste Haltestelle). */
    static double nearestDist(Context ctx, String mode, double lon, double lat) {
        try {
            List<Double> ds = new ArrayList<>();
            if (mode.equals("taxi") || mode.equals("brunnen")) {
                JSONArray a = new JSONObject(cached(ctx, WienWidget.APP + "widget-punkte.json", "widget-punkte.json", 7L * 86400000)).getJSONArray(mode);
                for (int i = 0; i < a.length(); i++) { JSONArray r = a.getJSONArray(i); ds.add(dist(lon, lat, r.getDouble(0), r.getDouble(1))); }
            } else if (mode.equals("bike")) {
                JSONArray a = new JSONObject(cached(ctx, GBFS + "station_information.json", "gbfs_info.json", 86400000L)).getJSONObject("data").getJSONArray("stations");
                for (int i = 0; i < a.length(); i++) { JSONObject s = a.getJSONObject(i); ds.add(dist(lon, lat, s.getDouble("lon"), s.getDouble("lat"))); }
            } else {
                JSONObject hs = new JSONObject(cached(ctx, WienWidget.APP + "haltestellen.json", "haltestellen.json", 7L * 86400000));
                Map<String, Double> byName = new LinkedHashMap<>();
                Iterator<String> it = hs.keys();
                while (it.hasNext()) { JSONArray r = hs.getJSONArray(it.next()); double d = dist(lon, lat, r.getDouble(0), r.getDouble(1));
                    Double o = byName.get(r.getString(2)); if (o == null || d < o) byName.put(r.getString(2), d); }
                ds.addAll(byName.values());
            }
            Collections.sort(ds);
            return ds.isEmpty() ? 0 : ds.get(Math.min(2, ds.size() - 1));
        } catch (Exception e) { return 0; }
    }

    static void drawTiles(Context ctx, Canvas cv, int z, double cx, double cy) {
        double ox = cx - W / 2.0 / SCALE, oy = cy - H / 2.0 / SCALE;
        int tx0 = (int) Math.floor(ox / 256), ty0 = (int) Math.floor(oy / 256);
        int tx1 = (int) Math.floor((ox + W / SCALE) / 256), ty1 = (int) Math.floor((oy + H / SCALE) / 256);
        File dir = new File(ctx.getCacheDir(), "tiles"); dir.mkdirs();
        Paint pp = new Paint(Paint.FILTER_BITMAP_FLAG);
        for (int tx = tx0; tx <= tx1; tx++) for (int ty = ty0; ty <= ty1; ty++) {
            File f = new File(dir, z + "_" + tx + "_" + ty + ".png");
            try {
                if (!f.exists() || System.currentTimeMillis() - f.lastModified() > 30L * 86400000) {
                    byte[] b = get(String.format(Locale.ROOT, TILE, z, ty, tx), 10000);
                    try (FileOutputStream o = new FileOutputStream(f)) { o.write(b); }
                }
                Bitmap t = BitmapFactory.decodeFile(f.getAbsolutePath());
                if (t == null) continue;
                float x = (float) ((tx * 256 - ox) * SCALE), y = (float) ((ty * 256 - oy) * SCALE);
                cv.drawBitmap(t, new Rect(0, 0, t.getWidth(), t.getHeight()), new RectF(x, y, x + (float) (256 * SCALE), y + (float) (256 * SCALE)), pp);
            } catch (Exception ignored) { }
        }
        trimTiles(dir);
    }

    static void trimTiles(File dir) {
        File[] fs = dir.listFiles();
        if (fs == null || fs.length < 400) return;
        java.util.Arrays.sort(fs, (a, b) -> Long.compare(a.lastModified(), b.lastModified()));
        for (int i = 0; i < fs.length - 300; i++) fs[i].delete();
    }

    static void label(Canvas cv, String line2, String line1, float x, float y, int col, List<RectF> used) {
        Paint a = new Paint(Paint.ANTI_ALIAS_FLAG), b = new Paint(Paint.ANTI_ALIAS_FLAG);
        a.setTextSize(25); a.setTypeface(Typeface.DEFAULT_BOLD); a.setColor(col);
        b.setTextSize(22); b.setTypeface(Typeface.DEFAULT_BOLD); b.setColor(0xFF1B1F1E);
        float w = Math.max(line1 == null ? 0 : a.measureText(line1), b.measureText(line2)) + 8, h = line1 == null ? 28 : 54;
        float[][] opts = {{x + 18, y - 20}, {x - w - 18, y - 20}, {x - w / 2, y + 18}, {x - w / 2, y - h - 18}};
        RectF r = null;
        for (float[] o : opts) {
            RectF c = new RectF(o[0], o[1], o[0] + w, o[1] + h);
            if (c.left < 2 || c.right > W - 2 || c.top < 2 || c.bottom > H - 2) continue;
            boolean hit = false;
            for (RectF u : used) { if (u.contains(x, y)) continue; if (RectF.intersects(u, c)) { hit = true; break; } }
            if (!hit) { r = c; break; }
        }
        if (r == null) return;
        used.add(r);
        Paint halo = new Paint(Paint.ANTI_ALIAS_FLAG); halo.setColor(0xD9FFFFFF);
        cv.drawRoundRect(r, 8, 8, halo);
        float ty = r.top + 23;
        if (line1 != null) { cv.drawText(line1, r.left + 4, ty, a); ty += 26; }
        cv.drawText(line2, r.left + 4, ty, b);
    }

    // ---------- Taxi und Trinkbrunnen ----------
    static String points(Context ctx, String key, double lon, double lat, int z, double cx, double cy, List<Pt> out, int col, String what) throws Exception {
        JSONArray a = new JSONObject(cached(ctx, WienWidget.APP + "widget-punkte.json", "widget-punkte.json", 7L * 86400000)).getJSONArray(key);
        List<Pt> all = new ArrayList<>();
        double ox = cx - W / 2.0 / SCALE, oy = cy - H / 2.0 / SCALE;
        for (int i = 0; i < a.length(); i++) {
            JSONArray r = a.getJSONArray(i);
            Pt t = new Pt(r.getDouble(0), r.getDouble(1), null);
            t.text = r.optString(2, ""); t.col = col; t.d = dist(lon, lat, t.lon, t.lat);
            double x = (wx(t.lon, z) - ox) * SCALE, y = (wy(t.lat, z) - oy) * SCALE;
            if (x > -20 && y > -20 && x < W + 20 && y < H + 20) out.add(t);
            all.add(t);
        }
        Collections.sort(all, (p, q) -> Double.compare(p.d, q.d));
        for (int i = 0; i < Math.min(2, all.size()); i++) all.get(i).label = fmt(all.get(i).d);
        StringBuilder s = new StringBuilder();
        for (int i = 0; i < Math.min(2, all.size()); i++) {
            Pt t = all.get(i);
            if (s.length() > 0) s.append('\n');
            s.append(fmt(t.d)).append(" · ").append(t.text.isEmpty() ? what : t.text);
        }
        if (s.length() == 0) s.append("Kein ").append(what).append(" gefunden.");
        return s.toString();
    }

    // ---------- Leihräder (WienMobil Rad, nextbike GBFS) ----------
    static String bikes(Context ctx, double lon, double lat, int z, double cx, double cy, List<Pt> out) throws Exception {
        JSONArray info = new JSONObject(cached(ctx, GBFS + "station_information.json", "gbfs_info.json", 86400000L)).getJSONObject("data").getJSONArray("stations");
        JSONArray stat = new JSONObject(new String(get(GBFS + "station_status.json", 15000), StandardCharsets.UTF_8)).getJSONObject("data").getJSONArray("stations");
        Map<String, JSONObject> st = new LinkedHashMap<>();
        for (int i = 0; i < stat.length(); i++) st.put(stat.getJSONObject(i).getString("station_id"), stat.getJSONObject(i));
        List<Pt> all = new ArrayList<>();
        double ox = cx - W / 2.0 / SCALE, oy = cy - H / 2.0 / SCALE;
        for (int i = 0; i < info.length(); i++) {
            JSONObject s = info.getJSONObject(i), x = st.get(s.getString("station_id"));
            if (x == null || !x.optBoolean("is_installed", true)) continue;
            Pt t = new Pt(s.getDouble("lon"), s.getDouble("lat"), s.optString("name"));
            int nb = x.optBoolean("is_renting", true) ? x.optInt("num_bikes_available", 0) : 0;
            boolean hasDocks = !s.isNull("capacity") && x.optBoolean("is_returning", true);
            int nd = x.optInt("num_docks_available", 0);
            t.col = nb <= 0 ? 0xFF9AA3A1 : nb <= 2 ? 0xFF1E7A34 : 0xFF5BD16F;
            t.text = t.name + " · " + nb + (nb == 1 ? " Rad" : " Räder") + (hasDocks ? " · " + nd + (nd == 1 ? " Platz" : " Plätze") : " · Rückgabe auf Fläche");
            t.d = dist(lon, lat, t.lon, t.lat);
            double px = (wx(t.lon, z) - ox) * SCALE, py = (wy(t.lat, z) - oy) * SCALE;
            t.label = String.valueOf(nb); t.name = null;
            if (px > -20 && py > -20 && px < W + 20 && py < H + 20) out.add(t);
            all.add(t);
        }
        Collections.sort(all, (p, q) -> Double.compare(p.d, q.d));
        for (int i = 8; i < all.size(); i++) all.get(i).label = null;
        StringBuilder s = new StringBuilder();
        for (int i = 0; i < Math.min(2, all.size()); i++) { if (s.length() > 0) s.append('\n'); s.append(fmt(all.get(i).d)).append(" · ").append(all.get(i).text); }
        return s.length() > 0 ? s.toString() : "Keine Station gefunden.";
    }

    // ---------- Nächstes Öffi (Wiener Linien Echtzeit) ----------
    static String departures(Context ctx, double lon, double lat, List<Pt> out) throws Exception {
        JSONObject hs = new JSONObject(cached(ctx, WienWidget.APP + "haltestellen.json", "haltestellen.json", 7L * 86400000));
        List<Pt> all = new ArrayList<>();
        Iterator<String> it = hs.keys();
        while (it.hasNext()) {
            String k = it.next(); JSONArray r = hs.getJSONArray(k);
            Pt t = new Pt(r.getDouble(0), r.getDouble(1), r.getString(2)); t.text = k; t.d = dist(lon, lat, t.lon, t.lat);
            if (t.d <= 1500) all.add(t);
        }
        Collections.sort(all, (p, q) -> Double.compare(p.d, q.d));
        List<String> names = new ArrayList<>();
        for (Pt t : all) if (!names.contains(t.name) && names.size() < 3) names.add(t.name);
        List<Pt> st = new ArrayList<>();
        for (Pt t : all) if (names.contains(t.name) && st.size() < 20) st.add(t);
        if (st.isEmpty()) return "Keine Haltestelle im Umkreis von 1,5 km.";
        StringBuilder q = new StringBuilder(WL);
        for (Pt t : st) q.append("stopId=").append(t.text).append('&');
        JSONArray mons = new JSONObject(new String(get(q.toString(), 15000), StandardCharsets.UTF_8)).getJSONObject("data").optJSONArray("monitors");
        // je Haltestelle: Linie → nächste Abfahrten (Minuten)
        Map<String, Map<String, List<Integer>>> dep = new LinkedHashMap<>();
        java.util.Set<String> active = new java.util.HashSet<>();
        if (mons != null) for (int i = 0; i < mons.length(); i++) {
            JSONObject m = mons.getJSONObject(i);
            JSONObject ls = m.getJSONObject("locationStop").getJSONObject("properties");
            String title = ls.optString("title");
            JSONObject attr = ls.optJSONObject("attributes");
            if (attr != null) active.add(String.valueOf(attr.optInt("rbl")));
            JSONArray lines = m.optJSONArray("lines");
            if (lines == null) continue;
            for (int j = 0; j < lines.length(); j++) {
                JSONObject l = lines.getJSONObject(j);
                JSONArray ds = l.optJSONObject("departures") != null ? l.getJSONObject("departures").optJSONArray("departure") : null;
                if (ds == null) continue;
                for (int k = 0; k < Math.min(2, ds.length()); k++) {
                    JSONObject t = ds.getJSONObject(k).optJSONObject("departureTime");
                    if (t == null || !t.has("countdown")) continue;
                    dep.computeIfAbsent(title, x -> new LinkedHashMap<>()).computeIfAbsent(l.optString("name"), x -> new ArrayList<>()).add(t.getInt("countdown"));
                }
            }
        }
        StringBuilder s = new StringBuilder();
        int ci = 0;
        for (String n : names) {
            int col = STOP_COL[ci++ % STOP_COL.length];
            Map<String, List<Integer>> lm = dep.get(n);
            List<String> parts = new ArrayList<>();
            List<String> shortParts = new ArrayList<>();
            if (lm != null) for (Map.Entry<String, List<Integer>> e : lm.entrySet()) {
                List<Integer> v = e.getValue(); Collections.sort(v);
                StringBuilder ms = new StringBuilder();
                for (int k = 0; k < Math.min(2, v.size()); k++) { if (k > 0) ms.append(", "); ms.append(v.get(k) <= 0 ? "jetzt" : v.get(k) + "′"); }
                parts.add(e.getKey() + " " + ms);
                shortParts.add(e.getKey() + " " + (v.get(0) <= 0 ? "jetzt" : v.get(0) + "′"));
            }
            double dmin = 1e9; boolean first = true;
            for (Pt t : st) if (n.equals(t.name)) {
                dmin = Math.min(dmin, t.d);
                if (!active.isEmpty() && !active.contains(t.text)) continue; // nur Haltepunkte mit Abfahrten
                t.col = col;
                if (first) { t.label = shortParts.isEmpty() ? "keine Abfahrt" : android.text.TextUtils.join(" · ", shortParts.subList(0, Math.min(3, shortParts.size()))); first = false; }
                else { t.name = null; }
                out.add(t);
            }
            if (s.length() > 0) s.append('\n');
            s.append(n).append(" (").append(fmt(dmin)).append("): ").append(parts.isEmpty() ? "keine Abfahrt gemeldet" : android.text.TextUtils.join(" · ", parts));
        }
        return s.toString();
    }
}
