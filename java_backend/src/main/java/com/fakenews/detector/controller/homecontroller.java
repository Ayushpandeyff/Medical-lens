package com.fakenews.detector.controller;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

public class homecontroller {



    @Controller
    public class HomeController {

        @GetMapping("/")
        public String home() {
            // Return the HTML file name WITHOUT the .html extension
            return "index";  // if your HTML file is index.html
        }
    }

}
