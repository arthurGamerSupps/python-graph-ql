import logging
from discount_code_repository import DiscountCodeRepository
from discount_code import DiscountCode
from code_status import CodeStatus
from code_validator import CodeValidator
from exceptions import CodeValidationException

class DiscountCodeService:
    """Business logic for discount code operations"""
    
    def __init__(self, repository: DiscountCodeRepository):
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    def ensure_code_exists(self, code: str) -> DiscountCode:
        """Check if code exists, create if not"""
        try:
            clean_code = CodeValidator.clean(code)
            
            # Check if exists
            existing_id = self.repository.find_by_code(clean_code)
            if existing_id:
                return DiscountCode(
                    code=clean_code,
                    id=existing_id,
                    status=CodeStatus.VALID
                )
            
            # Skip creation of new codes
            self.logger.info(f"Skipping creation of new code: {clean_code}")
            return DiscountCode(
                code=clean_code,
                status=CodeStatus.SKIPPED_CREATION
            )
            
        except CodeValidationException:
            return DiscountCode(
                code=str(code),
                status=CodeStatus.INVALID_FORMAT
            )
        except Exception as e:
            self.logger.error(f"Unexpected error processing code '{code}': {e}")
            return DiscountCode(
                code=str(code),
                status=CodeStatus.EXCEPTION
            ) 