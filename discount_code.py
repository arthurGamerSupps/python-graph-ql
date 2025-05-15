from dataclasses import dataclass
from typing import Optional
from code_status import CodeStatus

@dataclass
class DiscountCode:
    """Discount code model"""
    code: str
    id: Optional[str] = None
    title: Optional[str] = None
    status: CodeStatus = CodeStatus.NOT_FOUND 