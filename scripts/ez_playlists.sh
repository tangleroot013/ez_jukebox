#!/usr/bin/env bash
# ez_playlists.sh - Bidirectional MPD playlist sync with Git repo

MPD_PLAYLIST_DIR="$HOME/.config/mpd/playlists"
REPO_PLAYLIST_DIR="config/playlists"

mkdir -p "$MPD_PLAYLIST_DIR" "$REPO_PLAYLIST_DIR"

case "$1" in
    export)
        echo "[ez_jukebox] Exporting MPD playlists to repository..."
        rsync -av --delete "$MPD_PLAYLIST_DIR/" "$REPO_PLAYLIST_DIR/"
        echo "[ok] Playlists exported to '$REPO_PLAYLIST_DIR/'. Ready to commit."
        ;;
    import)
        echo "[ez_jukebox] Restoring playlists from repository to MPD..."
        rsync -av "$REPO_PLAYLIST_DIR/" "$MPD_PLAYLIST_DIR/"
        mpc update
        echo "[ok] Playlists restored to MPD."
        ;;
    *)
        echo "Usage: $0 {export|import}"
        exit 1
        ;;
esac
