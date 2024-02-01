import com.intuit.karate.http.apache.ApacheHttpClient;
import org.junit.Test;

public class TestRunner {
    @Test
    public void testKarateFeature() {
        org.apache.http.client.HttpClient httpClient = org.apache.http.impl.client.HttpClients.createDefault(); // Create Apache client directly
        ApacheHttpClient client = new ApacheHttpClient();
        client.setHttpClient(httpClient);    // Set the Apache client
        client.run("classpath:your-feature-file.feature");
    }
}
