import base64
from aqt import mw
from aqt.operations import OpChangesWithCount
from aqt.utils import showInfo
from aqt.qt import *
from . import logger
from . import yomitan_api  

# https://github.com/wikidattica/reversoanki/pull/1/commits/62f0c9145a5ef7b2bde1dc6dfd5f23a53daac4d0
# targets is a list of tuples in the format (field, handlebar, should_replace)
def backfill_notes(col, note_ids, expression_field, reading_field, targets):
    logger.log.info(targets)
    notes = []
    for nid in note_ids:
        note = col.get_note(nid)
        if not expression_field in note:
            continue
        expression = note[expression_field].strip()
        
        targets_to_update = filter_targets(targets, note, expression)
        if not targets_to_update:
            logger.log.info(f"skipping {expression}, nothing to update")
            continue

        handlebars_to_request = [h for t in targets_to_update for h in t[1]]

        reading = note[reading_field] if reading_field else None
        api_request = yomitan_api.request_handlebar(expression, reading, handlebars_to_request)
        if not api_request:
            logger.log.error(f"api request failed: {expression} {reading} {handlebars_to_request}")
            continue

        api_fields = api_request.get("fields")
        if not api_fields:
            logger.log.error(f"api request invalid: {expression} {reading} {handlebars_to_request}")
            continue

        note_updated = False
        for field, handlebar in targets_to_update:
            data = get_data_from_reading(api_fields, handlebar, reading)
            if not data:
                logger.log.error(f"skipping {field} for {expression} {reading}, invalid api data")
                continue

            # check if handlebar data contains filename and write to anki if present
            dictionary_media = api_request.get("dictionaryMedia", [])
            for file in dictionary_media:
                filename = file.get("ankiFilename")
                if filename in data:
                    write_media(file)
                            
            audio_media = api_request.get("audioMedia", [])
            for file in audio_media:
                filename = file.get("ankiFilename")
                # if audio handlebar is requested, handlebar data contains a single filename
                if filename in data:
                    write_media(file)
                    break
                    
            note[field] = data
            note_updated = True

        if note_updated:
            notes.append(note)
            
    return OpChangesWithCount(changes=col.update_notes(notes), count=len(notes))

def filter_targets(targets, note, expression):
    result = []
    for field, handlebar, should_replace in targets:
        if not field in note:
            logger.log.error(f"{field} does not exist in notetype")
            continue
            
        if should_replace or not note[field].strip():
            result.append((field, handlebar))
        else:
            logger.log.info(f"skipping {field} for {expression}, current {field} not empty")

def write_media(file):
    try:
        content = file.get("content")
        filename = file.get("ankiFilename")
        anki_media_dir = mw.col.media.dir()
        decoded = base64.b64decode(content)

        target_path = os.path.join(anki_media_dir, filename)

        with open(target_path, "wb") as f:
            f.write(decoded)  

        return True
    except Exception:
        return False

def get_user_files_dir():
    addon_dir = os.path.dirname(__file__)
    user_files_dir = os.path.join(addon_dir, "user_files")

    if not os.path.isdir(user_files_dir):
        os.makedirs(user_files_dir, exist_ok=True)
    
    return user_files_dir

def open_user_files_folder():
    QDesktopServices.openUrl(QUrl.fromLocalFile(get_user_files_dir()))

def read_user_files_folder():
    json_files = [
        f for f in os.listdir(get_user_files_dir()) 
        if f.lower().endswith('.json')
    ]
    return sorted(json_files)

def get_data_from_reading(entries, handlebars, reading):
    if reading:
        for entry in entries:
            if entry.get(yomitan_api.reading_handlebar) == reading:
                return "".join(entry.get(h, "") for h in handlebars)
            else:
                logger.log.info(f"{reading} does not match {yomitan_api.reading_handlebar}")
        return None
    else:
        return "".join(entries[0].get(h, "") for h in handlebars)
            
def on_success(result):
    m = f"Updated {result.count} cards"
    logger.log.info(m)
    showInfo(m)