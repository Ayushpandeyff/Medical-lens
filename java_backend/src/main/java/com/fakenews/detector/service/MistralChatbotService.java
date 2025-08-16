package com.fakenews.detector.service;


import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@Service
public class MistralChatbotService {

    @Value("${mistral.api.key}")
    private String mistralApiKey;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    public Map<String, Object> getChatbotResponse(String articleText) {
        try {
            String url = "https://api.mistral.ai/v1/chat/completions";

            // Set headers
            HttpHeaders headers = new HttpHeaders();
            headers.set("Authorization", "Bearer " + mistralApiKey);
            headers.setContentType(MediaType.APPLICATION_JSON);

            // Create prompt
            String prompt = String.format(
                    "Analyze this news article and provide helpful context:\n\n" +
                            "\"%s\"\n\n" +
                            "Please provide:\n" +
                            "1. A brief analysis of the topic\n" +
                            "2. Key facts to verify\n" +
                            "3. Related verified sources or similar news (if any)\n" +
                            "4. Red flags to watch for in this type of news\n\n" +
                            "Keep your response informative but concise (under 300 words).\n",
                    articleText
            );


            // Build JSON payload
            ObjectNode payload = objectMapper.createObjectNode();
            payload.put("model", "mistral-small");
            payload.put("max_tokens", 400);
            payload.put("temperature", 0.7);

            // Create messages array
            ArrayNode messages = objectMapper.createArrayNode();

            // System message
            ObjectNode systemMessage = objectMapper.createObjectNode();
            systemMessage.put("role", "system");
            systemMessage.put("content", "You are a helpful fact-checking assistant that provides context and verification guidance for news articles.");
            messages.add(systemMessage);

            // User message
            ObjectNode userMessage = objectMapper.createObjectNode();
            userMessage.put("role", "user");
            userMessage.put("content", prompt);
            messages.add(userMessage);

            payload.set("messages", messages);

            // Make HTTP request
            HttpEntity<String> entity = new HttpEntity<>(payload.toString(), headers);
            ResponseEntity<String> response = restTemplate.exchange(
                    url,
                    HttpMethod.POST,
                    entity,
                    String.class
            );

            // Parse response
            JsonNode responseJson = objectMapper.readTree(response.getBody());
            String content = responseJson
                    .path("choices")
                    .get(0)
                    .path("message")
                    .path("content")
                    .asText()
                    .strip();

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("response", content);
            return result;

        } catch (Exception e) {
            Map<String, Object> result = new HashMap<>();
            result.put("success", false);
            result.put("error", "Chatbot service unavailable: " + e.getMessage());
            return result;
        }
    }
}


