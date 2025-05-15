from enum import Enum

class CodeStatus(Enum):
    """Status of discount code processing"""
    VALID = "VALID"
    INVALID_FORMAT = "NO_ID_invalid_format"
    CREATION_FAILED = "NO_ID_creation_failed"
    EXCEPTION = "NO_ID_exception"
    NOT_FOUND = "NO_ID"
    SKIPPED_CREATION = "NO_ID_skipped_creation" 