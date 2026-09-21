#!/bin/zsh
set -e
cd "$(dirname "$0")"
echo "HYPE FORM / Visual FX Lab v28.2.35 — Mac Fast Export"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required."
  read "?Press Return to close..."
  exit 1
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo ""
  echo "FFmpeg was not found."
  if command -v brew >/dev/null 2>&1; then
    echo "Install with: brew install ffmpeg"
  else
    echo "Install Homebrew first, then run: brew install ffmpeg"
  fi
  echo ""
  echo "Browser Export still works without FFmpeg."
  read "?Press Return to close..."
  exit 1
fi
python3 native_export_helper.py &
HELPER_PID=$!
trap 'kill $HELPER_PID 2>/dev/null || true' EXIT INT TERM
sleep 1
open "http://127.0.0.1:48735/"
echo ""
echo "Native helper is running. Keep this window open while using HYPE FORM."
echo "Exports are saved to: ~/Downloads/HYPE_FORM_Exports/"
wait $HELPER_PID
