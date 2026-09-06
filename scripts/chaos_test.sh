#!/usr/bin/env bash
# ez_jukebox chaos test -- injects real failures into the live stack and
# verifies each piece self-heals per its systemd Restart= policy.
# Not -e: individual checks are expected to fail/succeed independently.
set -uo pipefail

REPO="$HOME/home-data/github_projects/ez_jukebox"
PASS=0; FAIL=0; WARN=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }
warn() { echo "  WARN: $1"; WARN=$((WARN+1)); }
section() { echo; echo "=== $1 ==="; }

wait_for() {
    local timeout=$1; shift
    local waited=0
    while ! "$@" >/dev/null 2>&1; do
        sleep 1
        waited=$((waited+1))
        [ "$waited" -ge "$timeout" ] && return 1
    done
    return 0
}

ALWAYS_ON="ez_jukebox_ui.service ez-jukebox-notify.service ez-jukebox-now-playing-api.service ez-jukebox-watcher.service"

section "Baseline"
for u in $ALWAYS_ON ez-jukebox-import.path; do
    echo "  $u: $(systemctl --user is-active "$u" 2>&1)"
done

section "Test 1: Force Stop actually stops everything"
"$REPO/scripts/ez_jukebox_stop.sh"
sleep 2
[ "$(systemctl --user is-active ez-jukebox-watcher.service 2>&1)" = "inactive" ] \
    && pass "watcher stopped" || fail "watcher still active after Force Stop"
pgrep -f ncmpcpp >/dev/null \
    && fail "ncmpcpp still running after Force Stop" || pass "no lingering ncmpcpp"
mpc status 2>&1 | grep -q '\[playing\]' \
    && fail "mpc still reports playing" || pass "mpc reports not playing"

section "Test 2: watcher respawns after a hard crash (kill -9, not systemctl stop)"
systemctl --user start ez-jukebox-watcher.service
sleep 1
wpid=$(systemctl --user show -p MainPID --value ez-jukebox-watcher.service)
if [ -z "$wpid" ] || [ "$wpid" = "0" ]; then
    fail "could not read watcher PID, skipped crash test"
else
    kill -9 "$wpid" 2>/dev/null || true
    wait_for 5 systemctl --user is-active --quiet ez-jukebox-watcher.service \
        && pass "watcher respawned within 5s of kill -9" \
        || fail "watcher did NOT respawn after kill -9"
fi

section "Test 3: crash-and-recover for the other services"
for u in ez_jukebox_ui.service ez-jukebox-notify.service ez-jukebox-now-playing-api.service; do
    pid=$(systemctl --user show -p MainPID --value "$u" 2>/dev/null)
    if [ -z "$pid" ] || [ "$pid" = "0" ]; then
        warn "$u not running, cannot crash-test"
        continue
    fi
    kill -9 "$pid" 2>/dev/null || true
    wait_for 5 systemctl --user is-active --quiet "$u" \
        && pass "$u respawned after kill -9" \
        || fail "$u did NOT respawn after kill -9"
done

section "Test 4: concurrent launcher race (flock guard)"
for i in 1 2 3 4 5; do "$REPO/scripts/ez_jukebox_shuffle.sh" & done
wait
sleep 1
mpd_count=$(pgrep -c -f 'mpd$' 2>/dev/null || echo 0)
[ "$mpd_count" -le 1 ] \
    && pass "single mpd instance after 5 concurrent launches" \
    || fail "$mpd_count mpd processes running -- flock guard did not hold"

section "Test 5: import.path trigger"
mkdir -p ~/Music-library
touch ~/Music-library/.chaos_test_$$ 2>/dev/null || warn "could not write to ~/Music-library"
sleep 3
echo "  ez-jukebox-import.service last start: $(systemctl --user show -p ExecMainStartTimestamp --value ez-jukebox-import.service 2>&1)"
rm -f ~/Music-library/.chaos_test_$$ 2>/dev/null || true

section "Test 6: idempotent install recipes"
cd "$REPO"
{ just install-desktop && just install-desktop; } >/tmp/chaos_desktop.log 2>&1 \
    && pass "install-desktop runs twice cleanly" \
    || fail "install-desktop errored on repeat -- see /tmp/chaos_desktop.log"
{ just install-service && just install-service; } >/tmp/chaos_service.log 2>&1 \
    && pass "install-service runs twice cleanly" \
    || fail "install-service errored on repeat -- see /tmp/chaos_service.log"

section "Restoring baseline"
systemctl --user daemon-reload
for u in $ALWAYS_ON; do systemctl --user restart "$u" 2>/dev/null || true; done

section "RESULTS"
echo "  PASS: $PASS   FAIL: $FAIL   WARN: $WARN"
[ "$FAIL" -eq 0 ]
