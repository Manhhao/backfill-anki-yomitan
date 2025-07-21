# backfill-anki-yomitan

This is a basic Anki add-on to backfill fields including media and audio using [Yomitan's API](https://github.com/Kuuuube/yomitan-api).
## Installation
1. Install the Yomitan API like specified in the README.
2. Install the add-on from [AnkiWeb](https://ankiweb.net/shared/info/1184164376)
3. Restart Anki

## Usage
**Create a Backup of your profile/deck before doing any of these steps**
Make sure your Browser is running and the API is working.

**Run on deck**
1. Go to `Tools -> Backfill from Yomitan` in the top bar.
2. Select your deck in the `Deck` dropdown

**Run on select cards**
1. Select Cards you want to backfill in `Browse`
2. Go to `Edit -> Backfill from Yomitan` in the top bar of the card browser.

**General Steps**
1. For `Expression Field` choose the expression field (e.g. `Expression` in Lapis) of your note type, this is the field that will be queried into Yomitan.
2. Optionally choose a `Reading Field` (e.g. ExpressionReading in Lapis) to differentiate expressions using their reading. If left blank, the add-on uses the first result Yomitan returns.
3. For `Field` choose the field to backfilled.
4. In `Handlebar` type in the Yomitan handlebar, from which you wish to pull data from, without brackets (e.g. `frequency-harmonic-rank`).
5. Optionally tick `Replace` if you wish to replace the current content of the field in every card.
6. Press `Run`.

Changes can be undone with `Edit -> Undo` or with `CTRL + Z`.

## Issues
The addon has been updated to support the changes to the API in Yomitan 25.7.14.1, previous versions of Yomitan are not supported anymore.

If you're backfilling audio, please be aware that retrieving audio - depending on the audio sources configured in Yomitan - can be quite slow.

## Screenshot
![screenshot](https://github.com/Manhhao/backfill-anki-yomitan/blob/main/screenshot/image.png?raw=true)
