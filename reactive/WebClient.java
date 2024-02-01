import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;

public class EventHandler {

    private final WebClient webClient;

    public EventHandler(WebClient webClient) {
        this.webClient = webClient;
    }

    public void handleEvents() {
        Flux<String> events = webClient.get().uri("sse-api-url")
                                        .retrieve()
                                        .bodyToFlux(String.class);

        events
            .filter(event -> event.contains("ping"))  // Adapt based on actual event structure
            .buffer(3)
            .flatMap(this::sendPostRequest)
            .subscribe();
    }

    private Mono<Void> sendPostRequest(List<String> events) {
        // Construct POST request body using events (if needed)
        return webClient.post().uri("post-api-url")
                         .bodyValue(events)  // Adjust body content as needed
                         .retrieve()
                         .bodyToMono(Void.class);
    }
}
