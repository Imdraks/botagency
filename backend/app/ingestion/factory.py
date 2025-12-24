"""
Connector factory - creates appropriate connector based on source type
"""
from app.db.models.source import SourceConfig
from app.db.models.opportunity import SourceType
from .base import BaseConnector
from .email_connector import EmailConnector
from .rss_connector import RSSConnector
from .html_connector import HTMLConnector
from .api_connector import APIConnector


def get_connector(config: SourceConfig) -> BaseConnector:
    """Get the appropriate connector for a source configuration"""
    connectors = {
        SourceType.EMAIL: EmailConnector,
        SourceType.RSS: RSSConnector,
        SourceType.HTML: HTMLConnector,
        SourceType.API: APIConnector,
    }
    
    connector_class = connectors.get(config.source_type)
    if not connector_class:
        raise ValueError(f"Unknown source type: {config.source_type}")
    
    return connector_class(config)
