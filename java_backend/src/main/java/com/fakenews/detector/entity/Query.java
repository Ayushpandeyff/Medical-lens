// Query.java - Query Entity
package com.fakenews.detector.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "queries")
public class Query {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;
    
    @Column(columnDefinition = "TEXT", nullable = false)
    private String articleText;
    
    @Column(nullable = false)
    private String prediction;
    
    @Column(nullable = false)
    private Double confidence;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    // Constructors
    public Query() {}
    
    public Query(User user, String articleText, String prediction, Double confidence) {
        this.user = user;
        this.articleText = articleText;
        this.prediction = prediction;
        this.confidence = confidence;
        this.createdAt = LocalDateTime.now();
    }
    
    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    
    public String getArticleText() { return articleText; }
    public void setArticleText(String articleText) { this.articleText = articleText; }
    
    public String getPrediction() { return prediction; }
    public void setPrediction(String prediction) { this.prediction = prediction; }
    
    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
