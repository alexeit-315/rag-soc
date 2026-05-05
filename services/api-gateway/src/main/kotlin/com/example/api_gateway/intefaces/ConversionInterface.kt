package com.example.api_gateway.intefaces

import com.example.api_gateway.model.*
import java.util.UUID

interface ConversionInterface {
    fun startConversion(request: ConvertRequest, traceparent: String?): ConvertResponse
    fun listJobs(status: JobStatus?, limit: Int, offset: Int, traceparent: String?): JobListResponse
    fun getJogStatus(jobId: UUID, traceparent: String?): JobStatusResponse
    fun cancelJob(jobId: UUID, traceparent: String?): CancelResponse
}