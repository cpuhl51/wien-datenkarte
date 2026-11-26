package ch.puhl.wienaktuell;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;

/**
 * Wird aus der Web-App über den Knopf „Standort erlauben“ geöffnet
 * (Link intent://standort#Intent;scheme=wienlive;package=ch.puhl.wienaktuell;end).
 * Fragt nach dem Standort; hat man früher „Nicht zulassen“ gewählt und Android fragt
 * nicht mehr, öffnet sie die App-Einstellungen. Danach geht es zurück in die App.
 */
public class StandortActivity extends Activity {
    private static final int REQ = 42;

    private boolean erlaubt() {
        return checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M || erlaubt()) { finish(); return; }
        boolean gefragt = getSharedPreferences(LauncherActivity.PREFS, MODE_PRIVATE)
                .getBoolean(LauncherActivity.KEY_GEFRAGT, false);
        if (gefragt && !shouldShowRequestPermissionRationale(Manifest.permission.ACCESS_FINE_LOCATION)
                && !shouldShowRequestPermissionRationale(Manifest.permission.ACCESS_COARSE_LOCATION)) {
            /* Android fragt nicht mehr nach – direkt in die App-Einstellungen */
            oeffneEinstellungen();
            return;
        }
        getSharedPreferences(LauncherActivity.PREFS, MODE_PRIVATE).edit()
                .putBoolean(LauncherActivity.KEY_GEFRAGT, true).apply();
        requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_COARSE_LOCATION}, REQ);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (!erlaubt() && !shouldShowRequestPermissionRationale(Manifest.permission.ACCESS_FINE_LOCATION)
                && !shouldShowRequestPermissionRationale(Manifest.permission.ACCESS_COARSE_LOCATION)) {
            oeffneEinstellungen();
            return;
        }
        finish();
    }

    private void oeffneEinstellungen() {
        try {
            startActivity(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                    Uri.fromParts("package", getPackageName(), null)));
        } catch (Exception ignored) { }
        finish();
    }
}
