import logging
import os

log = logging.getLogger("backfill-anki-yomitan")
log.setLevel(logging.DEBUG)

addon_dir = os.path.dirname(__file__)
log_file_path = os.path.join(addon_dir, "user_files", "backfill-log.log")

def setup_logging():
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    if any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file_path for h in log.handlers):
        return

    handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    
    log.addHandler(handler)
    log.debug("logging started")

def shutdown_logging():
    for handler in log.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == log_file_path:
            log.debug("logging stopped")
            handler.close()
            log.removeHandler(handler)
            break