package com.example.api_gateway.model

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming
import java.time.Instant
import java.util.UUID

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class JobSummary(
    val jobId: UUID,
    val status: JobStatus,
    val sourceUri: String,
    val outputUri: String?,
    val createdAt: Instant,
    val startedAt: Instant?,
    val completedAt: Instant?
)
