package com.fakenews.detector.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.List;

@Service
public class RelatedNewsService {

    @Value("${serpapi.key}")
    private String serpApiKey;

    @Value("${serpapi.timeout:5000}") // Default 5 seconds if not set
    private int serpApiTimeout;

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5)) // Connection timeout
            .build();

    public List<String> getRelatedNewsLinks(String query) {
        List<String> newsLinks = new ArrayList<>();
        try {
            String url = "https://serpapi.com/search.json?q=" +
                    java.net.URLEncoder.encode(query, "UTF-8") +
                    "&tbm=nws&api_key=" + serpApiKey;

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofMillis(serpApiTimeout)) // Request timeout
                    .GET()
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            ObjectMapper mapper = new ObjectMapper();
            JsonNode root = mapper.readTree(response.body());
            JsonNode newsResults = root.get("news_results");

            if (newsResults != null && newsResults.isArray()) {
                int count = 0;
                for (JsonNode news : newsResults) {
                    if (news.has("link")) {
                        newsLinks.add(news.get("link").asText());
                        count++;
                        if (count >= 3) { // Limit to top 3
                            break;
                        }
                    }
                }
            }

        } catch (Exception e) {
            e.printStackTrace(); // Or use proper logging
        }
        return newsLinks;
    }
}


