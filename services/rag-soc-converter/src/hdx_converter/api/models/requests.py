"""Pydantic models for API requests/responses."""
from pydantic import BaseModel, Field, validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Статус задачи конвертации."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConvertRequest(BaseModel):
    """Запрос на конвертацию."""
    source_uri: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Путь к исходному документу или папке"
    )
    output_uri: Optional[str] = Field(
        None,
        min_length=1,
        max_length=1024,
        description="Выходная директория для результатов"
    )
    max_articles: Optional[int] = Field(
        None,
        ge=1,
        le=100000,
        description="Обработать только первые N статей"
    )
    skip_extract: bool = Field(
        False,
        description="Пропустить извлечение HDX"
    )
    log_level: int = Field(
        2,
        ge=0,
        le=3,
        description="Уровень логирования: 0=ERROR, 1=WARNING, 2=INFO, 3=DEBUG"
    )

    @validator('source_uri')
    def validate_source_uri(cls, v):
        if not v or not v.strip():
            raise ValueError('source_uri cannot be empty')
        return v.strip()


class ConvertResponse(BaseModel):
    """Ответ на запрос конвертации."""
    job_id: UUID
    status: JobStatus
    source_uri: str
    output_uri: Optional[str]
    created_at: datetime


class JobStatusResponse(BaseModel):
    """Статус задачи."""
    job_id: UUID
    status: JobStatus
    progress_percent: int = 0
    source_uri: str
    output_uri: Optional[str]
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    statistics: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobSummary(BaseModel):
    """Краткая информация о задаче."""
    job_id: UUID
    status: JobStatus
    source_uri: str
    output_uri: Optional[str]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobListResponse(BaseModel):
    """Список задач."""
    jobs: list[JobSummary]
    total: int
    limit: int
    offset: int


class CancelResponse(BaseModel):
    """Ответ на отмену задачи."""
    job_id: UUID
    status: JobStatus
    message: str


class ErrorResponse(BaseModel):
    """Ответ с ошибкой."""
    error: str
    code: str
    details: Optional[dict] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None