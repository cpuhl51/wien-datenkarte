package ch.puhl.wienaktuell;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.widget.RemoteViews;

import java.io.File;

/**
 * Home-Screen-Widget „Wien live in der Nähe“: Kartenbild (Stadtplan der Stadt Wien) mit
 * nächstem Öffi, Taxistandplätzen, Leihrädern oder Trinkbrunnen.
 * Standort nur beim Tippen auf ↻ (WidgetRefreshActivity, im Vordergrund) – keine Hintergrund-Ortung.
 * Zoom und Verschieben über Knöpfe; das Kartenbild wird dann aus dem letzten Standort neu gezeichnet.
 */
public class WienWidget extends AppWidgetProvider {
    static final String A_MODE = "ch.puhl.wienaktuell.widget.MODE";
    static final String A_ZOOM = "ch.puhl.wienaktuell.widget.ZOOM";
    static final String A_PAN = "ch.puhl.wienaktuell.widget.PAN";
    static final String A_CENTER = "ch.puhl.wienaktuell.widget.CENTER";
    static final String A_REDRAW = "ch.puhl.wienaktuell.widget.REDRAW";
    static final String[] MODES = {"next", "taxi", "bike", "brunnen"};
    static final String APP = "https://app.wien-live-daten.puhl.ch/";

    static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences("wienwidget", Context.MODE_PRIVATE);
    }

    @Override
    public void onUpdate(Context c, AppWidgetManager m, int[] ids) {
        for (int id : ids) {
            show(c, m, id);
            background(c, id, true); // alle 30 Min: Daten am letzten Standort neu laden (ohne Ortung)
        }
    }

    @Override
    public void onDeleted(Context c, int[] ids) {
        SharedPreferences.Editor e = prefs(c).edit();
        for (int id : ids) {
            for (String k : new String[]{"mode", "z", "px", "py", "info", "time"}) e.remove(k + id);
            new File(c.getCacheDir(), "widget_" + id + ".png").delete();
        }
        e.apply();
    }

    @Override
    public void onReceive(Context c, Intent in) {
        super.onReceive(c, in);
        String a = in.getAction();
        int id = in.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID);
        if (a == null || id == AppWidgetManager.INVALID_APPWIDGET_ID) return;
        SharedPreferences p = prefs(c);
        SharedPreferences.Editor e = p.edit();
        boolean refetch = false;
        switch (a) {
            case A_MODE:
                e.putString("mode" + id, in.getStringExtra("mode"));
                e.putInt("px" + id, 0).putInt("py" + id, 0);
                refetch = true;
                break;
            case A_ZOOM:
                int z = Math.max(12, Math.min(18, p.getInt("z" + id, 16) + in.getIntExtra("d", 0)));
                int old = p.getInt("z" + id, 16);
                double f = Math.pow(2, z - old);
                e.putInt("z" + id, z);
                e.putInt("px" + id, (int) (p.getInt("px" + id, 0) * f));
                e.putInt("py" + id, (int) (p.getInt("py" + id, 0) * f));
                break;
            case A_PAN:
                e.putInt("px" + id, p.getInt("px" + id, 0) + in.getIntExtra("dx", 0));
                e.putInt("py" + id, p.getInt("py" + id, 0) + in.getIntExtra("dy", 0));
                break;
            case A_CENTER:
                e.putInt("px" + id, 0).putInt("py" + id, 0);
                break;
            case A_REDRAW:
                break;
            default:
                return;
        }
        e.apply();
        AppWidgetManager m = AppWidgetManager.getInstance(c);
        setBusy(c, m, id);
        background(c, id, refetch);
    }

    /** Daten laden (falls nötig) und Kartenbild zeichnen – im Hintergrund, mit goAsync-ähnlichem Thread. */
    static void background(Context c, int id, boolean refetch) {
        final Context app = c.getApplicationContext();
        new Thread(() -> {
            try {
                WidgetData.render(app, id, refetch);
            } catch (Throwable t) {
                prefs(app).edit().putString("info" + id, "Daten konnten gerade nicht geladen werden.").apply();
            }
            show(app, AppWidgetManager.getInstance(app), id);
        }).start();
    }

    static void setBusy(Context c, AppWidgetManager m, int id) {
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.widget_wien);
        v.setTextViewText(R.id.w_time, "Wird geladen …");
        m.partiallyUpdateAppWidget(id, v);
    }

    static PendingIntent bc(Context c, int id, String action, int req, Intent extra) {
        Intent i = extra != null ? extra : new Intent();
        i.setAction(action);
        i.setComponent(new ComponentName(c, WienWidget.class));
        i.putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, id);
        i.setData(Uri.parse("wienwidget://" + id + "/" + action + "/" + req));
        return PendingIntent.getBroadcast(c, id * 100 + req, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    static String mode(Context c, int id) {
        return prefs(c).getString("mode" + id, "next");
    }

    static String layerUrl(String mode) {
        switch (mode) {
            case "taxi": return APP + "#ebene=taxi";
            case "bike": return APP + "#ebene=bike";
            case "brunnen": return APP + "#ebene=infra:brunnen";
            default: return APP + "#ebene=next";
        }
    }

    static void show(Context c, AppWidgetManager m, int id) {
        SharedPreferences p = prefs(c);
        String mode = mode(c, id);
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.widget_wien);
        int[] tabs = {R.id.w_tab_next, R.id.w_tab_taxi, R.id.w_tab_bike, R.id.w_tab_brunnen};
        for (int i = 0; i < MODES.length; i++) {
            boolean on = MODES[i].equals(mode);
            v.setInt(tabs[i], "setBackgroundResource", on ? R.drawable.widget_tab_on : R.drawable.widget_tab);
            v.setTextColor(tabs[i], on ? 0xFFFFFFFF : 0xFF1B1F1E);
            Intent x = new Intent();
            x.putExtra("mode", MODES[i]);
            v.setOnClickPendingIntent(tabs[i], bc(c, id, A_MODE, 1 + i, x));
        }
        File img = new File(c.getCacheDir(), "widget_" + id + ".png");
        if (img.exists()) {
            Bitmap b = BitmapFactory.decodeFile(img.getAbsolutePath());
            if (b != null) v.setImageViewBitmap(R.id.w_map, b);
        }
        v.setTextViewText(R.id.w_info, p.getString("info" + id, "Tippe ↻, um deinen Standort zu holen."));
        v.setTextViewText(R.id.w_time, p.getString("time" + id, ""));

        int step = 120;
        Intent zi = new Intent(); zi.putExtra("d", 1);
        Intent zo = new Intent(); zo.putExtra("d", -1);
        v.setOnClickPendingIntent(R.id.w_zin, bc(c, id, A_ZOOM, 10, zi));
        v.setOnClickPendingIntent(R.id.w_zout, bc(c, id, A_ZOOM, 11, zo));
        int[][] pans = {{0, -step}, {0, step}, {-step, 0}, {step, 0}};
        int[] pid = {R.id.w_up, R.id.w_down, R.id.w_left, R.id.w_right};
        for (int i = 0; i < 4; i++) {
            Intent x = new Intent(); x.putExtra("dx", pans[i][0]); x.putExtra("dy", pans[i][1]);
            v.setOnClickPendingIntent(pid[i], bc(c, id, A_PAN, 20 + i, x));
        }
        v.setOnClickPendingIntent(R.id.w_center, bc(c, id, A_CENTER, 30, null));

        Intent r = new Intent(c, WidgetRefreshActivity.class);
        r.putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, id);
        r.setData(Uri.parse("wienwidget://" + id + "/refresh"));
        r.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_NO_ANIMATION);
        v.setOnClickPendingIntent(R.id.w_refresh, PendingIntent.getActivity(c, id * 100 + 40, r, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE));

        Intent open = new Intent(Intent.ACTION_VIEW, Uri.parse(layerUrl(mode)), c, LauncherActivity.class);
        open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        PendingIntent po = PendingIntent.getActivity(c, id * 100 + 41, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        v.setOnClickPendingIntent(R.id.w_map, po);
        v.setOnClickPendingIntent(R.id.w_info, po);
        m.updateAppWidget(id, v);
    }

    static void redrawAll(Context c) {
        AppWidgetManager m = AppWidgetManager.getInstance(c);
        for (int id : m.getAppWidgetIds(new ComponentName(c, WienWidget.class))) background(c, id, true);
    }
}
