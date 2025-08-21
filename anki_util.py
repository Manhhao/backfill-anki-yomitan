import base64
from aqt import mw
from aqt.operations import OpChangesWithCount
from aqt.utils import showInfo
from aqt.qt import *
from . import yomitan_api  

# https://github.com/wikidattica/reversoanki/pull/1/commits/62f0c9145a5ef7b2bde1dc6dfd5f23a53daac4d0
def backfill_notes(col, note_ids, expression_field, reading_field, field, handlebars, should_replace):
    notes = []
    for nid in note_ids:
        note = col.get_note(nid)
        if not expression_field in note or not field in note:
            continue

        current = note[field].strip()
        if should_replace or not current:
            reading = note[reading_field] if reading_field else None
            api_request = yomitan_api.request_handlebar(note[expression_field].strip(), reading, handlebars)
            if not api_request:
                continue

            fields = api_request.get("fields")
            if not fields:
                continue

            data = get_data_from_reading(fields, handlebars, reading)
            if not data:
                continue

            # checks if handlebar data contains filename and writes it to anki if present
            dictionary_media = api_request.get("dictionaryMedia", [])
            for file in dictionary_media:
                filename = file.get("ankiFilename")
                if filename in data:
                    write_media(file)
                        
            audio_media = api_request.get("audioMedia", [])
            for file in audio_media:
                filename = file.get("ankiFilename")
                # if audio handlebar is requested, handlebar data contains the relevant audio filename, write only that file
                if filename in data:
                    write_media(file)
                    break

            note[field] = data
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

def get_data_from_reading(entries, handlebars, reading):
    if reading:
        for entry in entries:
            if entry.get(yomitan_api.reading_handlebar) == reading:
                return "".join(entry.get(h, "") for h in handlebars)
        return None
    else:
        return "".join(entries[0].get(h, "") for h in handlebars)
            
def on_success(result):
    mw.col.reset()
    showInfo(f"Updated {result.count} cards")