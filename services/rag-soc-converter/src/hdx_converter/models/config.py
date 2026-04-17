# models/config.py (добавляем в класс ConverterConfig)
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import List, Dict, Any, Optional, Pattern
from datetime import datetime
import re

class ConverterConfig(BaseSettings):
    """Конфигурация конвертера"""
    
    # Основные настройки
    output_dir: Path = Field(default=Path("hdx_output"))
    skip_extract: bool = Field(default=False)
    max_articles: Optional[int] = Field(default=None)

    # Добавляем поле для пути к HDX файлу (исправление пункта 18)
    hdx_file_path: Optional[Path] = Field(default=None)
    
    # Настройки форматов вывода
    generate_markdown: bool = Field(default=True)
    generate_text: bool = Field(default=True)
    generate_json_metadata: bool = Field(default=True)
    copy_images: bool = Field(default=True)
    backup_html: bool = Field(default=True)
    
    # Настройки валидации и логирования
    validate_metadata: bool = Field(default=True)
    collect_statistics: bool = Field(default=True)
    print_statistics: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    
    # Настройки именования директорий
    images_dir_name: str = Field(default="images")
    metadata_dir_name: str = Field(default="meta_data")
    html_backup_dir_name: str = Field(default="html_backup")
    txt_dir_name: str = Field(default="txt_data")  # ИЗМЕНЕНО: было "text"
    md_dir_name: str = Field(default="md_data")    # ИЗМЕНЕНО: было "markdown"
    json_data_dir_name: str = Field(default="json_data")  # ДОБАВЛЕНО
    temp_extract_dir_name: str = Field(default="temp_extract")
    
    # Имена файлов
    log_file: str = Field(default="conversion_log.txt")
    mapping_file: str = Field(default="filename_mapping.json")
    
    # Глобальные метаданные
    global_firmware_versions: Dict[str, Any] = Field(default={
        "primary": "",
        "all_versions": [],
        "applicability_scope": "unknown",
        "confirmed_by_user": False
    })
    
    global_platforms: Dict[str, Any] = Field(default={
        "product_series": "",
        "compatible_models": [],
        "model_limitations": {},
        "applicability_scope": "unknown",
        "confirmed_by_user": False
    })
    
    # Поля для валидации
    # === ИЗМЕНЕНИЕ: Переименование полей для однозначного маппинга ===
    # Обязательные поля (mandatory)
    mandatory_fields: List[str] = Field(default=[
        "source.html_filename",
        "source.html_path",
        "source.extraction_date",
        "source.json_filename",
        "source.md_filename",
        "article.title",
        "article.dc_identifier",
        "article.md_filename",
        "article.hierarchy",
        "article.section_structure",
        "technical_metadata.firmware_versions.primary",
        "technical_metadata.firmware_versions.applicability_scope",
        "technical_metadata.firmware_versions.confirmed_by_user",
        "technical_metadata.platforms.product_series",
        "technical_metadata.platforms.applicability_scope",
        "technical_metadata.platforms.confirmed_by_user",
        "technical_metadata.content_flags",
        "validation"
    ])

    # Строго желательные поля (recommended) - бывшее strictly_desirable_fields
    recommended_fields: List[str] = Field(default=[
        "article.document_type",
        "article.language",
        "article.dc_publisher",
        "article.dc_audience_job",
        "technical_metadata.platforms.compatible_models",
        "relations.parent_article",
        "relations.previous_article",
        "relations.next_article",
        "relations.internal_links",
        "relations.external_links"
    ])

    # Желательные поля (optional) - бывшее recommended_fields
    optional_fields: List[str] = Field(default=[
        "article.prodname",
        "article.version",
        "article.brand",
        "article.addwebmerge"
    ])
    # === КОНЕЦ ИЗМЕНЕНИЯ ===
    
    # Настройки именования
    max_filename_length: int = Field(default=255)
    sanitize_filenames: bool = Field(default=True)
    preserve_original_names: bool = Field(default=False)
    
    # Добавляем отсутствующий атрибут
    clean_filename_pattern: Pattern = Field(default=re.compile(r'[<>:"/\\|?*]'))
    
    # Настройки обработки
    extract_only_first_level: bool = Field(default=False)
    save_skipped_files: bool = Field(default=True)
    force_overwrite: bool = Field(default=False)
    
    class Config:
        env_file = ".env"
        env_prefix = "hdx_"
        case_sensitive = False
        arbitrary_types_allowed = True