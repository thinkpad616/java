package com.example;

import com.intuit.karate.http.apache.ApacheHttpClient;

public class TestRunner {
    public static void main(String[] args) {
        ApacheHttpClient client = new ApacheHttpClient();
        client.run("classpath:your-feature-file.feature");  // Replace with your feature file path
    }
}
