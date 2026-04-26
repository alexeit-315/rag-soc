package com.example.api_gateway.model

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class HealthResponse(
    val status: HealthStatus,
    val version: String,
    val components: Map<String, DependencyStatus>
)
