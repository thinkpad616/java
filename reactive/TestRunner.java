import com.intuit.karate.http.apache.ApacheHttpClient;
import org.apache.http.client.HttpClient;
import java.lang.reflect.Method;

public class TestRunner {
    @Test
    public void testKarateFeature() throws Exception {
        HttpClient httpClient = HttpClients.createDefault();
        ApacheHttpClient client = new ApacheHttpClient();

         Method featureMethod = ApacheHttpClient.class.getDeclaredMethod("feature", String.class);
        featureMethod.setAccessible(true);
        featureMethod.invoke(client, "classpath:your-feature-file.feature");
    }
}
