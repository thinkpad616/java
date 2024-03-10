import static org.mockito.Mockito.*;
import static org.junit.Assert.*;
import org.junit.jupiter.api.Test;
import reactor.netty.http.client.HttpClient;
import java.time.Duration;
import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;

public class WebClientCreatorTest {

    @Test
    public void testCreateWebClient() {
        // Arrange
        ChassisWebClientBuilder mockBuilder = mock(ChassisWebClientBuilder.class);
        OAuthBuilder mockOAuthBuilder = mock(OAuthBuilder.class);
        WebClient expectedWebClient = mock(WebClient.class);
        HttpClient httpClient = HttpClient.create()
            .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 5000)
            .responseTimeout(Duration.ofMillis(5000))
            .doOnConnected(conn ->
                conn.addHandlerLast(new ReadTimeoutHandler(5000, TimeUnit.MILLISECONDS))
                    .addHandlerLast(new WriteTimeoutHandler(5000, TimeUnit.MILLISECONDS)));

        when(mockBuilder.getOAuthBuilder()).thenReturn(mockOAuthBuilder);
        when(mockBuilder.buildOAuthWebClient()).thenReturn(expectedWebClient);
        when(mockOAuthBuilder.clientConnector(any(ReactorClientHttpConnector.class))).thenReturn(mockOAuthBuilder);

        WebClientCreator creator = new WebClientCreator();

        // Act
        WebClient result = creator.createWebClient(mockBuilder);

        // Assert
        assertNotNull(result);
        assertEquals(expectedWebClient, result);
        verify(mockBuilder).getOAuthBuilder();
        verify(mockOAuthBuilder).clientConnector(any(ReactorClientHttpConnector.class));
        verify(mockBuilder).buildOAuthWebClient();
    }
}
