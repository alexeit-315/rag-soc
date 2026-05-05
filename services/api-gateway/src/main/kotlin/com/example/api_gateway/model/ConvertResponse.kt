package com.example.api_gateway.model

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming
import java.time.Instant
import java.util.*

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class ConvertResponse(
    val jobId: UUID,
    val status: JobStatus,
    val sourceUri: String,
    val outputUri: String?,
    val createdAt: Instant
)