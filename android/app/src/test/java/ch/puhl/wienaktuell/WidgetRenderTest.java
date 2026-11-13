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
@Config(sdk = 34)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class WidgetRenderTest {
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
            System.out.println("MODE " + modes[i] + ": " + WienWidget.prefs(c).getString("info" + id, "") + " | " + WienWidget.prefs(c).getString("time" + id, ""));
        }
    }
}
