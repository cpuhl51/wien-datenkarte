package ch.puhl.wienaktuell;

import android.content.Context;
import androidx.test.core.app.ApplicationProvider;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import java.io.File;
import java.nio.file.Files;

/** Zeichnet das Widget-Kartenbild für alle vier Modi (Testlauf mit echten Daten), Ausgabe nach build/widget-test. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 34, qualifiers = "xxhdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class WidgetRenderTest {
    /** Widget-Layout wie auf dem Startbildschirm (ca. 4×3 Felder) als Bild ausgeben. */
    static void layoutShot(Context c, int id, File out) throws Exception {
        android.widget.FrameLayout parent = new android.widget.FrameLayout(c);
        android.view.View v = android.view.LayoutInflater.from(c).inflate(R.layout.widget_wien, parent, false);
        ((android.widget.ImageView) v.findViewById(R.id.w_map)).setImageBitmap(android.graphics.BitmapFactory.decodeFile(new File(c.getCacheDir(), "widget_" + id + ".png").getAbsolutePath()));
        ((android.widget.TextView) v.findViewById(R.id.w_info)).setText(WienWidget.prefs(c).getString("info" + id, ""));
        ((android.widget.TextView) v.findViewById(R.id.w_time)).setText(WienWidget.prefs(c).getString("time" + id, ""));
        android.widget.TextView tab = v.findViewById(R.id.w_tab_next); tab.setBackgroundResource(R.drawable.widget_tab_on); tab.setTextColor(0xFFFFFFFF);
        float d = c.getResources().getDisplayMetrics().density;
        int w = (int) (340 * d), h = (int) (330 * d);
        v.measure(android.view.View.MeasureSpec.makeMeasureSpec(w, android.view.View.MeasureSpec.EXACTLY), android.view.View.MeasureSpec.makeMeasureSpec(h, android.view.View.MeasureSpec.EXACTLY));
        v.layout(0, 0, w, h);
        android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(w, h, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas cv = new android.graphics.Canvas(b); cv.drawColor(0xFF555555); v.draw(cv);
        try (java.io.FileOutputStream o = new java.io.FileOutputStream(new File(out, "layout.png"))) { b.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, o); }
    }

    @Test
    public void renderModes() throws Exception {
        Context c = ApplicationProvider.getApplicationContext();
        WienWidget.prefs(c).edit().putFloat("lat", 48.2312f).putFloat("lon", 16.4895f).putLong("locTime", System.currentTimeMillis()).apply();
        File out = new File("build/widget-test"); out.mkdirs();
        String[] modes = {"next", "taxi", "bike", "brunnen"};
        for (int i = 0; i < modes.length; i++) {
            int id = 100 + i;
            WienWidget.prefs(c).edit().putString("mode" + id, modes[i]).apply();
            WidgetData.render(c, id, true);
            Files.copy(new File(c.getCacheDir(), "widget_" + id + ".png").toPath(), new File(out, modes[i] + ".png").toPath(), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            if (i == 0) layoutShot(c, id, out);
            System.out.println("MODE " + modes[i] + ": " + WienWidget.prefs(c).getString("info" + id, "") + " | " + WienWidget.prefs(c).getString("time" + id, ""));
        }
    }
}
