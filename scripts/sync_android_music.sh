#!/usr/bin/env bash
# sync_android_music.sh – pull music from Android media store
set -euo pipefail

ANDROID_MUSIC="/mnt/chromeos/MyFiles/Android/media/com.android.providers.media.telephony/files/Music"
LOCAL_MUSIC="${HOME}/Music/AndroidSync"

mkdir -p "$LOCAL_MUSIC"
rsync -av --progress "$ANDROID_MUSIC/" "$LOCAL_MUSIC/"
./bin/jukebox build --root "$LOCAL_MUSIC" --execute
echo "[ok] Synced Android music to $LOCAL_MUSIC"
