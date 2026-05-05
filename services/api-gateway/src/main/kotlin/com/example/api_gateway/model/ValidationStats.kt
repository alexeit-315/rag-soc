package com.example.api_gateway.model

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class ValidationStats(
    val totalArticles: Int,
    val validArticles: Int,
    val articlesWithErrors: Int,
    val articlesWithWarnings: Int
)
