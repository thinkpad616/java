Feature: SSE Handling and POST Trigger

Scenario: Wait for SSE events and trigger POST
  * configure headers = { 'Accept': 'text/event-stream' }
  * def events = call read('sse-events.feature')
  * def stopEvent = events[2] // Replace with logic to identify the stopping event
  * call read('post-api.feature') { data: stopEvent }


  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
    <version>2.7.4</version>
    <scope>test</scope>
  </dependency>
