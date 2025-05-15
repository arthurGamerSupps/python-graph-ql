from typing import Any
from exceptions import CodeValidationException

class CodeValidator:
    """Validates and cleans discount codes"""
    
    @staticmethod
    def is_valid(code: Any) -> bool:
        """Check if code is valid"""
        return (isinstance(code, str) and 
                bool(code.strip()) and 
                len(code.strip()) > 0)
    
    @staticmethod
    def clean(code: str) -> str:
        """Clean and normalize code"""
        if not CodeValidator.is_valid(code):
            raise CodeValidationException(f"Invalid code format: {code}")
        return code.strip() 