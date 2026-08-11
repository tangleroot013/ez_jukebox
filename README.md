# ez_jukebox

Terminal-first music library management + playback for ChromeOS/Crostini.

## Quick start
```
just install         # mpd, mpc, ncmpcpp via apt
just setup           # links config (no-clobber), enables mpd user service
just play            # launches ncmpcpp
just organize
just cleanup --dry-run
just build-library
```

## Layout
- `src/`     - python tooling (dedup, tag cleanup, library builder)
- `scripts/` - shell utilities (lyrics watcher, glue)
- `config/`  - mpd.conf + ncmpcpp config templates
- `bin/jukebox` - single entrypoint dispatcher

## Known TODO
`config/mpd.conf`'s `music_directory` is a placeholder — point it at the
consolidated library once the dedup/organize pass is done. The `~/Music`
symlink currently resolves to ChromeOS Downloads, not the real library.
