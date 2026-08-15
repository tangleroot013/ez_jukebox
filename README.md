# ez_jukebox

Local Crostini music automation.

## Commands
- just verify
- just dedup-triage
- just check-integrity
- just recover

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
