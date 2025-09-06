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
    audio_targets = [t for t in targets if "audio" in t[1]]
    other_targets = [t for t in targets if "audio" not in t[1]]

    # split audio from other handlebars
    other_handlebars = [h for t in other_targets for h in t[1]]
    audio_target_handlebars = [h for t in audio_targets for h in t[1]]

    logger.log.info(f"targets: {other_targets}")
    logger.log.info(f"audio targets: {audio_targets}")
    logger.log.info(f"target handlebars: {other_handlebars}")
    logger.log.info(f"audio target handlebars: {audio_target_handlebars}")

    notes = []
    for nid in note_ids:
        note = col.get_note(nid)

        if not expression_field in note:
            continue

        reading = note[reading_field] if reading_field else None
        note_updated = False

        if other_handlebars:
            api_request = yomitan_api.request_handlebar(note[expression_field].strip(), reading, other_handlebars)

            if not api_request:
                logger.log.error(f"api request failed: {note[expression_field]} {reading} {other_handlebars}")
                continue

            api_fields = api_request.get("fields")
            if not api_fields:
                logger.log.error(f"api request empty: {note[expression_field]} {reading} {other_handlebars}")
                continue

            for field, handlebar, should_replace in other_targets:
                if not field in note:
                    logger.log.error(f"{field} does not exist in notetype")
                    continue

                if should_replace or not note[field].strip():
                    data = get_data_from_reading(api_fields, handlebar, reading)
                    if not data:
                        logger.log.info(f"skipping {field} for {note[expression_field]}, api data empty")
                        continue

                    # checks if handlebar data contains filename and writes it to anki if present
                    dictionary_media = api_request.get("dictionaryMedia", [])
                    for file in dictionary_media:
                        filename = file.get("ankiFilename")
                        if filename in data:
                            write_media(file)
                        
                    note[field] = data
                    note_updated = True
                else:
                    logger.log.info(f"skipping {field} for {note[expression_field]}, {field} not empty")

        # we are only requesting audio if necessary (if current is empty OR if replace is true), this fixes requesting audio for each entry unconditionally
        for field, handlebar, should_replace in audio_targets:
            if not field in note:
                logger.log.error(f"{field} does not exist in notetype")
                continue

            if should_replace or not note[field].strip():
                audio_api_request = yomitan_api.request_handlebar(note[expression_field].strip(), reading, audio_target_handlebars)

                if not audio_api_request:
                    logger.log.info(f"skipping {field} for {note[expression_field]}, api data empty")
                    continue

                audio_api_fields = audio_api_request.get("fields")
                if not audio_api_fields:
                    logger.log.error(f"api request failed: {note[expression_field]} {reading} {audio_target_handlebars}")
                    continue
                
                data = get_data_from_reading(audio_api_fields, handlebar, reading)
                if not data:
                    logger.log.info(f"skipping {field} for {note[expression_field]}, api data empty")
                    continue
                
                audio_media = audio_api_request.get("audioMedia", [])
                for file in audio_media:
                    if file.get("ankiFilename") in data:
                        write_media(file)
                        break
                
                note[field] = data
                note_updated = True
            else:
                logger.log.info(f"skipping {field} for {note[expression_field]}, {field} not empty")

        if note_updated:
            notes.append(note)
            
    return OpChangesWithCount(changes=col.update_notes(notes), count=len(notes))

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
        return None
    else:
        return "".join(entries[0].get(h, "") for h in handlebars)
            
def on_success(result):
    m = f"Updated {result.count} cards"
    logger.log.info(m)
    showInfo(m)