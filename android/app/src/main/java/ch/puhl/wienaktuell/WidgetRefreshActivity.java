package ch.puhl.wienaktuell;

import android.Manifest;
import android.app.Activity;
import android.appwidget.AppWidgetManager;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;

/**
 * Unsichtbare Aktivität hinter dem ↻-Knopf des Widgets: holt den Standort im Vordergrund
 * (nur die normale Standort-Erlaubnis, keine Hintergrund-Ortung), speichert ihn nur auf dem Gerät
 * und lässt das Widget neu zeichnen.
 */
public class WidgetRefreshActivity extends Activity {
    private int id;
    private boolean done = false;
    private final Handler h = new Handler(Looper.getMainLooper());
    private LocationManager lm;
    private LocationListener listener;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        id = getIntent().getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID);
        if (id == AppWidgetManager.INVALID_APPWIDGET_ID) { finish(); return; }
        WienWidget.setBusy(this, AppWidgetManager.getInstance(this), id);
        if (hasPerm()) locate();
        else if (Build.VERSION.SDK_INT >= 23) requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, 1);
        else locate();
    }

    private boolean hasPerm() {
        return Build.VERSION.SDK_INT < 23
                || checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    public void onRequestPermissionsResult(int rc, String[] perms, int[] res) {
        if (hasPerm()) locate();
        else {
            Toast.makeText(this, "Ohne Standort zeigt das Widget nur den zuletzt gewählten Ausschnitt.", Toast.LENGTH_LONG).show();
            finishWith(null);
        }
    }

    @SuppressWarnings({"MissingPermission", "deprecation"})
    private void locate() {
        lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        if (lm == null) { finishWith(null); return; }
        String prov = lm.isProviderEnabled(LocationManager.GPS_PROVIDER) ? LocationManager.GPS_PROVIDER
                : lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER) ? LocationManager.NETWORK_PROVIDER : null;
        if (prov == null) {
            Toast.makeText(this, "Standort ist am Gerät ausgeschaltet.", Toast.LENGTH_LONG).show();
            finishWith(best());
            return;
        }
        h.postDelayed(() -> finishWith(best()), 12000); // spätestens nach 12 s mit dem besten bekannten Standort
        if (Build.VERSION.SDK_INT >= 30) {
            lm.getCurrentLocation(prov, null, getMainExecutor(), this::finishWith);
        } else {
            listener = new LocationListener() {
                @Override public void onLocationChanged(Location l) { finishWith(l); }
                @Override public void onStatusChanged(String p, int s, Bundle e) { }
                @Override public void onProviderEnabled(String p) { }
                @Override public void onProviderDisabled(String p) { }
            };
            lm.requestSingleUpdate(prov, listener, Looper.getMainLooper());
        }
    }

    @SuppressWarnings("MissingPermission")
    private Location best() {
        if (lm == null || !hasPerm()) return null;
        Location best = null;
        for (String p : lm.getProviders(true)) {
            Location l = lm.getLastKnownLocation(p);
            if (l != null && (best == null || l.getTime() > best.getTime())) best = l;
        }
        return best;
    }

    private void finishWith(Location l) {
        if (done) return;
        done = true;
        h.removeCallbacksAndMessages(null);
        if (lm != null && listener != null) lm.removeUpdates(listener);
        if (l == null) l = best();
        if (l != null) {
            WienWidget.prefs(this).edit()
                    .putFloat("lat", (float) l.getLatitude()).putFloat("lon", (float) l.getLongitude())
                    .putLong("locTime", System.currentTimeMillis())
                    .putInt("px" + id, 0).putInt("py" + id, 0).apply();
        }
        WienWidget.background(this, id, true);
        finish();
        overridePendingTransition(0, 0);
    }
}
