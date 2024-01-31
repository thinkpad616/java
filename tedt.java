import com.intuit.karate.apache.HttpClientFactory;
import org.apache.http.HttpResponse;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;

// Additional imports if needed for event parsing or data manipulation

function listenForEventsAndPostSDP() {
  HttpClient client = HttpClientFactory.create();
  HttpGet getRequest = new HttpGet("http://your-sse-api-url");
  getRequest.setHeader("Authorization", "Bearer <your_auth_token>");
  getRequest.setHeader("Accept", "text/event-stream");

  try (HttpResponse response = client.execute(getRequest)) {
    try (BufferedReader reader = new BufferedReader(new InputStreamReader(response.getEntity().getContent()))) {
      String event;
      while ((event = reader.readLine()) != null) {
        // Parse event data (adjust based on your SSE format)
        Map<String, Object> eventData = karate.parse(event);

        try {
          // Additional data for POST request
          Map<String, Object> dataToBePosted = ...; // Replace with your data
          sendPostSDPRequest(eventData, dataToBePosted);
        } catch (Exception e) {
          log.error("Error sending POST request:", e);
        }
      }
    }
  } catch (Exception e) {
    log.error("Error reading SSE stream:", e);
  }
}

function sendPostSDPRequest(data, additionalData) {
  HttpClient client = HttpClientFactory.create();
  HttpPost postRequest = new HttpPost("http://your-sdp-api-url");
  postRequest.setHeader("Content-Type", "application/json");
  // Set other necessary headers

  try {
    StringEntity entity = new StringEntity(karate.json(karate.merge(data, additionalData)));
    postRequest.setEntity(entity);
    client.execute(postRequest);
  } catch (Exception e) {
    log.error("Error sending POST request:", e);
  }
}
