import logging
import os

addon_dir = os.path.dirname(__file__)
log_file_path = os.path.join(addon_dir, "user_files", "addon.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

log = logging.getLogger("backfill-anki-yomitan")
log.setLevel(logging.DEBUG)

handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
if not log.handlers:
    log.addHandler(handler)