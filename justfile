install:
    sudo apt install -y mpd mpc ncmpcpp

setup:
    mkdir -p ~/.config/mpd ~/.ncmpcpp
    cp -n config/mpd.conf ~/.config/mpd/mpd.conf
    cp -n config/ncmpcpp/config ~/.ncmpcpp/config
    systemctl --user enable --now mpd || mpd ~/.config/mpd/mpd.conf

play:
    ncmpcpp

organize:
    python3 src/organize_music.py

cleanup *ARGS:
    python3 src/cleanup_music_library.py {{ARGS}}

build-library:
    python3 src/build_music_library.py
