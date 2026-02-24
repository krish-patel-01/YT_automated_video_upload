"""YouTube API integration for video uploads."""

import logging
import os
import pickle
from pathlib import Path
from typing import Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


logger = logging.getLogger(__name__)


class YouTubeUploader:
    """Handle YouTube video uploads via the YouTube Data API."""
    
    def __init__(
        self,
        client_secrets_file: str,
        token_file: str,
        scopes: list[str]
    ):
        """Initialize YouTube uploader.
        
        Args:
            client_secrets_file: Path to OAuth2 client secrets JSON file
            token_file: Path to store OAuth2 token
            scopes: List of YouTube API scopes
        """
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self.scopes = scopes
        self.youtube = None
        
    def authenticate(self) -> bool:
        """Authenticate with YouTube API.
        
        Returns:
            True if authentication successful
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing credentials")
            except Exception as e:
                logger.warning(f"Failed to load token file: {e}")
        
        # Refresh or obtain new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed expired credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.client_secrets_file):
                    logger.error(
                        f"Client secrets file not found: {self.client_secrets_file}\n"
                        f"Please download it from Google Cloud Console and place it in the project root."
                    )
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secrets_file,
                        self.scopes
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Obtained new credentials")
                except Exception as e:
                    logger.error(f"Failed to obtain credentials: {e}")
                    return False
            
            # Save credentials for future use
            try:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info(f"Saved credentials to {self.token_file}")
            except Exception as e:
                logger.warning(f"Failed to save credentials: {e}")
        
        try:
            self.youtube = build('youtube', 'v3', credentials=creds)
            logger.info("YouTube API client initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to build YouTube API client: {e}")
            return False
    
    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str,
        tags: list[str],
        category_id: str = "22",
        privacy_status: str = "private",
        made_for_kids: bool = False,
        notify_subscribers: bool = True,
        video_language: str = "en",
        title_description_language: str = "en"
    ) -> Optional[str]:
        """Upload a video to YouTube.
        
        Args:
            file_path: Path to video file
            title: Video title
            description: Video description
            tags: List of video tags
            category_id: YouTube category ID (default: 22 = People & Blogs)
            privacy_status: Privacy status (public, private, unlisted)
            made_for_kids: Whether video is made for kids
            notify_subscribers: Whether to notify subscribers
            video_language: Language of the video audio (default: en)
            title_description_language: Language of title and description (default: en)
            
        Returns:
            Video ID if successful, None otherwise
        """
        if not self.youtube:
            logger.error("YouTube API not authenticated")
            return None
        
        if not os.path.exists(file_path):
            logger.error(f"Video file not found: {file_path}")
            return None
        
        # Prepare video metadata
        body = {
            'snippet': {
                'title': title[:100],  # YouTube max title length
                'description': description[:5000],  # YouTube max description length
                'tags': tags[:500],  # YouTube max tags
                'categoryId': category_id,
                'defaultLanguage': title_description_language,
                'defaultAudioLanguage': video_language
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': made_for_kids
            }
        }
        
        # Set notification preference
        if not notify_subscribers:
            body['status']['publishAt'] = None
        
        # Create media upload
        try:
            media = MediaFileUpload(
                file_path,
                chunksize=1024*1024,  # 1MB chunks
                resumable=True
            )
            
            logger.info(f"Starting upload: {Path(file_path).name}")
            logger.info(f"Title: {title}")
            logger.info(f"Privacy: {privacy_status}")
            
            # Execute upload
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media,
                notifySubscribers=notify_subscribers
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")
            
            video_id = response['id']
            logger.info(f"Upload complete! Video ID: {video_id}")
            logger.info(f"Video URL: https://www.youtube.com/watch?v={video_id}")
            
            return video_id
            
        except HttpError as e:
            logger.error(f"HTTP error during upload: {e}")
            if e.resp.status == 403:
                logger.error("Quota exceeded or insufficient permissions")
            return None
        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
            return None
    
    def get_upload_quota_usage(self) -> Optional[Dict[str, Any]]:
        """Get current quota usage information.
        
        Returns:
            Dictionary with quota information if available
        """
        if not self.youtube:
            logger.error("YouTube API not authenticated")
            return None
        
        try:
            # Note: Direct quota info not available via API
            # This is a placeholder for future implementation
            logger.info("Quota usage information not directly available via API")
            return {"message": "Check Google Cloud Console for quota details"}
        except Exception as e:
            logger.error(f"Failed to get quota information: {e}")
            return None
