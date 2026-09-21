#!/bin/zsh
set -u
SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR" || exit 1

clear
printf '%s\n' 'HYPE FORM / Visual FX Lab — Mac Fast Export'
printf '%s\n' '------------------------------------------------'

if command -v python3 >/dev/null 2>&1; then
  PYTHON="$(command -v python3)"
elif [[ -x /opt/homebrew/bin/python3 ]]; then
  PYTHON="/opt/homebrew/bin/python3"
elif [[ -x /usr/local/bin/python3 ]]; then
  PYTHON="/usr/local/bin/python3"
else
  printf '\nPython 3 が見つかりません。\n'
  printf 'Homebrew がある場合: brew install python\n\n'
  read '?Enterで終了…'
  exit 1
fi

if command -v ffmpeg >/dev/null 2>&1; then
  export FFMPEG_PATH="$(command -v ffmpeg)"
elif [[ -x /opt/homebrew/bin/ffmpeg ]]; then
  export FFMPEG_PATH="/opt/homebrew/bin/ffmpeg"
elif [[ -x /usr/local/bin/ffmpeg ]]; then
  export FFMPEG_PATH="/usr/local/bin/ffmpeg"
else
  printf '\nFFmpeg が見つかりません。Mac Fast ExportにはFFmpegが必要です。\n'
  if command -v brew >/dev/null 2>&1; then
    printf 'インストールコマンド: brew install ffmpeg\n'
  else
    printf 'Homebrewを導入後、brew install ffmpeg を実行してください。\n'
  fi
  printf '\nブラウザ版ExportはFFmpegなしでも引き続き使用できます。\n\n'
  read '?Enterで終了…'
  exit 1
fi

printf 'Python: %s\n' "$PYTHON"
printf 'FFmpeg: %s\n\n' "$FFMPEG_PATH"
exec "$PYTHON" "$SCRIPT_DIR/mac_fast_export/native_export_helper.py"