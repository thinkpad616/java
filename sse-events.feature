Feature: Listen to SSE events

Background:
  * url sseUrl

Scenario: Consume events
  * def events = karate.web.listen(5) // Wait for up to 5 events
