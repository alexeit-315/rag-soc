package com.example.api_gateway.model

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming
import jakarta.validation.constraints.Size
import java.time.Instant
import java.util.UUID

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class JobStatusResponse(
    val jobId: UUID,
    val status: JobStatus,
    @field:Size(min = 0, max = 100)
    val progressPercent: Int,
    val sourceUri: String,
    val outputUri: String?,
    val errorMessage: String?,
    val warningMessage: String?,
    val statistics: ConversionStatistics?,
    val startedAt: Instant?,
    val completedAt: Instant?
)