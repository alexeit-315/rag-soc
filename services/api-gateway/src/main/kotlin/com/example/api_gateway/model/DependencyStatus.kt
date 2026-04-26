package com.example.api_gateway.model

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class DependencyStatus(
    val status: UpDownStatus,
    val latencyMs: Int,
    val error: String
)
