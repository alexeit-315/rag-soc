package com.example.api_gateway.model

import jakarta.validation.constraints.NotBlank
import jakarta.validation.constraints.Email
import jakarta.validation.constraints.Size

data class RegisterRequest (
    @field:NotBlank(message = "Имя не может быть пустым")
    @field:Size(min = 2, max = 50, message = "Имя должно содержать от 2 до 50 символов")
    val name: String,

    @field:NotBlank(message = "Email не может быть пустым")
    @field:Email(message = "Некорректный email")
    val email: String,

    @field:NotBlank(message = "Пароль не может быть пустым")
    @field:Size(min = 6, message = "Пароль должен содержать минимум 6 символов")
    val password: String
)