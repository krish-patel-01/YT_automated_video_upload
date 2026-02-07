"""File system monitoring for new video files."""

import logging
import os
import time
from pathlib import Path
from typing import Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


logger = logging.getLogger(__name__)


class VideoFileHandler(FileSystemEventHandler):
    """Handler for video file system events."""
    
    def __init__(
        self,
        supported_extensions: list[str],
        min_file_size_mb: float,
        on_new_video: Callable[[str], None],
        processed_videos: Set[str]
    ):
        """Initialize the video file handler.
        
        Args:
            supported_extensions: List of supported video file extensions
            min_file_size_mb: Minimum file size in MB to process
            on_new_video: Callback function when new video is detected
            processed_videos: Set of already processed video paths
        """
        super().__init__()
        self.supported_extensions = [ext.lower() for ext in supported_extensions]
        self.min_file_size_bytes = min_file_size_mb * 1024 * 1024
        self.on_new_video = on_new_video
        self.processed_videos = processed_videos
        self._pending_files = {}  # Track files being written
        
    def _is_video_file(self, file_path: str) -> bool:
        """Check if file is a supported video file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is a supported video file
        """
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def _is_file_ready(self, file_path: str) -> bool:
        """Check if file is ready to be processed (not being written).
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is ready to be processed
        """
        try:
            # Check if file exists and is large enough
            if not os.path.exists(file_path):
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size < self.min_file_size_bytes:
                logger.debug(f"File {file_path} is too small ({file_size} bytes)")
                return False
            
            # Check if file size is stable (not being written)
            if file_path in self._pending_files:
                last_size, last_check = self._pending_files[file_path]
                if file_size == last_size:
                    # File size hasn't changed, likely ready
                    del self._pending_files[file_path]
                    return True
                else:
                    # File is still growing
                    self._pending_files[file_path] = (file_size, time.time())
                    return False
            else:
                # First time seeing this file at this size
                self._pending_files[file_path] = (file_size, time.time())
                return False
                
        except (OSError, PermissionError) as e:
            logger.debug(f"Cannot access file {file_path}: {e}")
            return False
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Check if it's a video file
        if not self._is_video_file(file_path):
            return
        
        # Skip if already processed
        if file_path in self.processed_videos:
            logger.debug(f"File {file_path} already processed, skipping")
            return
        
        logger.info(f"New video file detected: {file_path}")
        # Don't process immediately, wait for file to be ready
        self._pending_files[file_path] = (0, time.time())
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Check if it's a video file we're tracking
        if not self._is_video_file(file_path):
            return
        
        # Skip if already processed
        if file_path in self.processed_videos:
            return
        
        # Check if file is ready
        if self._is_file_ready(file_path):
            logger.info(f"Video file ready for processing: {file_path}")
            self.processed_videos.add(file_path)
            self.on_new_video(file_path)


class FileMonitor:
    """Monitor directories for new video files."""
    
    def __init__(
        self,
        watch_directories: list[str],
        supported_extensions: list[str],
        min_file_size_mb: float,
        on_new_video: Callable[[str], None],
        processed_videos: Set[str]
    ):
        """Initialize the file monitor.
        
        Args:
            watch_directories: List of directories to monitor
            supported_extensions: List of supported video file extensions
            min_file_size_mb: Minimum file size in MB to process
            on_new_video: Callback function when new video is detected
            processed_videos: Set of already processed video paths
        """
        self.watch_directories = watch_directories
        self.supported_extensions = supported_extensions
        self.min_file_size_mb = min_file_size_mb
        self.on_new_video = on_new_video
        self.processed_videos = processed_videos
        self.observer = Observer()
        self._validate_directories()
        
    def _validate_directories(self):
        """Validate that watch directories exist."""
        for directory in self.watch_directories:
            if not os.path.exists(directory):
                logger.warning(f"Watch directory does not exist: {directory}")
            elif not os.path.isdir(directory):
                logger.warning(f"Watch path is not a directory: {directory}")
            else:
                logger.info(f"Monitoring directory: {directory}")
    
    def start(self):
        """Start monitoring directories."""
        self.event_handler = VideoFileHandler(
            self.supported_extensions,
            self.min_file_size_mb,
            self.on_new_video,
            self.processed_videos
        )
        
        for directory in self.watch_directories:
            if os.path.exists(directory) and os.path.isdir(directory):
                self.observer.schedule(self.event_handler, directory, recursive=False)
                logger.info(f"Started monitoring: {directory}")
        
        self.observer.start()
        logger.info("File monitoring started")
    
    def check_pending_files(self):
        """Check pending files and process any that are ready.
        
        This is called periodically from the main loop to handle files
        that were detected but didn't trigger enough modification events.
        """
        if not hasattr(self, 'event_handler'):
            return
        
        # Get a copy of pending files to avoid modification during iteration
        pending_files = list(self.event_handler._pending_files.keys())
        
        for file_path in pending_files:
            # Skip if already processed
            if file_path in self.processed_videos:
                if file_path in self.event_handler._pending_files:
                    del self.event_handler._pending_files[file_path]
                continue
            
            # Check if file is ready
            if self.event_handler._is_file_ready(file_path):
                logger.info(f"Video file ready for processing (periodic check): {file_path}")
                self.processed_videos.add(file_path)
                self.on_new_video(file_path)
    
    def stop(self):
        """Stop monitoring directories."""
        self.observer.stop()
        self.observer.join()
        logger.info("File monitoring stopped")
    
    def scan_existing_files(self):
        """Scan for existing video files in watch directories.
        
        Returns:
            List of existing video file paths
        """
        existing_videos = []
        
        for directory in self.watch_directories:
            if not os.path.exists(directory) or not os.path.isdir(directory):
                continue
            
            try:
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    
                    # Skip if not a file
                    if not os.path.isfile(file_path):
                        continue
                    
                    # Check if it's a video file
                    if Path(file_path).suffix.lower() not in self.supported_extensions:
                        continue
                    
                    # Check file size
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size < self.min_file_size_mb * 1024 * 1024:
                            continue
                    except OSError:
                        continue
                    
                    # Skip if already processed
                    if file_path in self.processed_videos:
                        continue
                    
                    existing_videos.append(file_path)
                    logger.info(f"Found existing video: {file_path}")
                    
            except PermissionError as e:
                logger.error(f"Permission denied accessing directory {directory}: {e}")
        
        return existing_videos
