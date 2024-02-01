import com.intuit.karate.http.apache.ApacheHttpClient;
import org.apache.http.client.HttpClient;
import java.lang.reflect.Method;

public class TestRunner {
    @Test
    public void testKarateFeature() throws Exception {
        HttpClient httpClient = HttpClients.createDefault();
        ApacheHttpClient client = new ApacheHttpClient();

        // Use reflection to access the setHttpClient method
        Method setHttpClientMethod = ApacheHttpClient.class.getDeclaredMethod("setHttpClient", HttpClient.class);
        setHttpClientMethod.setAccessible(true);
        setHttpClientMethod.invoke(client, httpClient);

        client.run("classpath:your-feature-file.feature");
    }
}
