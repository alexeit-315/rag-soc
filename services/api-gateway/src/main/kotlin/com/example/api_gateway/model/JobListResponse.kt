package com.example.api_gateway.model

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class JobListResponse(
    val jobs: JobSummary,
    val total: Int,
    val limit: Int,
    val offset: Int
)
