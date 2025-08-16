// QueryService.java
package com.fakenews.detector.service;

import com.fakenews.detector.entity.Query;
import com.fakenews.detector.entity.User;
import com.fakenews.detector.repository.QueryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Map;  // ← ADDED THIS IMPORT

@Service
public class QueryService {
    
    @Autowired
    private QueryRepository queryRepository;
    
    @Autowired
    private MLServiceClient mlServiceClient;
    
    public Query analyzeNews(User user, String articleText) {
        // Call ML service
        var mlResult = mlServiceClient.predictNews(articleText);
        
        if (mlResult.containsKey("error")) {
            throw new RuntimeException("Analysis failed: " + mlResult.get("error"));
        }
        
        @SuppressWarnings("unchecked")
        //Map<String, Object> result = (Map<String, Object>) mlResult.get("result");
        String prediction="Fake";
        Double confidence=0.0;
        if(!mlResult.isEmpty()){
            prediction = (String) mlResult.get("prediction");
            confidence = (Double) mlResult.get("confidence");
        }

        //String prediction = (String) mlResult.get("prediction");
        //Double confidence = (Double) mlResult.get("confidence");
        
        // Save query to database
        Query query = new Query(user, articleText, prediction, confidence);
        return queryRepository.save(query);
    }
    
    public List<Query> getUserHistory(User user) {
        return queryRepository.findTop10ByUserOrderByCreatedAtDesc(user);
    }
}