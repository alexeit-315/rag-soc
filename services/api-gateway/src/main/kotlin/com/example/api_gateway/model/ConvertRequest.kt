package com.example.api_gateway.model

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming
import jakarta.validation.constraints.NotBlank
import jakarta.validation.constraints.Size

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class ConvertRequest(
    @field:NotBlank(message = "Путь к исходному документу или папке не может быть пустым")
    @field:Size(max = 1024, message = "Слишком большой путь sourceUri")
    val sourceUri: String,
    @field:Size(max = 1024, message = "Слишком большой путь outputUri")
    val outputUri: String ?= null,
    @field:Size(min = 1, max = 10000)
    val maxArticles: Int ?= null,
    val skipExtract: Boolean = false,
    @field:Size(min = 0, max = 3, message = "Уровень логирования может быть от 0 до 3\n(0: ERROR\n1: WARNING\n2: INFO\n3: DEBUG)")
    val logLevel: Int = 2
)
