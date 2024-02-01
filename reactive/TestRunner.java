import com.intuit.karate.http.apache.ApacheHttpClient;
import org.apache.http.client.HttpClient;
import org.apache.http.impl.client.HttpClients;
import org.junit.Test;
import java.lang.reflect.Method;

public class ApacheHttpClientTest {
    @Test
    public void testKarateFeature() throws Exception {
        HttpClient httpClient = HttpClients.createDefault();
        ApacheHttpClient client = new ApacheHttpClient();

        // Use reflection to access and invoke the setHttpClient method (if available)
        Method setHttpClientMethod = ApacheHttpClient.class.getDeclaredMethod("setHttpClient", Object.class);  // Use Object as argument
        if (setHttpClientMethod != null) {  // Check if method exists
            setHttpClientMethod.setAccessible(true);
            setHttpClientMethod.invoke(client, httpClient);
        } else {
            // Handle cases where setHttpClient method is not available
        }

        // Proceed with executeScript as before
        Method executeScriptMethod = ApacheHttpClient.class.getDeclaredMethod("executeScript", String.class);
        executeScriptMethod.setAccessible(true);
        executeScriptMethod.invoke(client, "classpath:your-feature-file.feature");
    }
}
