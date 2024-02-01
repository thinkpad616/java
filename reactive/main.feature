Feature: Handling events and terminating SSE

  Scenario: Handling pings and sending POST request
    Given url sse-api-url
    And def events = karate.http.sse.stream()
    And java.call('com.example.EventHandler', 'handleEventsAndSendPost', sseApiUrl, postApiUrl)
