// NewsController.java
package com.fakenews.detector.controller;

import com.fakenews.detector.entity.Query;
import com.fakenews.detector.entity.User;
import com.fakenews.detector.service.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;  // ← ADDED THIS IMPORT
import org.springframework.web.bind.annotation.*;
import javax.servlet.http.HttpSession;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/news")

public class NewsController {
    
    @Autowired
    private QueryService queryService;
    
    @Autowired
    private UserService userService;
    
    @Autowired
    private MLServiceClient mlServiceClient;
    @Autowired
    private MistralChatbotService mistralChatbotService;

    @Autowired
    private RelatedNewsService relatedNewsService;



    @PostMapping("/analyze")
    public ResponseEntity<Map<String, Object>> analyzeNews(@RequestBody Map<String, String> request, HttpSession session) {
        Map<String, Object> response = new HashMap<>();
        
        try {
            Long userId = (Long) session.getAttribute("userId");
            if (userId == null) {
                response.put("success", false);
                response.put("error", "User not authenticated");
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);  // ← FIXED THIS LINE
            }
            
            String username = (String) session.getAttribute("username");
            User user = userService.findByUsername(username);
            
            String articleText = request.get("text");
            if (articleText == null || articleText.trim().isEmpty()) {
                response.put("success", false);
                response.put("error", "Article text is required");
                return ResponseEntity.badRequest().body(response);
            }
            
            Query query = queryService.analyzeNews(user, articleText);
            
            response.put("success", true);
            response.put("result", Map.of(
                "id", query.getId(),
                "prediction", query.getPrediction(),
                "confidence", query.getConfidence(),
                "createdAt", query.getCreatedAt().toString()
            ));
            System.out.println("debug about to call");
            Map<String,Object> chatbotResult=mistralChatbotService.getChatbotResponse(articleText);
            System.out.println("debug result"+chatbotResult.keySet());
            Map<String,Object>chatbotResponse=new HashMap<>();
            if(chatbotResult.containsKey("response")&&chatbotResult.get("response")!=null){
                chatbotResponse.put("response",chatbotResult.get("response"));
                System.out.println("found response adding to output");
            }else{
              chatbotResponse.put("error","n0 response found");
                System.out.println("error no respponse found");
            }
            response.put("chatbot",chatbotResponse);
            // After chatbot response
            List<String> relatedNews = relatedNewsService.getRelatedNewsLinks(articleText);
            response.put("relatedNews", relatedNews);


            return ResponseEntity.ok(response);
        } catch (Exception e) {
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }
    
    @GetMapping("/history")
    public ResponseEntity<Map<String, Object>> getUserHistory(HttpSession session) {
        Map<String, Object> response = new HashMap<>();
        
        try {
            Long userId = (Long) session.getAttribute("userId");
            if (userId == null) {
                response.put("success", false);
                response.put("error", "User not authenticated");
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);  // ← FIXED THIS LINE
            }
            
            String username = (String) session.getAttribute("username");
            User user = userService.findByUsername(username);
            
            List<Query> queries = queryService.getUserHistory(user);
            
            List<Map<String, Object>> history = queries.stream().map(q -> {
                Map<String, Object> item = new HashMap<>();
                item.put("id", q.getId());
                item.put("text", q.getArticleText().substring(0, Math.min(100, q.getArticleText().length())) + "...");
                item.put("prediction", q.getPrediction());
                item.put("confidence", q.getConfidence());
                item.put("createdAt", q.getCreatedAt().toString());
                return item;
            }).collect(Collectors.toList());
            
            response.put("success", true);
            response.put("history", history);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }
    
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        Map<String, Object> response = new HashMap<>();
        response.put("backend", "healthy");
        response.put("mlService", mlServiceClient.isHealthy());
        return ResponseEntity.ok(response);
    }
}