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
4. In `Handlebar` type in the Yomitan handlebar, from which you wish to pull data from (e.g. `frequency-harmonic-rank`). You can concatenate multiple handlebars using a `,` (e.g. `single-glossary-jmdict-2025-08-08,single-glossary-デジタル大辞泉`)
5. Optionally tick `Replace` if you wish to replace the current content of the field in every card.
6. Press `Run`.

Changes can be undone with `Edit -> Undo` or with `CTRL + Z`.

## Config

`Tools -> Add-ons -> backfill-anki-yomitan -> Config`

`max_entries`

Default: `4`

Amount of entries to request when `Reading Field` is specified.

`reading_handlebar`

Default: `reading`

Handlebar used to compare against `Reading Field`.

`yomitan_api_ip`

Default: `127.0.0.1`

`yomitan_api_port`

Default: `19633`

## Issues
If you installed the Yomitan API before 07/29/2025, the default port of the API has been changed. You can either reinstall the API (recommended), or change `yomitan_api_port` to `8766` in the config.

The addon has been updated to support the changes to the API in Yomitan 25.7.14.1, previous versions of Yomitan are not supported anymore.

If you're backfilling audio, please be aware that retrieving audio - depending on the audio sources configured in Yomitan - can be quite slow.

## Screenshot
![screenshot](https://github.com/Manhhao/backfill-anki-yomitan/blob/main/screenshot/image.png?raw=true)
