"""
DriveFolderMap Model
Stores Google Drive folder IDs for workspace structures.
Enables idempotent folder creation and quick lookup.
"""
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Index, UniqueConstraint, Text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.workspace import Workspace
    from app.db.models.user import User
    from app.db.models.agency import Project


# ============================================================================
# ENUMS
# ============================================================================

class DriveFolderType(str, enum.Enum):
    """Types of Drive folders tracked in the system"""
    # Root level
    ROOT = "ROOT"                           # Radar/
    PROJECTS_ROOT = "PROJECTS_ROOT"         # Radar/Projets/
    WORKSPACE_ROOT = "WORKSPACE_ROOT"       # Radar/00_Workspace/
    WORKSPACE_RESOURCES = "WORKSPACE_RESOURCES"  # Radar/00_Workspace/01_Ressources/
    WORKSPACE_ARCHIVE = "WORKSPACE_ARCHIVE"      # Radar/00_Workspace/99_Archive/
    
    # Templates
    TEMPLATES_ROOT = "TEMPLATES_ROOT"       # Radar/00_Workspace/00_Templates/
    TEMPLATES_DOCS = "TEMPLATES_DOCS"       # Radar/00_Workspace/00_Templates/Docs/
    TEMPLATES_SHEETS = "TEMPLATES_SHEETS"   # Radar/00_Workspace/00_Templates/Sheets/
    
    # Business (Radar Business addon)
    BUSINESS_ROOT = "BUSINESS_ROOT"         # Radar/Business/
    BUSINESS_QUOTES = "BUSINESS_QUOTES"     # Radar/Business/Devis/
    BUSINESS_INVOICES = "BUSINESS_INVOICES" # Radar/Business/Factures/
    BUSINESS_CREDITS = "BUSINESS_CREDITS"   # Radar/Business/Avoirs/
    BUSINESS_PAYMENTS = "BUSINESS_PAYMENTS" # Radar/Business/Paiements/
    BUSINESS_EXPORT = "BUSINESS_EXPORT"     # Radar/Business/Export_Compta/
    BUSINESS_ARCHIVE = "BUSINESS_ARCHIVE"   # Radar/Business/99_Archive/
    
    # Exports (analytics or intelligence pack)
    EXPORTS_ROOT = "EXPORTS_ROOT"           # Radar/Exports/
    EXPORTS_PDF = "EXPORTS_PDF"             # Radar/Exports/PDF/
    EXPORTS_CSV = "EXPORTS_CSV"             # Radar/Exports/CSV/
    EXPORTS_REPORTS = "EXPORTS_REPORTS"     # Radar/Exports/Reports/
    EXPORTS_ARCHIVE = "EXPORTS_ARCHIVE"     # Radar/Exports/99_Archive/
    
    # Discovery (discovery pack)
    DISCOVERY_ROOT = "DISCOVERY_ROOT"       # Radar/Discovery/
    DISCOVERY_ARTISTS = "DISCOVERY_ARTISTS" # Radar/Discovery/Artistes/
    DISCOVERY_WATCH = "DISCOVERY_WATCH"     # Radar/Discovery/Veille/
    DISCOVERY_COMPARE = "DISCOVERY_COMPARE" # Radar/Discovery/Comparaisons/
    DISCOVERY_ARCHIVE = "DISCOVERY_ARCHIVE" # Radar/Discovery/99_Archive/
    
    # Data (data pack)
    DATA_ROOT = "DATA_ROOT"                 # Radar/Data/
    DATA_SOURCES = "DATA_SOURCES"           # Radar/Data/Sources/
    DATA_LOGS = "DATA_LOGS"                 # Radar/Data/Logs/
    DATA_ARCHIVE = "DATA_ARCHIVE"           # Radar/Data/99_Archive/
    
    # Inbox (optional)
    INBOX_ROOT = "INBOX_ROOT"               # Radar/Inbox/
    INBOX_TRIAGE = "INBOX_TRIAGE"           # Radar/Inbox/A_trier/
    
    # Project level folders
    PROJECT_ROOT = "PROJECT_ROOT"           # Radar/Projets/<ProjectName>/
    PROJECT_ADMIN = "PROJECT_ADMIN"         # Radar/Projets/<ProjectName>/00_Admin/
    PROJECT_COMM = "PROJECT_COMM"           # Radar/Projets/<ProjectName>/01_Communication/
    PROJECT_ASSETS = "PROJECT_ASSETS"       # Radar/Projets/<ProjectName>/02_Assets/
    PROJECT_PROD = "PROJECT_PROD"           # Radar/Projets/<ProjectName>/03_Production/
    PROJECT_DELIVERABLES = "PROJECT_DELIVERABLES"  # Radar/Projets/<ProjectName>/04_Livrables/
    PROJECT_ARCHIVE = "PROJECT_ARCHIVE"     # Radar/Projets/<ProjectName>/99_Archive/
    
    # Project conditional subfolders
    PROJECT_ADMIN_BUSINESS = "PROJECT_ADMIN_BUSINESS"   # .../00_Admin/Business/
    PROJECT_ADMIN_BUSINESS_QUOTES = "PROJECT_ADMIN_BUSINESS_QUOTES"  # .../00_Admin/Business/Devis/
    PROJECT_ADMIN_BUSINESS_INVOICES = "PROJECT_ADMIN_BUSINESS_INVOICES"  # .../Business/Factures/
    PROJECT_ADMIN_BUSINESS_VALIDATIONS = "PROJECT_ADMIN_BUSINESS_VALIDATIONS"  # .../Business/Validations/
    PROJECT_ADMIN_REPORTING = "PROJECT_ADMIN_REPORTING"  # .../00_Admin/Reporting/
    PROJECT_ADMIN_SCORING = "PROJECT_ADMIN_SCORING"      # .../00_Admin/Scoring/
    PROJECT_COMM_WATCH = "PROJECT_COMM_WATCH"            # .../01_Communication/Veille/
    PROJECT_ASSETS_REFS = "PROJECT_ASSETS_REFS"          # .../02_Assets/Refs/


# ============================================================================
# DRIVE FOLDER MAP MODEL
# ============================================================================

class DriveFolderMap(Base):
    """
    Maps Drive folder IDs to workspace/project structures.
    Enables idempotent folder creation and quick lookup without Drive API calls.
    """
    __tablename__ = "drive_folder_map"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "google_account_id", "folder_type", "project_id",
            name="uq_drive_folder_map"
        ),
        Index("ix_drive_folder_map_workspace", "workspace_id"),
        Index("ix_drive_folder_map_google_account", "google_account_id"),
        Index("ix_drive_folder_map_type", "folder_type"),
        Index("ix_drive_folder_map_project", "project_id"),
        {"extend_existing": True}
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Workspace this folder belongs to
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Google account that owns this folder (user's Drive)
    google_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Type of folder (enum key)
    folder_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Project ID (nullable - only for project-level folders)
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Google Drive folder ID
    drive_folder_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Parent folder ID in Drive (for reference)
    drive_parent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Folder name in Drive
    folder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Full path (for debugging/display)
    folder_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Last verification timestamp (when we checked if folder still exists)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", backref="drive_folders")
    project: Mapped[Optional["Project"]] = relationship("Project", backref="drive_folders")

    def __repr__(self):
        return f"<DriveFolderMap {self.folder_type} -> {self.drive_folder_id}>"

    @property
    def drive_url(self) -> str:
        """Get the Google Drive folder URL"""
        return f"https://drive.google.com/drive/folders/{self.drive_folder_id}"
