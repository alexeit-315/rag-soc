from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pathlib import Path

class DocumentType(str, Enum):
    CONFIGURATION_GUIDE = "configuration_guide"
    CLI_COMMAND = "cli_command"
    CONCEPT = "concept"
    UNKNOWN = "unknown"
    
class SectionType(str, Enum):
    CONTENT = "content"
    FUNCTION = "function"
    FORMAT = "format"
    PARAMETERS = "parameters"
    EXAMPLE = "example"
    CONFIGURATION_GUIDE = "configuration_guide"
    UNKNOWN = "unknown"

class ApplicabilityScope(str, Enum):
    ENTIRE_HDX = "entire_hdx"
    SPECIFIC_ARTICLE = "specific_article"
    UNKNOWN = "unknown"

class HierarchyItem(BaseModel):
    title: str
    dc_identifier: str = ""
    html_filename: str = ""
    md_filename: str = ""

class SectionStructure(BaseModel):
    section_id: str
    title: str
    type: SectionType = SectionType.UNKNOWN

class FirmwareVersions(BaseModel):
    primary: str = ""
    all_versions: List[str] = []
    applicability_scope: ApplicabilityScope = ApplicabilityScope.UNKNOWN
    confirmed_by_user: bool = False

class Platforms(BaseModel):
    product_series: str = ""
    compatible_models: List[str] = []
    model_limitations: Dict[str, Any] = {}
    applicability_scope: ApplicabilityScope = ApplicabilityScope.UNKNOWN
    confirmed_by_user: bool = False

class ContentFlags(BaseModel):
    contains_cli_commands: bool = False
    contains_configuration_steps: bool = False
    contains_tables: bool = False
    contains_code_examples: bool = False
    contains_warnings: bool = False

class TechnicalMetadata(BaseModel):
    firmware_versions: FirmwareVersions = Field(default_factory=FirmwareVersions)
    platforms: Platforms = Field(default_factory=Platforms)
    features: List[str] = []
    content_flags: ContentFlags = Field(default_factory=ContentFlags)

class RelatedArticle(BaseModel):
    title: str = ""
    dc_identifier: str = ""
    html_filename: str = ""
    html_path: str = ""
    md_filename: str = ""

    class Config:
        # Разрешаем сериализацию пустых строк
        json_encoders = {
            str: lambda v: v if v else None
        }

class InternalLink(BaseModel):
    text: str
    dc_identifier: str = ""
    html_filename: str = ""
    html_path: str = ""
    md_filename: str = ""

class ExternalLink(BaseModel):
    text: str
    url: str

class Relations(BaseModel):
    parent_article: RelatedArticle = Field(default_factory=RelatedArticle)
    previous_article: RelatedArticle = Field(default_factory=RelatedArticle)
    next_article: RelatedArticle = Field(default_factory=RelatedArticle)
    internal_links: List[InternalLink] = []
    external_links: List[ExternalLink] = []

class MissingFields(BaseModel):
    mandatory: List[str] = []
    recommended: List[str] = []
    optional: List[str] = []

class Validation(BaseModel):
    is_valid: bool = False
    missing_fields: MissingFields = Field(default_factory=MissingFields)
    errors: List[str] = []
    warnings: List[str] = []
    info: List[str] = []

class SourceInfo(BaseModel):
    hdx_filename: str = ""
    html_filename: str
    html_path: str
    extraction_date: str
    json_filename: str = ""
    md_filename: str = ""
    hdx_hash: str = ""

class ArticleMetadata(BaseModel):
    metadata_version: str = "1.2"
    source: SourceInfo
    article: Dict[str, Any]
    technical_metadata: TechnicalMetadata
    relations: Relations
    validation: Validation

    class Config:
        arbitrary_types_allowed = True

    def dict(self, **kwargs):
        # Переопределяем сериализацию для обработки Enum и пустых строк
        data = super().model_dump(mode='json', **kwargs)
        return self._clean_serialized_data(data)

    def _clean_serialized_data(self, data):
        """Очистка сериализованных данных"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, Enum):
                    result[key] = value.value
                elif isinstance(value, bool):
                    result[key] = value
                elif isinstance(value, str) and not value:
                    result[key] = None
                elif isinstance(value, (dict, list)):
                    result[key] = self._clean_serialized_data(value)
                else:
                    result[key] = value
            return result
        elif isinstance(data, list):
            return [self._clean_serialized_data(item) for item in data]
        return data