from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class ConversionStats(BaseModel):
    total_files_created: int = 0
    txt_files_created: int = 0
    md_files_created: int = 0
    total_images_copied: int = 0
    name_conflicts_resolved: int = 0
    errors_encountered: int = 0
    topics_processed: int = 0
    html_files_processed: int = 0
    internal_links_preserved: int = 0
    tables_processed: int = 0
    metadata_files_created: int = 0
    html_backups_created: int = 0
    articles_with_valid_metadata: int = 0
    files_without_dc_identifier: int = 0
    files_with_duplicate_dc_identifier: int = 0
    files_with_long_filenames: int = 0
    files_skipped: int = 0
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def get_duration(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

class ValidationStats(BaseModel):
    total_articles: int = 0
    valid_articles: int = 0
    articles_with_errors: int = 0
    articles_with_warnings: int = 0
    articles_with_info: int = 0
    missing_mandatory: Dict[str, int] = {}
    missing_recommended: Dict[str, int] = {}
    missing_optional: Dict[str, int] = {}

class SkippedFileInfo(BaseModel):
    file_path: str
    reason: str
    details: Optional[Dict] = None