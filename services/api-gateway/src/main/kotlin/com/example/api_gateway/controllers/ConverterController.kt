package com.example.api_gateway.controllers

import com.example.api_gateway.model.*
import com.example.api_gateway.intefaces.ConversionInterface
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import java.util.UUID

@RestController
@RequestMapping("/convert")
class ConverterController(
    @Autowired private val conversionService: ConversionInterface
) {
    @PostMapping()
    fun convert(
        @RequestHeader(value = "traceparent", required = false) traceparent: String?,
        @RequestBody request: ConvertRequest
    ): ResponseEntity<ConvertResponse>{
        val job = conversionService.startConversion(request, traceparent)
        return ResponseEntity.accepted().body(job)
    }
    @GetMapping()
    fun listJobs(
        @RequestHeader(value = "traceparent", required = false) traceparent: String?,
        @RequestParam status: JobStatus? = null,
        @RequestParam limit: Int = 50,
        @RequestParam offset: Int = 0
        ): ResponseEntity<JobListResponse>{
        val jobs = conversionService.listJobs(status, limit, offset, traceparent)
        return ResponseEntity.ok(jobs)
    }
    @GetMapping("/{jobId}/status")
    fun getJobStatus(
        @RequestHeader(value = "traceparent", required = false) traceparent: String?,
        @PathVariable("jobId") jobId: UUID
    ): ResponseEntity<JobStatusResponse>{
        val job = conversionService.getJogStatus(jobId, traceparent)
        return ResponseEntity.ok(job)
    }
    @PostMapping("/{jobId}/cancel")
    fun cancelJob(
        @RequestHeader(value = "traceparent", required = false) traceparent: String?,
        @PathVariable("jobId") jobId: UUID
    ): ResponseEntity<CancelResponse>{
        val result = conversionService.cancelJob(jobId, traceparent)
        return ResponseEntity.ok(result)
    }
}