Scenario: Test SSE API and send async SDP requests
  * def asyncResult = callAsync listenForEventsAndPostSDP()

  * def response = http.get('http://some-other-api')
  * match response.status == 200

  * // ... other test steps

  * await asyncResult  // Wait for async task to complete
