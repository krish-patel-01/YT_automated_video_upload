"""Main automation script for YouTube video uploads."""

import logging
import os
import shutil
import signal
import sys
import time
from pathlib import Path
from typing import Set

from youtube_auto_upload_automation.config import Config
from youtube_auto_upload_automation.file_monitor import FileMonitor
from youtube_auto_upload_automation.youtube_uploader import YouTubeUploader
from youtube_auto_upload_automation.metadata_handler import MetadataHandler


# Global flag for graceful shutdown
shutdown_requested = False


def setup_logging(config: Config):
    """Setup logging configuration.
    
    Args:
        config: Configuration instance
    """
    log_dir = Path(config.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # File handler with rotation
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        config.log_file,
        maxBytes=config.max_log_size_mb * 1024 * 1024,
        backupCount=config.backup_count
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce verbosity of third-party libraries
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('watchdog').setLevel(logging.WARNING)


def load_processed_videos(config: Config) -> Set[str]:
    """Load set of already processed video paths.
    
    Args:
        config: Configuration instance
        
    Returns:
        Set of processed video file paths
    """
    processed_videos = set()
    
    if not config.track_processed_videos:
        return processed_videos
    
    if os.path.exists(config.processed_videos_file):
        try:
            with open(config.processed_videos_file, 'r', encoding='utf-8') as f:
                for line in f:
                    path = line.strip()
                    if path:
                        processed_videos.add(path)
            logging.info(f"Loaded {len(processed_videos)} processed videos")
        except Exception as e:
            logging.error(f"Failed to load processed videos: {e}")
    
    return processed_videos


def save_processed_video(config: Config, video_path: str):
    """Save a processed video path to tracking file.
    
    Args:
        config: Configuration instance
        video_path: Path to processed video
    """
    if not config.track_processed_videos:
        return
    
    try:
        with open(config.processed_videos_file, 'a', encoding='utf-8') as f:
            f.write(f"{video_path}\n")
    except Exception as e:
        logging.error(f"Failed to save processed video: {e}")


def move_video_file(source_path: str, destination_dir: str) -> bool:
    """Move video file to destination directory.
    
    Args:
        source_path: Source file path
        destination_dir: Destination directory path
        
    Returns:
        True if move successful
    """
    try:
        # Create destination directory if it doesn't exist
        os.makedirs(destination_dir, exist_ok=True)
        
        # Generate destination path
        filename = Path(source_path).name
        destination_path = os.path.join(destination_dir, filename)
        
        # Handle filename conflicts
        counter = 1
        while os.path.exists(destination_path):
            stem = Path(source_path).stem
            ext = Path(source_path).suffix
            filename = f"{stem}_{counter}{ext}"
            destination_path = os.path.join(destination_dir, filename)
            counter += 1
        
        # Move file
        shutil.move(source_path, destination_path)
        logging.info(f"Moved file to {destination_path}")
        
        # Also move metadata file if it exists
        metadata_path = source_path.replace(Path(source_path).suffix, '_metadata.json')
        if os.path.exists(metadata_path):
            metadata_dest = destination_path.replace(Path(destination_path).suffix, '_metadata.json')
            try:
                shutil.move(metadata_path, metadata_dest)
                logging.info(f"Moved metadata to {metadata_dest}")
            except Exception as e:
                logging.warning(f"Failed to move metadata file: {e}")
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to move file: {e}")
        return False


def process_video(
    video_path: str,
    config: Config,
    uploader: YouTubeUploader,
    metadata_handler: MetadataHandler,
    processed_videos: Set[str]
):
    """Process and upload a video file.
    
    Args:
        video_path: Path to video file
        config: Configuration instance
        uploader: YouTubeUploader instance
        metadata_handler: MetadataHandler instance
        processed_videos: Set of processed video paths
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Processing video: {video_path}")
    
    try:
        # Load metadata
        metadata = metadata_handler.load_metadata(video_path)
        
        # Validate metadata
        is_valid, errors = metadata_handler.validate_metadata(metadata)
        if not is_valid:
            logger.error(f"Invalid metadata: {', '.join(errors)}")
            if config.move_after_upload:
                move_video_file(video_path, config.failed_directory)
            return
        
        # Upload video
        video_id = uploader.upload_video(
            file_path=video_path,
            title=metadata.title,
            description=metadata.description,
            tags=metadata.tags,
            category_id=metadata.category_id,
            privacy_status=metadata.privacy_status,
            made_for_kids=metadata.made_for_kids,
            notify_subscribers=config.notify_subscribers
        )
        
        if video_id:
            logger.info(f"Successfully uploaded: {video_path}")
            logger.info(f"Video URL: https://www.youtube.com/watch?v={video_id}")
            
            # Track processed video
            save_processed_video(config, video_path)
            
            # Move file if configured
            if config.move_after_upload:
                move_video_file(video_path, config.processed_directory)
        else:
            logger.error(f"Failed to upload: {video_path}")
            if config.move_after_upload:
                move_video_file(video_path, config.failed_directory)
    
    except Exception as e:
        logger.error(f"Error processing video {video_path}: {e}", exc_info=True)
        if config.move_after_upload:
            move_video_file(video_path, config.failed_directory)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    global shutdown_requested
    logging.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


def main():
    """Main entry point for the automation script."""
    global shutdown_requested
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load configuration
        config = Config()
        
        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)
        
        logger.info("="*60)
        logger.info("YouTube Auto-Upload Automation Starting")
        logger.info("="*60)
        
        # Initialize components
        uploader = YouTubeUploader(
            config.client_secrets_file,
            config.token_file,
            config.youtube_scopes
        )
        
        # Authenticate with YouTube
        logger.info("Authenticating with YouTube...")
        if not uploader.authenticate():
            logger.error("Failed to authenticate with YouTube API")
            logger.error("Please ensure client_secrets.json is configured correctly")
            sys.exit(1)
        
        logger.info("Successfully authenticated with YouTube")
        
        # Initialize metadata handler
        metadata_handler = MetadataHandler(
            config.metadata_file_suffix,
            config.default_title_template,
            config.default_description,
            config.default_tags
        )
        
        # Load processed videos
        processed_videos = load_processed_videos(config)
        
        # Process existing files first
        logger.info("Scanning for existing video files...")
        monitor = FileMonitor(
            config.watch_directories,
            config.supported_extensions,
            config.min_file_size_mb,
            lambda path: process_video(path, config, uploader, metadata_handler, processed_videos),
            processed_videos
        )
        
        existing_videos = monitor.scan_existing_files()
        if existing_videos:
            logger.info(f"Found {len(existing_videos)} existing video(s) to process")
            for video_path in existing_videos:
                if shutdown_requested:
                    break
                process_video(video_path, config, uploader, metadata_handler, processed_videos)
        else:
            logger.info("No existing videos found")
        
        # Start monitoring for new files
        logger.info("Starting directory monitoring...")
        monitor.start()
        
        logger.info("Automation is running. Press Ctrl+C to stop.")
        
        # Keep running until shutdown requested
        check_counter = 0
        try:
            while not shutdown_requested:
                time.sleep(1)
                check_counter += 1
                
                # Check pending files every 5 seconds
                if check_counter >= 5:
                    monitor.check_pending_files()
                    check_counter = 0
        except KeyboardInterrupt:
            pass
        
        # Cleanup
        logger.info("Stopping file monitoring...")
        monitor.stop()
        
        logger.info("="*60)
        logger.info("YouTube Auto-Upload Automation Stopped")
        logger.info("="*60)
        
    except FileNotFoundError as e:
        logging.error(str(e))
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
