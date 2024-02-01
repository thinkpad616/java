Feature: Handling events and terminating SSE

  Scenario: Handling pings and sending POST request
    Given url sse-api-url
    And def events = karate.apache.e2e.SSE.stream()
    And def pingCount = 0
    When events.subscribe({ event ->
      * if (event.data contains 'ping') karate.increment('pingCount')
      * if (pingCount == 3) karate.proceed()
    })
    And def response = events.await()
    Then def postResponse = post post-api-url
    # Assert response and termination behavior
