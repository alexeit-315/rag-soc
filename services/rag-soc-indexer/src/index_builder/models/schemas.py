#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pydantic models for chunks and metadata
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

class ChunkMetadata(BaseModel):
    """Метаданные для чанка"""
    # Базовая информация
    source_file: str
    title: str
    section: str
    chunk_id: str
    start: int = 0
    length: int = 0

    # Расширенная информация из метаданных JSON
    dc_identifier: str = ""
    document_type: str = ""
    hierarchy_path: str = ""
    firmware_versions: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)

    # Связи между статьями
    parent_article_title: str = ""
    parent_article_md: str = ""
    previous_article_title: str = ""
    previous_article_md: str = ""
    next_article_title: str = ""
    next_article_md: str = ""

    class Config:
        arbitrary_types_allowed = True

class ChunkData(BaseModel):
    """Данные чанка"""
    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None

class ProcessingStats(BaseModel):
    """Статистика обработки"""
    total_files: int = 0
    total_chunks: int = 0
    files_with_errors: List[str] = Field(default_factory=list)
    processing_time: float = 0.0
    chunks_by_strategy: Dict[str, int] = Field(default_factory=dict)