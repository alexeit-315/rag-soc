package com.example.api_gateway.model

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class ConversionStats(
    val totalHtmlFiles: Int,
    val totalTopics: Int,
    val totalFiles: Int,
    val txtFiles: Int,
    val mdFiles: Int,
    val metadataFiles: Int,
    val htmlBackups: Int,
    val imagesCopied: Int,
    val tablesProcessed: Int,
    val internalLinksPreserved: Int,
    val nameConflictsResolved: Int,
    val errorsEncountered: Int,
    val durationSeconds: Int
)
