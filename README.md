# ECHO NANO ID3 title patch

This patch makes the ECHO NANO's **media-library list** display a track's embedded title when one is present, and use its filename when the title is empty. File Browser continues to show filenames.

The patch targets the official ECHO NANO firmware **V1.7.0** image only. The author installed this exact patched build on an ECHO NANO and confirmed that the library list displayed song titles correctly. The image remains version 1.7.0. This is an independent community patch, not affiliated with FiiO.

## Build your image

Obtain the official `NANOV170.IMG` from [FiiO's ECHO NANO firmware page](https://forum.fiio.com/note/showNoteContent.do?id=202605161533005115232). This repository does not redistribute FiiO's firmware.

Python 3.10 or newer; no third-party packages are needed.

```powershell
python apply_patch.py NANOV170.IMG NANOV170-ID3-TITLE-EXPERIMENTAL.IMG
```

The builder checks the input's SHA-256, firmware marker, duplicate header, and checksum. It refuses to overwrite the output file. Verify the resulting SHA-256 before installing:

```powershell
(Get-FileHash .\NANOV170-ID3-TITLE-EXPERIMENTAL.IMG -Algorithm SHA256).Hash
```

Expected:

```text
9576D6AF3CF0E07A8E1B49A168ECE09B55E4AFA40275C3C1827C103715E9CA61
```

The builder only accepts the exact V1.7.0 source image with SHA-256:

```text
54A45D233A23C3CE142D1DA9C093CC40C46EBA417AA91FE915EE867726F4A116
```

## Install

1. Charge the player and back up its internal storage.
2. Power it off and remove the microSD card.
3. Connect the ECHO NANO in USB storage mode. Copy only the generated `.IMG` to the root of its internal storage. Keep its filename; do not place it on the microSD card.
4. Safely eject the player and restart it. FiiO's documented update procedure starts the automatic upgrade on restart. Do not interrupt the update.
5. After it boots, power off, put the microSD card back, and restart. Refresh/update the media library so the player rebuilds its cached records.
6. Check a song in the media-library list. A track with a title tag should show that title; a track with no title should show its filename.

See the [official update instructions](https://forum.fiio.com/note/showNoteContent.do?id=202605161533005115232). The title is stored in the media-library index, so existing entries need a library rebuild. The patch can affect title-based ordering. Back up files before installing.

## What it changes

The 44-byte patch changes record construction in firmware V1.7.0. It keeps a parsed, nonempty title and copies the filename only if the title is empty. The firmware container layout, version, and date are unchanged; the firmware checksum is recalculated. The original firmware's exact input hash is required, so later releases and other models are rejected.

The builder contains a small hand-authored Thumb patch. `tests/test_patch.py` checks patch bytes, source-image identity, checksum calculation, output hash and non-overwrite behavior. The original full firmware is intentionally excluded; the user supplies their own official copy.

## Recovery and limitations

The normal update process writes both firmware copies. They are not old/new rollback slots: a completed update leaves both copies on the new image. The author's successful flash verifies this image and procedure on one ECHO NANO, but it does not prove recovery from an interrupted update or failed boot. No Nano-specific emergency recovery procedure has been verified. Install at your own risk.

This only changes titles shown in the media-library list. File Browser still shows filenames. The patch does not edit audio files or metadata. Sorting behavior, CUE/favorites edge cases, and other firmware versions have not been exhaustively tested.

## License

The patching tool and patch bytes are MIT-licensed; see [LICENSE](LICENSE). FiiO firmware, names, and trademarks remain their respective owners' property and are not included in this repository.
