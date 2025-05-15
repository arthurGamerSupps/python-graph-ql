class DiscountCodeException(Exception):
    """Base exception for discount code operations"""
    pass


class CodeCreationException(DiscountCodeException):
    """Exception raised when code creation fails"""
    pass


class CodeValidationException(DiscountCodeException):
    """Exception raised when code validation fails"""
    pass


class FileOperationException(DiscountCodeException):
    """Exception raised when file operations fail"""
    pass 