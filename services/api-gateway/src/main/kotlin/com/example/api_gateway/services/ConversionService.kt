package com.example.api_gateway.services

import com.example.api_gateway.intefaces.ConversionInterface
import com.example.api_gateway.model.*
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.MediaType
import org.springframework.stereotype.Service
import org.springframework.web.reactive.function.client.WebClient
import org.springframework.web.reactive.function.client.WebClientResponseException
import org.springframework.web.reactive.function.client.bodyToMono
import org.springframework.web.util.UriComponentsBuilder
import java.util.*

@Service
class ConversionService(
    @Value("\${conversion.service.url}") private val serviceUrl: String,
    private val webClient: WebClient
) : ConversionInterface {

    override fun startConversion(request: ConvertRequest, traceparent: String?): ConvertResponse {
        return try {
            webClient.post()
                .uri("$serviceUrl/convert")
                .header("traceparent", traceparent)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono<ConvertResponse>()
                .block() ?: throw RuntimeException("Empty response")
        }catch (e: WebClientResponseException){
            throw RuntimeException("HTTP error: ${e.statusCode}: ${e.message}", e)
        }
    }

    override fun listJobs(status: JobStatus?, limit: Int, offset: Int, traceparent: String?): JobListResponse {
        val uri = UriComponentsBuilder.fromHttpUrl("$serviceUrl/convert")
            .queryParam("status", status)
            .queryParam("limit", limit)
            .queryParam("offset", offset)
            .build()
            .toUri()

        return try {
            webClient.get()
                .uri(uri)
                .header("traceparent", traceparent)
                .retrieve()
                .bodyToMono<JobListResponse>()
                .block() ?: throw RuntimeException("Empty response")
        }catch (e: WebClientResponseException){
            throw RuntimeException("HTTP error: ${e.statusCode}: ${e.message}", e)
        }
    }

    override fun getJogStatus(jobId: UUID, traceparent: String?): JobStatusResponse {
        return try {
            webClient.get()
                .uri("$serviceUrl/convert/$jobId/status")
                .header("traceparent", traceparent)
                .retrieve()
                .bodyToMono<JobStatusResponse>()
                .block() ?: throw RuntimeException("Empty response")
        }catch (e: WebClientResponseException){
            throw RuntimeException("HTTP error: ${e.statusCode}: ${e.message}", e)
        }
    }

    override fun cancelJob(jobId: UUID, traceparent: String?): CancelResponse {
        return try {
            webClient.post()
                .uri("$serviceUrl/convert/$jobId/cancel")
                .header("traceparent", traceparent)
                .retrieve()
                .bodyToMono<CancelResponse>()
                .block() ?: throw RuntimeException("Empty response")
        }catch (e: WebClientResponseException){
            throw RuntimeException("HTTP error: ${e.statusCode}: ${e.message}", e)
        }
    }
}