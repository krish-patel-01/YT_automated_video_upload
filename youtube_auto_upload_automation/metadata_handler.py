"""Metadata handling for video uploads."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class VideoMetadata:
    """Container for video metadata."""
    
    def __init__(
        self,
        title: str,
        description: str = "",
        tags: list[str] = None,
        category_id: str = "22",
        privacy_status: str = "private",
        made_for_kids: bool = False
    ):
        """Initialize video metadata.
        
        Args:
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID
            privacy_status: Privacy status (public, private, unlisted)
            made_for_kids: Whether video is made for kids
        """
        self.title = title
        self.description = description
        self.tags = tags or []
        self.category_id = category_id
        self.privacy_status = privacy_status
        self.made_for_kids = made_for_kids
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary.
        
        Returns:
            Dictionary representation of metadata
        """
        return {
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'category_id': self.category_id,
            'privacy_status': self.privacy_status,
            'made_for_kids': self.made_for_kids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoMetadata':
        """Create metadata from dictionary.
        
        Args:
            data: Dictionary containing metadata
            
        Returns:
            VideoMetadata instance
        """
        return cls(
            title=data.get('title', ''),
            description=data.get('description', ''),
            tags=data.get('tags', []),
            category_id=data.get('category_id', '22'),
            privacy_status=data.get('privacy_status', 'private'),
            made_for_kids=data.get('made_for_kids', False)
        )


class MetadataHandler:
    """Handle loading and parsing of video metadata."""
    
    def __init__(
        self,
        metadata_file_suffix: str,
        default_title_template: str,
        default_description: str,
        default_tags: list[str]
    ):
        """Initialize metadata handler.
        
        Args:
            metadata_file_suffix: Suffix for metadata files
            default_title_template: Template for default title
            default_description: Default description
            default_tags: Default tags
        """
        self.metadata_file_suffix = metadata_file_suffix
        self.default_title_template = default_title_template
        self.default_description = default_description
        self.default_tags = default_tags
    
    def get_metadata_file_path(self, video_path: str) -> str:
        """Get the metadata file path for a video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to metadata file
        """
        video_path_obj = Path(video_path)
        stem = video_path_obj.stem
        directory = video_path_obj.parent
        
        metadata_filename = f"{stem}{self.metadata_file_suffix}"
        return str(directory / metadata_filename)
    
    def load_metadata(self, video_path: str) -> VideoMetadata:
        """Load metadata for a video file.
        
        Looks for a metadata JSON file alongside the video file.
        If not found, generates default metadata.
        
        Args:
            video_path: Path to video file
            
        Returns:
            VideoMetadata instance
        """
        metadata_path = self.get_metadata_file_path(video_path)
        
        # Try to load from metadata file
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = VideoMetadata.from_dict(data)
                logger.info(f"Loaded metadata from {metadata_path}")
                return metadata
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in metadata file {metadata_path}: {e}")
            except Exception as e:
                logger.error(f"Failed to load metadata from {metadata_path}: {e}")
        else:
            logger.info(f"No metadata file found at {metadata_path}, using defaults")
        
        # Generate default metadata
        return self._generate_default_metadata(video_path)
    
    def _generate_default_metadata(self, video_path: str) -> VideoMetadata:
        """Generate default metadata for a video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            VideoMetadata instance with default values
        """
        filename = Path(video_path).stem
        
        # Apply title template
        title = self.default_title_template.replace('{filename}', filename)
        
        return VideoMetadata(
            title=title,
            description=self.default_description,
            tags=self.default_tags.copy()
        )
    
    def save_metadata_template(self, video_path: str) -> bool:
        """Save a metadata template file for a video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if template saved successfully
        """
        metadata_path = self.get_metadata_file_path(video_path)
        
        if os.path.exists(metadata_path):
            logger.info(f"Metadata file already exists: {metadata_path}")
            return False
        
        # Generate default metadata
        metadata = self._generate_default_metadata(video_path)
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created metadata template: {metadata_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save metadata template: {e}")
            return False
    
    def validate_metadata(self, metadata: VideoMetadata) -> tuple[bool, list[str]]:
        """Validate video metadata.
        
        Args:
            metadata: VideoMetadata to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        if not metadata.title or not metadata.title.strip():
            errors.append("Title is required")
        elif len(metadata.title) > 100:
            errors.append("Title exceeds 100 characters")
        
        if len(metadata.description) > 5000:
            errors.append("Description exceeds 5000 characters")
        
        if len(metadata.tags) > 500:
            errors.append("Too many tags (max 500)")
        
        valid_privacy_statuses = ['public', 'private', 'unlisted']
        if metadata.privacy_status not in valid_privacy_statuses:
            errors.append(f"Invalid privacy status. Must be one of: {valid_privacy_statuses}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
