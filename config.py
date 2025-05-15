from dataclasses import dataclass

@dataclass
class Config:
    """Application configuration"""
    DEFAULT_DISCOUNT_PERCENTAGE: float = 0.10
    DEFAULT_STARTS_AT: str = "2025-01-01T00:00:00Z"
    DEFAULT_BATCH_SIZE: int = 15
    DEFAULT_SAVE_FREQUENCY: int = 3
    RETRY_DELAY: float = 0.5
    FILENAME_SUFFIX_LENGTH: int = 3
    BASE_FILENAME: str = "discount_code_results" 