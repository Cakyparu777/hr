"""
Pagination utilities for DynamoDB operations.
"""
from typing import List, Dict, Optional, Any
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PaginatedResponse:
    """Paginated response wrapper."""
    def __init__(
        self,
        items: List[Dict[str, Any]],
        total: int,
        page: int,
        page_size: int,
        has_next: bool = False,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.has_next = has_next
        self.last_evaluated_key = last_evaluated_key
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "has_next": self.has_next
        }


def validate_pagination_params(page: Optional[int] = None, page_size: Optional[int] = None) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Tuple of (page, page_size)
    """
    if page is None or page < 1:
        page = 1
    
    if page_size is None or page_size < 1:
        page_size = settings.DEFAULT_PAGE_SIZE
    elif page_size > settings.MAX_PAGE_SIZE:
        page_size = settings.MAX_PAGE_SIZE
    
    return page, page_size

