# NFL FIDOS Real Media-Tool Smoke

Run `python scripts/media_tool_smoke.py` in a validation environment. The rehearsal creates a one-second synthetic MP4 in a temporary directory, probes it with FFprobe, transcodes it, creates a thumbnail, and segments it with FFmpeg. All temporary files are removed when the command exits.

`blocked` means the required binaries are not discoverable; it is not permission to install or enable production media processing. The rehearsal never reads managed media, writes production storage, or changes the Stage 0 control gate.
