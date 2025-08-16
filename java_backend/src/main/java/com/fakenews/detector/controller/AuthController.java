package com.fakenews.detector.controller;

import com.fakenews.detector.entity.User;
import com.fakenews.detector.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpSession;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    
    @Autowired
    private UserService userService;
    
    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> register(
            @RequestBody Map<String, String> request, 
            HttpSession session,
            HttpServletRequest httpRequest,
            HttpServletResponse httpResponse) {
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            String username = request.get("username");
            String email = request.get("email");
            String password = request.get("password");
            
            System.out.println("=== REGISTER REQUEST ===");
            System.out.println("Username: " + username);
            System.out.println("Session ID before register: " + session.getId());
            System.out.println("Session isNew: " + session.isNew());
            
            User user = userService.registerUser(username, email, password);
            
            // Clear any existing session data
            session.invalidate();
            // Get new session
            session = httpRequest.getSession(true);
            
            // Set session attributes
            session.setAttribute("userId", user.getId());
            session.setAttribute("username", user.getUsername());
            session.setMaxInactiveInterval(1800); // 30 minutes
            
            System.out.println("New Session ID after register: " + session.getId());
            System.out.println("User ID stored in session: " + session.getAttribute("userId"));
            
            // Set session cookie explicitly
            httpResponse.setHeader("Set-Cookie", 
                "JSESSIONID=" + session.getId() + 
                "; Path=/; HttpOnly; SameSite=Lax; Max-Age=1800");
            
            response.put("success", true);
            response.put("message", "User registered successfully");
            response.put("user", Map.of(
                "id", user.getId(), 
                "username", user.getUsername(), 
                "email", user.getEmail()
            ));
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            System.err.println("Registration error: " + e.getMessage());
            e.printStackTrace();
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }
    
    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(
            @RequestBody Map<String, String> request, 
            HttpSession session,
            HttpServletRequest httpRequest,
            HttpServletResponse httpResponse) {
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            String username = request.get("username");
            String password = request.get("password");
            
            System.out.println("=== LOGIN REQUEST ===");
            System.out.println("Username: " + username);
            System.out.println("Session ID before login: " + session.getId());
            System.out.println("Session isNew: " + session.isNew());
            System.out.println("Existing userId in session: " + session.getAttribute("userId"));
            
            User user = userService.loginUser(username, password);
            
            // Invalidate existing session and create new one
            session.invalidate();
            session = httpRequest.getSession(true);
            
            // Set session attributes
            session.setAttribute("userId", user.getId());
            session.setAttribute("username", user.getUsername());
            session.setMaxInactiveInterval(1800); // 30 minutes
            
            System.out.println("New Session ID after login: " + session.getId());
            System.out.println("User ID stored in session: " + session.getAttribute("userId"));
            
            // Set session cookie explicitly
            httpResponse.setHeader("Set-Cookie", 
                "JSESSIONID=" + session.getId() + 
                "; Path=/; HttpOnly; SameSite=Lax; Max-Age=1800");
            
            response.put("success", true);
            response.put("message", "Login successful");
            response.put("user", Map.of(
                "id", user.getId(), 
                "username", user.getUsername(), 
                "email", user.getEmail()
            ));
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            System.err.println("Login error: " + e.getMessage());
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }
    
    @PostMapping("/logout")
    public ResponseEntity<Map<String, Object>> logout(HttpSession session) {
        System.out.println("=== LOGOUT REQUEST ===");
        System.out.println("Session ID: " + session.getId());
        System.out.println("User ID in session: " + session.getAttribute("userId"));
        
        session.invalidate();
        
        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("message", "Logout successful");
        return ResponseEntity.ok(response);
    }
    
    @GetMapping("/me")
    public ResponseEntity<Map<String, Object>> getCurrentUser(
            HttpSession session,
            HttpServletRequest request) {
        
        Map<String, Object> response = new HashMap<>();
        
        System.out.println("=== AUTH CHECK REQUEST ===");
        System.out.println("Session ID: " + session.getId());
        System.out.println("Session isNew: " + session.isNew());
        System.out.println("Request URL: " + request.getRequestURL());
        System.out.println("Request method: " + request.getMethod());
        
        // Print all cookies
        if (request.getCookies() != null) {
            System.out.println("=== COOKIES ===");
            for (javax.servlet.http.Cookie cookie : request.getCookies()) {
                System.out.println("Cookie: " + cookie.getName() + " = " + cookie.getValue());
            }
        } else {
            System.out.println("No cookies found in request");
        }
        
        Long userId = (Long) session.getAttribute("userId");
        String username = (String) session.getAttribute("username");
        
        System.out.println("User ID from session: " + userId);
        System.out.println("Username from session: " + username);
        
        if (userId != null && username != null) {
            response.put("authenticated", true);
            response.put("user", Map.of("id", userId, "username", username));
            System.out.println("User is authenticated");
        } else {
            response.put("authenticated", false);
            System.out.println("User is NOT authenticated");
        }
        
        return ResponseEntity.ok(response);
    }
}