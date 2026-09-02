---
description: "Improve ez_jukebox resource usage while preserving MPD playback continuity and audio integrity"
name: "Optimize Audio Resources"
argument-hint: "Describe the audio, launcher, or background-service behavior to optimize"
agent: "agent"
---

Improve the requested `ez_jukebox` audio behavior for lower CPU use, fewer wakeups, and lower idle resource consumption while preserving reliable playback.

## Repository Context

This is a Bash/Python Linux and Crostini project using MPD and `mpc`, not a Node/TypeScript service. Prefer the existing scripts, `justfile`, MPD configuration, user systemd services, and offline shell tests. Do not introduce a new daemon, database, web service, or external dependency unless the request clearly requires it.

## Workflow

1. Identify the nearest code that directly controls the requested behavior. Inspect only the relevant script, configuration, service, test, and nearby documentation.
2. State one falsifiable hypothesis about the current resource cost or reliability risk and one focused check that could disprove it.
3. Preserve audio integrity: keep gapless playback, appropriate buffering for Crostini scheduling jitter, and documented ReplayGain/resampler behavior. Do not claim bit-perfect output through the CRAS/PulseAudio bridge.
4. Prefer event-driven or blocking operations over polling loops. Reduce scan frequency, process lifetime, subprocess count, and unnecessary notifications where behavior permits.
5. Keep user configuration portable: honor `XDG_CONFIG_HOME` and `XDG_DATA_HOME`; never expose credentials from `MPD_HOST` in logs, notifications, or error output.
6. Make commands safe to retry. Use strict permissions for state and lock files, avoid duplicate queue entries, and preserve existing user changes in unrelated files.
7. Keep installers self-locating and idempotent. Do not auto-commit, reset, or discard repository changes.
8. Add or update a focused offline test when the behavior can be mocked. A stateful `mpc` mock is preferred over a static output stub for queue behavior.
9. Update README or `justfile` only when needed to make the new behavior discoverable and operable.

## Validation

Run the narrowest available checks first, then any relevant broader check:

- `bash -n` on changed shell scripts
- the focused offline test, such as `bash test/verify_suite/test_shuffle.sh`
- `git diff --check`
- `get_errors` for changed files when available
- ShellCheck if installed or in CI

Do not require a live MPD server, D-Bus notification bus, removable media path, or audio device for offline tests. If live validation is unavailable, say exactly what was and was not tested.

## Output

Report briefly:

- the resource cost or reliability issue found
- the files changed and why
- the audio-integrity tradeoff, if any
- validation commands and results
- any remaining live-environment limitation
