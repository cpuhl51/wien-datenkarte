/*
 * Copyright 2020 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package ch.puhl.wienaktuell;

import android.Manifest;
import android.content.SharedPreferences;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;



public class LauncherActivity
        extends com.google.androidbrowserhelper.trusted.LauncherActivity {

    /* Beim ersten Start einmal nach dem Standort fragen (für „Nächstes Öffi“ und das Widget).
       Ohne diese Android-Freigabe liefert Chrome in der App keinen Standort. */
    private static final int REQ_STANDORT = 41;
    static final String PREFS = "wienlive", KEY_GEFRAGT = "standort_gefragt";
    private boolean mFrageStandort;

    private boolean standortErlaubt() {
        return checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    protected boolean shouldLaunchImmediately() {
        SharedPreferences sp = getSharedPreferences(PREFS, MODE_PRIVATE);
        mFrageStandort = Build.VERSION.SDK_INT >= Build.VERSION_CODES.M
                && !standortErlaubt() && !sp.getBoolean(KEY_GEFRAGT, false);
        return !mFrageStandort;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == REQ_STANDORT) launchTwa();
    }
    

    

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Setting an orientation crashes the app due to the transparent background on Android 8.0
        // Oreo and below. We only set the orientation on Oreo and above. This only affects the
        // splash screen and Chrome will still respect the orientation.
        // See https://github.com/GoogleChromeLabs/bubblewrap/issues/496 for details.
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.O) {
            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER_PORTRAIT);
        } else {
            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED);
        }
        if (mFrageStandort) {
            getSharedPreferences(PREFS, MODE_PRIVATE).edit().putBoolean(KEY_GEFRAGT, true).apply();
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION}, REQ_STANDORT);
        }
    }

    @Override
    protected Uri getLaunchingUrl() {
        // Get the original launch Url.
        Uri uri = super.getLaunchingUrl();
        /* Der Web-App mitteilen, ob Android den Standort erlaubt (für passende Hinweise) */
        try {
            if (uri != null && uri.getQueryParameter("standort") == null) {
                uri = uri.buildUpon().appendQueryParameter("standort",
                        (Build.VERSION.SDK_INT < Build.VERSION_CODES.M || standortErlaubt()) ? "1" : "0").build();
            }
        } catch (Exception ignored) { }

        

        return uri;
    }
}
