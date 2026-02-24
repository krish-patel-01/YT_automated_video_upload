"""Main automation script for YouTube video uploads."""

import logging
import os
import shutil
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Set

from youtube_auto_upload_automation.config import Config
from youtube_auto_upload_automation.youtube_uploader import YouTubeUploader
from youtube_auto_upload_automation.metadata_handler import MetadataHandler
from youtube_auto_upload_automation.tag_generator import TagGenerator


# Global flag for graceful shutdown
shutdown_requested = False


def setup_logging(config: Config):
    """Setup logging configuration."""
    log_dir = Path(config.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        config.log_file,
        maxBytes=config.max_log_size_mb * 1024 * 1024,
        backupCount=config.backup_count,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def move_video_file(source_path: str, destination_dir: str) -> bool:
    """Move video file to destination directory."""
    try:
        os.makedirs(destination_dir, exist_ok=True)
        filename = Path(source_path).name
        destination_path = os.path.join(destination_dir, filename)

        counter = 1
        while os.path.exists(destination_path):
            stem = Path(source_path).stem
            ext = Path(source_path).suffix
            destination_path = os.path.join(destination_dir, f"{stem}_{counter}{ext}")
            counter += 1

        shutil.move(source_path, destination_path)
        logging.info(f"Moved file to {destination_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to move file: {e}")
        return False


# ---------------------------------------------------------------------------
# Upload retry tracking
# ---------------------------------------------------------------------------
# Tracks consecutive network-error counts per video filename across polls.
# Resets on success. After MAX_UPLOAD_RETRIES the video is marked Failed.
_upload_failure_counts: Dict[str, int] = {}
MAX_UPLOAD_RETRIES = 3


def _is_transient_error(exc: Exception) -> bool:
    """Return True for errors worth retrying (network blips)."""
    transient_phrases = (
        "eof occurred",
        "connection reset",
        "timed out",
        "unable to find the server",
        "connection aborted",
        "remote end closed",
        "ssl",
        "socket",
        "network",
        "temporarily unavailable",
    )
    return any(p in str(exc).lower() for p in transient_phrases)


def poll_excel(
    config: Config,
    uploader: YouTubeUploader,
    metadata_handler: MetadataHandler,
    tag_generator: TagGenerator,
    logger: logging.Logger,
):
    """Single poll cycle: generate tags then process pending uploads.

    Args:
        config: Configuration instance
        uploader: Authenticated YouTubeUploader
        metadata_handler: MetadataHandler with Excel queue
        tag_generator: TagGenerator for Groq-powered tag generation
        logger: Logger instance
    """
    # ------------------------------------------------------------------ #
    # Step 1 – Auto-generate tags for rows that requested it             #
    # ------------------------------------------------------------------ #
    try:
        generated = metadata_handler.process_tag_generation(tag_generator)
        if generated:
            logger.info(f"Generated tags for {generated} row(s).")
    except Exception as e:
        logger.error(f"Tag generation poll failed: {e}", exc_info=True)

    # ------------------------------------------------------------------ #
    # Step 2 – Upload videos whose 'upload' column is 'yes'             #
    # ------------------------------------------------------------------ #
    try:
        pending = metadata_handler.get_pending_uploads(config.watch_directories)
    except Exception as e:
        logger.error(f"Failed to read pending uploads from Excel: {e}", exc_info=True)
        return

    for video_path, metadata in pending:
        if shutdown_requested:
            break

        vname = Path(video_path).name
        logger.info(f"Processing upload: {video_path}")
        logger.info(f"  Title       : {metadata.title}")
        logger.info(f"  Tags        : {metadata.tags[:5]}{'...' if len(metadata.tags) > 5 else ''}")
        logger.info(f"  Privacy     : {metadata.privacy_status}")

        # Validate metadata
        is_valid, errors = metadata_handler.validate_metadata(metadata)
        if not is_valid:
            logger.error(f"Invalid metadata for '{video_path}': {', '.join(errors)}")
            metadata_handler.mark_as_failed(video_path)
            _upload_failure_counts.pop(vname, None)
            if config.move_after_upload:
                move_video_file(video_path, config.failed_directory)
            continue

        try:
            video_id = uploader.upload_video(
                file_path=video_path,
                title=metadata.title,
                description=metadata.description,
                tags=metadata.tags,
                category_id=metadata.category_id,
                privacy_status=metadata.privacy_status,
                made_for_kids=metadata.made_for_kids,
                notify_subscribers=config.notify_subscribers,
                video_language=config.video_language,
                title_description_language=config.title_description_language,
            )
        except Exception as e:
            if _is_transient_error(e):
                _upload_failure_counts[vname] = _upload_failure_counts.get(vname, 0) + 1
                attempts = _upload_failure_counts[vname]
                if attempts < MAX_UPLOAD_RETRIES:
                    logger.warning(
                        f"Transient network error for '{vname}' "
                        f"(attempt {attempts}/{MAX_UPLOAD_RETRIES}), will retry next poll: {e}"
                    )
                    continue  # don't move/mark-failed yet
                else:
                    logger.error(
                        f"Upload failed after {MAX_UPLOAD_RETRIES} transient errors for '{vname}': {e}"
                    )
            else:
                logger.error(f"Upload exception for '{video_path}': {e}", exc_info=True)
            metadata_handler.mark_as_failed(video_path)
            _upload_failure_counts.pop(vname, None)
            if config.move_after_upload:
                move_video_file(video_path, config.failed_directory)
            continue

        if video_id:
            logger.info(f"Upload successful: https://www.youtube.com/watch?v={video_id}")
            metadata_handler.mark_as_uploaded(video_path)
            _upload_failure_counts.pop(vname, None)
            if config.move_after_upload:
                move_video_file(video_path, config.processed_directory)
        else:
            # uploader returned None without raising — treat as transient
            _upload_failure_counts[vname] = _upload_failure_counts.get(vname, 0) + 1
            attempts = _upload_failure_counts[vname]
            if attempts < MAX_UPLOAD_RETRIES:
                logger.warning(
                    f"Upload returned no video ID for '{vname}' "
                    f"(attempt {attempts}/{MAX_UPLOAD_RETRIES}), will retry next poll."
                )
            else:
                logger.error(
                    f"Upload failed after {MAX_UPLOAD_RETRIES} attempts for '{vname}'. Marking as Failed."
                )
                metadata_handler.mark_as_failed(video_path)
                _upload_failure_counts.pop(vname, None)
                if config.move_after_upload:
                    move_video_file(video_path, config.failed_directory)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logging.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


def main():
    """Main entry point for the automation script."""
    global shutdown_requested

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        config = Config()
        setup_logging(config)
        logger = logging.getLogger(__name__)

        logger.info("=" * 60)
        logger.info("YouTube Auto-Upload Automation Starting")
        logger.info("=" * 60)
        logger.info(f"Excel queue  : {config.excel_file}")
        logger.info(f"Watch dirs   : {config.watch_directories}")
        logger.info(f"Poll interval: {config.check_interval_seconds}s")

        # ------------------------------------------------------------------ #
        # Authenticate with YouTube                                          #
        # ------------------------------------------------------------------ #
        uploader = YouTubeUploader(
            config.client_secrets_file,
            config.token_file,
            config.youtube_scopes,
        )
        logger.info("Authenticating with YouTube...")
        if not uploader.authenticate():
            logger.error("YouTube authentication failed. Exiting.")
            sys.exit(1)
        logger.info("YouTube authentication successful.")

        # ------------------------------------------------------------------ #
        # Initialise MetadataHandler (creates upload_queue.xlsx if missing)  #
        # ------------------------------------------------------------------ #
        metadata_handler = MetadataHandler(
            excel_file=config.excel_file,
            default_description=config.default_description,
            default_tags=config.default_tags,
            default_category_id=config.default_category,
            default_privacy_status=config.default_privacy,
            default_made_for_kids=config.made_for_kids,
        )

        # ------------------------------------------------------------------ #
        # Initialise TagGenerator (Groq)                                     #
        # ------------------------------------------------------------------ #
        tag_generator = TagGenerator(
            api_key=config.groq_api_key,
            model=config.groq_model,
        )
        logger.info(f"Tag generator ready (model: {config.groq_model}).")

        logger.info("Automation is running. Press Ctrl+C to stop.")
        logger.info(
            "Workflow:\n"
            "  1. Drop video files into: " + ", ".join(config.watch_directories) + "\n"
            f"  2. Open '{config.excel_file}' and fill in: video_filename, title, description\n"
            "  3. Set 'generate_tags' = yes  -> tags are auto-generated via Groq\n"
            "  4. Set 'upload' = yes         -> video is uploaded to YouTube\n"
            "  5. The 'status' column is updated automatically."
        )

        # ------------------------------------------------------------------ #
        # Main polling loop                                                  #
        # ------------------------------------------------------------------ #
        poll_ticker = 0
        try:
            while not shutdown_requested:
                time.sleep(1)
                poll_ticker += 1

                if poll_ticker >= config.check_interval_seconds:
                    poll_ticker = 0
                    poll_excel(config, uploader, metadata_handler, tag_generator, logger)

        except KeyboardInterrupt:
            pass

        logger.info("=" * 60)
        logger.info("YouTube Auto-Upload Automation Stopped")
        logger.info("=" * 60)

    except FileNotFoundError as e:
        logging.error(str(e))
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
