#!/bin/bash
# Dopemux statusline for Claude Code.
#
# Mirrors the operator's zsh PS1 (`%n@%m %1~ %#` → `user@host dir %`), then appends:
#   git branch ±dirty 🌳worktree | model ⚡effort | ctx used% usedK/sizeK
#   | 5h <remaining>% ↺<time-to-reset> · 7d <remaining>% ↺<time-to-reset> | ⏱ session-minutes
#
# Input: the Claude Code statusLine JSON payload on stdin (keys confirmed on
# Claude Code 2.1.272 — see memory note reference_claude_code_statusline_payload).
# Every segment is optional: a missing/null key simply omits its segment.
#
# Constraints:
#   - /bin/bash on macOS is 3.2.57 → no assoc arrays, no ${var,,}, no mapfile.
#   - One jq pass, one value per line, successive `IFS= read -r` (never @tsv+read:
#     tab is IFS-whitespace and empty fields shift every later variable).
#   - Never hardcode the context size: Fable/Opus report 1,000,000, not 200K.
#   - Keep it fast: no network probes; git calls only (≈30 ms in this repo).

input=$(cat)

# Keep the last payload for schema debugging (local, atomic). Disable with
# DOPEMUX_STATUSLINE_CAPTURE=0.
if [ "${DOPEMUX_STATUSLINE_CAPTURE:-1}" != "0" ] && [ -d "$HOME/.claude" ]; then
    cap="$HOME/.claude/.statusline-last-payload.json"
    printf '%s' "$input" > "$cap.tmp.$$" 2>/dev/null && mv -f "$cap.tmp.$$" "$cap" 2>/dev/null
fi

C_RST=$'\033[0m'; C_DIM=$'\033[2m'; C_BOLD=$'\033[1m'
C_GRN=$'\033[32m'; C_YEL=$'\033[33m'; C_RED=$'\033[31m'
C_CYN=$'\033[36m'; C_MAG=$'\033[35m'; C_GRY=$'\033[90m'
SEP=" ${C_DIM}|${C_RST} "

# ── payload extraction (one jq pass; -1 = numeric field absent) ───────────────
cur_dir="" model_name="" effort="" ctx_pct=-1 ctx_size=-1
cu_in=-1 cu_cc=-1 cu_cr=-1 ctx_total_in=-1
fh_used=-1 fh_reset=-1 sd_used=-1 sd_reset=-1 dur_ms=-1 over200k=false

if command -v jq >/dev/null 2>&1; then
    jq_out=$(printf '%s' "$input" | jq -r '
        def num(f): try (if (f|type) == "number" then (f|floor) else -1 end) catch -1;
        [
          (.workspace.current_dir // .cwd // ""),
          (.model.display_name // .model.id // "Claude"),
          (.effort.level // ""),
          num(.context_window.used_percentage),
          num(.context_window.context_window_size),
          num(.context_window.current_usage.input_tokens),
          num(.context_window.current_usage.cache_creation_input_tokens),
          num(.context_window.current_usage.cache_read_input_tokens),
          num(.context_window.total_input_tokens),
          num(.rate_limits.five_hour.used_percentage),
          num(.rate_limits.five_hour.resets_at),
          num(.rate_limits.seven_day.used_percentage),
          num(.rate_limits.seven_day.resets_at),
          num(.cost.total_duration_ms),
          (.exceeds_200k_tokens // false)
        ] | .[] | tostring' 2>/dev/null)
    if [ -n "$jq_out" ]; then
        {
            IFS= read -r cur_dir
            IFS= read -r model_name
            IFS= read -r effort
            IFS= read -r ctx_pct
            IFS= read -r ctx_size
            IFS= read -r cu_in
            IFS= read -r cu_cc
            IFS= read -r cu_cr
            IFS= read -r ctx_total_in
            IFS= read -r fh_used
            IFS= read -r fh_reset
            IFS= read -r sd_used
            IFS= read -r sd_reset
            IFS= read -r dur_ms
            IFS= read -r over200k
        } <<EOF
$jq_out
EOF
    fi
fi
[ -z "$cur_dir" ] && cur_dir="$PWD"
[ -z "$model_name" ] && model_name="Claude"

# ── helpers ───────────────────────────────────────────────────────────────────
is_int() { case "$1" in ''|*[!0-9-]*) return 1 ;; *) return 0 ;; esac; }
for v in ctx_pct ctx_size cu_in cu_cc cu_cr ctx_total_in fh_used fh_reset sd_used sd_reset dur_ms; do
    eval "is_int \"\$$v\" || $v=-1"
done

fmt_tok() {  # tokens → 1M / 200K / 123K
    local n=$1
    if [ "$n" -ge 1000000 ] && [ $((n % 1000000)) -eq 0 ]; then printf '%dM' $((n / 1000000))
    else printf '%dK' $((n / 1000)); fi
}
fmt_countdown() {  # seconds → 2d04h / 1h23m / 47m / now
    local s=$1 d h m
    [ "$s" -le 0 ] && { printf 'now'; return; }
    d=$((s / 86400)); h=$((s % 86400 / 3600)); m=$((s % 3600 / 60))
    if   [ "$d" -gt 0 ]; then printf '%dd%02dh' "$d" "$h"
    elif [ "$h" -gt 0 ]; then printf '%dh%02dm' "$h" "$m"
    else printf '%dm' "$m"; fi
}
color_used() {  # used% → colour (green <60, yellow <80, red)
    if   [ "$1" -lt 60 ]; then printf '%s' "$C_GRN"
    elif [ "$1" -lt 80 ]; then printf '%s' "$C_YEL"
    else printf '%s' "$C_RED"; fi
}
color_remaining() {  # remaining% → colour (green ≥50, yellow ≥20, red)
    if   [ "$1" -ge 50 ]; then printf '%s' "$C_GRN"
    elif [ "$1" -ge 20 ]; then printf '%s' "$C_YEL"
    else printf '%s' "$C_RED"; fi
}

# ── 1. PS1 mirror: %n@%m %1~ %# ───────────────────────────────────────────────
ps_user=${USER:-$(id -un 2>/dev/null)}
ps_host=$(hostname -s 2>/dev/null); ps_host=${ps_host%%.*}
if [ "$cur_dir" = "$HOME" ]; then ps_dir="~"; else ps_dir=$(basename "$cur_dir"); fi
if [ "$(id -u 2>/dev/null)" = "0" ]; then ps_mark="#"; else ps_mark="%"; fi
line="${C_GRN}${ps_user}@${ps_host}${C_RST} ${C_BOLD}${C_CYN}${ps_dir}${C_RST} ${C_DIM}${ps_mark}${C_RST}"

# ── 2. git: branch ±dirty 🌳worktree ──────────────────────────────────────────
if git -C "$cur_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    branch=$(git -C "$cur_dir" symbolic-ref --short -q HEAD 2>/dev/null) \
        || branch=$(git -C "$cur_dir" rev-parse --short HEAD 2>/dev/null)
    dirty=$(git -C "$cur_dir" status --porcelain -uno 2>/dev/null | wc -l | tr -d ' ')
    git_dir=$(git -C "$cur_dir" rev-parse --absolute-git-dir 2>/dev/null)
    common_dir=$(git -C "$cur_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
    seg=" ${C_YEL}${branch}${C_RST}"
    [ "${dirty:-0}" -gt 0 ] && seg="$seg ${C_MAG}±${dirty}${C_RST}"
    if [ -n "${DOPEMUX_INSTANCE_ID:-}" ]; then seg="$seg 🌳${DOPEMUX_INSTANCE_ID}"
    elif [ -n "$git_dir" ] && [ -n "$common_dir" ] && [ "$git_dir" != "$common_dir" ]; then seg="$seg 🌳"; fi
    line="$line$seg"
fi

# ── 3. model ⚡effort ──────────────────────────────────────────────────────────
seg="${C_GRY}${model_name}${C_RST}"
[ -n "$effort" ] && seg="$seg ${C_DIM}⚡${effort}${C_RST}"
line="$line$SEP$seg"

# ── 4. context usage ──────────────────────────────────────────────────────────
ctx_used=-1
if [ "$cu_in" -ge 0 ] || [ "$cu_cc" -ge 0 ] || [ "$cu_cr" -ge 0 ]; then
    ctx_used=0
    [ "$cu_in" -ge 0 ] && ctx_used=$((ctx_used + cu_in))
    [ "$cu_cc" -ge 0 ] && ctx_used=$((ctx_used + cu_cc))
    [ "$cu_cr" -ge 0 ] && ctx_used=$((ctx_used + cu_cr))
elif [ "$ctx_total_in" -ge 0 ]; then
    ctx_used=$ctx_total_in
elif [ "$ctx_pct" -ge 0 ] && [ "$ctx_size" -gt 0 ]; then
    ctx_used=$((ctx_pct * ctx_size / 100))
fi
if [ "$ctx_pct" -lt 0 ] && [ "$ctx_used" -ge 0 ] && [ "$ctx_size" -gt 0 ]; then
    ctx_pct=$((ctx_used * 100 / ctx_size))
fi
if [ "$ctx_pct" -ge 0 ]; then
    seg="$(color_used "$ctx_pct")ctx ${ctx_pct}%"
    if [ "$ctx_used" -ge 0 ] && [ "$ctx_size" -gt 0 ]; then
        seg="$seg $(fmt_tok "$ctx_used")/$(fmt_tok "$ctx_size")"
    fi
    seg="$seg${C_RST}"
    [ "$over200k" = "true" ] && seg="$seg ${C_RED}⚠️>200K${C_RST}"
    line="$line$SEP$seg"
fi

# ── 5. rate limits: 5h remaining% ↺reset · 7d remaining% ──────────────────────
now=$(date +%s)
seg=""
if [ "$fh_used" -ge 0 ]; then
    rem=$((100 - fh_used)); [ "$rem" -lt 0 ] && rem=0
    seg="$(color_remaining "$rem")5h ${rem}%${C_RST}"
    if [ "$fh_reset" -gt 0 ]; then
        [ "$fh_reset" -gt 100000000000 ] && fh_reset=$((fh_reset / 1000))  # ms → s
        seg="$seg ${C_DIM}↺$(fmt_countdown $((fh_reset - now)))${C_RST}"
    fi
fi
if [ "$sd_used" -ge 0 ]; then
    rem=$((100 - sd_used)); [ "$rem" -lt 0 ] && rem=0
    [ -n "$seg" ] && seg="$seg ${C_DIM}·${C_RST} "
    seg="$seg$(color_remaining "$rem")7d ${rem}%${C_RST}"
    if [ "$sd_reset" -gt 0 ]; then
        [ "$sd_reset" -gt 100000000000 ] && sd_reset=$((sd_reset / 1000))  # ms → s
        seg="$seg ${C_DIM}↺$(fmt_countdown $((sd_reset - now)))${C_RST}"
    fi
fi
[ -n "$seg" ] && line="$line$SEP$seg"

# ── 6. session timer (ADHD 25-min checkpoints) ────────────────────────────────
if [ "$dur_ms" -ge 0 ]; then
    mins=$((dur_ms / 60000))
    if   [ "$mins" -lt 25 ]; then seg="${C_GRN}⏱ ${mins}m${C_RST}"
    elif [ "$mins" -lt 50 ]; then seg="${C_YEL}⏱ ${mins}m${C_RST}"
    else seg="${C_RED}⏱ ${mins}m ☕${C_RST}"; fi
    line="$line$SEP$seg"
fi

printf '%s\n' "$line"
