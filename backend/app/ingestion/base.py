"""
Base connector class
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.db.models.source import SourceConfig


class BaseConnector(ABC):
    """Base class for all data source connectors"""
    
    def __init__(self, config: SourceConfig):
        self.config = config
        self.errors: List[str] = []
    
    @abstractmethod
    async def fetch(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch raw items from the source.
        Returns a list of dictionaries with raw data.
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the connection to the source works"""
        pass
    
    def log_error(self, error: str):
        """Log an error"""
        self.errors.append(f"[{datetime.utcnow().isoformat()}] {error}")
    
    def get_errors(self) -> List[str]:
        """Get all logged errors"""
        return self.errors
    
    def clear_errors(self):
        """Clear all logged errors"""
        self.errors = []
