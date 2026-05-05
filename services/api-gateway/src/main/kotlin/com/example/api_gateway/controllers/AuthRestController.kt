package com.example.api_gateway.controllers

import com.example.api_gateway.model.RegisterRequest
import jakarta.validation.Valid
import org.springframework.http.ResponseEntity
import org.springframework.validation.BindingResult
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/auth")
class AuthRestController {

    @PostMapping("/register")
    fun register(@ModelAttribute  @Valid registerRequest: RegisterRequest,
                 bindingResult: BindingResult): ResponseEntity<Any> {

        if (bindingResult.hasErrors()) {
            val errors = mutableMapOf<String, String>()
            bindingResult.fieldErrors.forEach { error ->
                errors[error.field] = error.defaultMessage ?: "Ошибка валидации"
            }
            return ResponseEntity.badRequest().body(mapOf(
                "message" to "Ошибка валидации данных",
                "errors" to errors
            ))
        }

        // Здесь будет логика сохранения пользователя в БД
        // Например: userRepository.save(user)

        return ResponseEntity.ok(mapOf(
            "message" to "Пользователь зарегистрирован успешно!",
            "user" to mapOf(
                "name" to registerRequest.name,
                "email" to registerRequest.email
            )
        ))
    }
}
