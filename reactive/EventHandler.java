package com.example;

import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

// Import for Karate Apache 0.9.6
import com.intuit.karate.http.apache.ApacheHttpClient;

public class EventHandler {

    private final WebClient webClient;

    public EventHandler(WebClient webClient) {
        this.webClient = webClient;
    }

    public void handleEventsAndSendPost(String sseApiUrl, String postApiUrl) {
        Flux<String> events = webClient.get().uri(sseApiUrl)
                                        .retrieve()
                                        .bodyToFlux(String.class);

        events
            .filter(event -> event.contains("ping"))
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
