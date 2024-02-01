import org.apache.http.conn.ssl.SSLConnectionSocketFactory;
import org.apache.http.conn.ssl.TrustStrategy;
import org.apache.http.ssl.SSLContextBuilder;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;

// ... other imports

// TrustStrategy that accepts all certificates (not recommended in production)
TrustStrategy acceptingTrustStrategy = (X509Certificate[] chain, String authType) -> true;

// Create SSLContext with the all-trusting TrustStrategy
SSLContext sslContext = SSLContextBuilder
        .create()
        .loadTrustMaterial(null, acceptingTrustStrategy)
        .build();

// Create SSLConnectionSocketFactory with the SSLContext
SSLConnectionSocketFactory csf = new SSLConnectionSocketFactory(sslContext);

// Create WebClient with the connector using the SSLConnectionSocketFactory
WebClient webClient = WebClient.builder()
        .clientConnector(new ReactorClientHttpConnector(HttpClient.create().secure(csf)))
        .build();
