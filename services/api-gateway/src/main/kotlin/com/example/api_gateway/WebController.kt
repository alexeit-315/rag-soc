package com.example.api_gateway

import com.example.api_gateway.model.RegisterRequest
import org.springframework.stereotype.Controller
import org.springframework.ui.Model
import org.springframework.web.bind.annotation.GetMapping


@Controller
class WebController {
    @GetMapping("/")
    fun home(): String {
        return "index"
    }

    @GetMapping("/register")
    fun showRegistrationForm(model: Model): String {
        model.addAttribute("registerRequest", RegisterRequest("", "", ""))
        return "register"
    }
    // ... остальные методы для веб-формы
}