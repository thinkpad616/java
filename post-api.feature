Feature: Send POST API

Scenario: Trigger event
  * url postUrl
  * request { data: '#(data)' }
  * method post
