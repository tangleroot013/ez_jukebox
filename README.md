# ez_jukebox

Local Crostini music automation.

## Commands

- just verify
- just dedup-triage
- just check-integrity
- just verify-shuffle
- just recover

## Shuffle App Launcher

Install the Linux or Crostini application icon and desktop launcher:

```bash
bash scripts/install_shuffle_launcher.sh
```

Find `ez_jukebox Shuffle` in the application menu and pin it to the shelf,
taskbar, or favorites. The first click seeds four random library tracks and
starts MPD playback in the background. Each later click advances to the next
track and replenishes the queue so three tracks remain ready to play.

The launcher uses `mpc` and requires a running user MPD service. Its log is at
`~/.local/share/ez_jukebox/shuffle.log`.

The installer and launcher honor `XDG_CONFIG_HOME` and `XDG_DATA_HOME`. An
optional config file at `~/.config/ez_jukebox/shuffle.conf` can set
`MPD_HOST`, `MPD_PORT`, and `PRELOAD_COUNT`; command-line options override
those values:

```bash
bash scripts/ez_jukebox_shuffle.sh --lookahead 3
```

The launcher also accepts `--host`, `--port`, `--preload`, and `--help`.
`--lookahead` is an alias for `--preload`. When available, `notify-send`
provides click feedback; MPD connection failures are reported instead of
failing silently.

## 🎵 Audio Stability in Crostini

### Problem

Audio stutters during window switches or tab changes due to ChromeOS CPU throttling of the Termina VM.

### Root Cause

Crostini's CrosVM hypervisor blocks real-time scheduling and CPU pinning for security. Kernel-level tweaks (`Nice`, `SCHED_FIFO`, `CPUAffinity`) are ignored.

### Solution

User-space buffering is the only supported fix:

- **MPD**: `buffer_time = 500000` (500ms output buffer), `audio_buffer_size = 16384` (16MB)
- **PipeWire**: `default.clock.quantum = 2048` (~46ms), `max-quantum = 8192` (~185ms)

### Verification

Run `just verify-audio-buffers` and `just stress-test-audio` to confirm stability.

### Monitoring

- `tail -f ~/.local/share/ez_jukebox/audio_health/audio_health_*.log`
- `htop -d 2 -p $(pgrep -d, -f "mpd|pipewire|wireplumber")`
