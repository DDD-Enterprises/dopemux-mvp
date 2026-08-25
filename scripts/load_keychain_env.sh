#!/bin/bash
# Dynamically generates an env file from the macOS keychain
# Uses local fallback values for database passwords and configs if not found in the keychain.
#
# Usage: scripts/load_keychain_env.sh [TARGET_ENV_FILE]
#   TARGET_ENV_FILE defaults to .env.unified for back-compat.
#   If the target file already exists, managed secrets are upserted in place
#   (existing KEY=... lines are replaced; new ones are appended under a
#   "# --- keychain-managed ---" marker) and all other lines are left
#   byte-identical. If the target does not exist, it is created fresh with
#   just the marker + managed lines.
#
# SECRETS entry syntax:
#   ENVVAR                       - keychain lookup: security find-generic-password -s ENVVAR -w
#   ENVVAR:fallback              - same, with a local fallback value if not in keychain
#   ENVVAR@service/account       - keychain lookup: security find-generic-password -s service -a account -w
#   ENVVAR@service/account:fallback - same, with a local fallback value

SECRETS=(
    # API Keys (Expected in Keychain)
    "GEMINI_API_KEY"
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "CHEAPERINFERENCE_API_KEY@cheaperinference/API_KEY"
    "VOYAGE_API_KEY"
    "VOYAGEAI_API_KEY"
    "XAI_API_KEY"
    "TAVILY_API_KEY"
    "CONTEXT7_API_KEY"
    "CONTEXT7_ENDPOINT"

    # Passwords (Keychain or Fallback)
    "POSTGRES_PASSWORD:dopemux_secure_2024"
    "AGE_PASSWORD:dopemux_age_dev_password"
    "AGE_DB_PASSWORD:dopemux_age_dev_password"
    "REDIS_PASSWORD:dopemux_redis_2024"
    "REDIS_UI_PASSWORD:dopemux-redis-ui"
    "MYSQL_ROOT_PASSWORD:dopemux_mysql_root_2024"
    "MYSQL_PASSWORD:leantime_secure_2024"
    "LEAN_SESSION_PASSWORD:dopemux_session_secure_2024"
    "MINIO_ACCESS_KEY:minioadmin"
    "MINIO_SECRET_KEY:minioadmin"

    # Non-sensitive Service Configurations
    "MYSQL_DATABASE:leantime"
    "MYSQL_USER:leantime"
    "LEAN_API_ENABLED:true"
)

ENV_FILE="${1:-.env.unified}"
MARKER="# --- keychain-managed ---"

# Resolve each SECRETS entry into "ENVVAR=value" lines (only for entries that
# actually resolved to a value, from keychain or fallback). Entries that
# resolve to neither are skipped entirely so they never clobber an existing
# working line during upsert.
RESOLVED_KEYS=()
RESOLVED_VALUES=()

for item in "${SECRETS[@]}"; do
    name="${item%%:*}"
    fallback="${item#*:}"

    if [ "$fallback" = "$name" ]; then
        fallback=""
    fi

    case "$name" in
        *@*)
            envvar="${name%%@*}"
            svc_acct="${name#*@}"
            service="${svc_acct%%/*}"
            account="${svc_acct#*/}"
            val=$(security find-generic-password -s "$service" -a "$account" -w 2>/dev/null)
            ;;
        *)
            envvar="$name"
            val=$(security find-generic-password -s "$envvar" -w 2>/dev/null)
            ;;
    esac

    if [ -n "$val" ]; then
        RESOLVED_KEYS[${#RESOLVED_KEYS[@]}]="$envvar"
        RESOLVED_VALUES[${#RESOLVED_VALUES[@]}]="$val"
    elif [ -n "$fallback" ]; then
        RESOLVED_KEYS[${#RESOLVED_KEYS[@]}]="$envvar"
        RESOLVED_VALUES[${#RESOLVED_VALUES[@]}]="$fallback"
    else
        echo "Warning: $envvar not found in keychain and no fallback provided; skipping." >&2
    fi
done

if [ ! -f "$ENV_FILE" ]; then
    {
        echo "# Generated securely from macOS Keychain"
        echo "$MARKER"
        i=0
        while [ "$i" -lt "${#RESOLVED_KEYS[@]}" ]; do
            printf '%s=%s\n' "${RESOLVED_KEYS[$i]}" "${RESOLVED_VALUES[$i]}"
            i=$((i + 1))
        done
    } > "$ENV_FILE"
    echo "Successfully generated $ENV_FILE from keychain."
    exit 0
fi

# Upsert mode: rewrite existing lines in place for managed keys that already
# appear in the file, then append any not-yet-present managed keys under the
# marker (creating the marker at end-of-file if it's missing). All other
# lines are copied through byte-identical.
TMP_FILE=$(mktemp "${TMPDIR:-/tmp}/load_keychain_env.XXXXXX")
trap 'rm -f "$TMP_FILE"' EXIT

is_resolved_key() {
    key="$1"
    i=0
    while [ "$i" -lt "${#RESOLVED_KEYS[@]}" ]; do
        if [ "${RESOLVED_KEYS[$i]}" = "$key" ]; then
            return 0
        fi
        i=$((i + 1))
    done
    return 1
}

value_for_key() {
    key="$1"
    i=0
    while [ "$i" -lt "${#RESOLVED_KEYS[@]}" ]; do
        if [ "${RESOLVED_KEYS[$i]}" = "$key" ]; then
            printf '%s' "${RESOLVED_VALUES[$i]}"
            return 0
        fi
        i=$((i + 1))
    done
    return 1
}

SEEN_MARKER=0
WRITTEN_KEYS=()

while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
        "$MARKER")
            SEEN_MARKER=1
            printf '%s\n' "$line" >> "$TMP_FILE"
            continue
            ;;
    esac

    key="${line%%=*}"
    case "$line" in
        *=*)
            if is_resolved_key "$key"; then
                val=$(value_for_key "$key")
                printf '%s=%s\n' "$key" "$val" >> "$TMP_FILE"
                WRITTEN_KEYS[${#WRITTEN_KEYS[@]}]="$key"
                continue
            fi
            ;;
    esac

    printf '%s\n' "$line" >> "$TMP_FILE"
done < "$ENV_FILE"

if [ "$SEEN_MARKER" -eq 0 ]; then
    printf '%s\n' "$MARKER" >> "$TMP_FILE"
fi

i=0
while [ "$i" -lt "${#RESOLVED_KEYS[@]}" ]; do
    key="${RESOLVED_KEYS[$i]}"
    already_written=0
    j=0
    while [ "$j" -lt "${#WRITTEN_KEYS[@]}" ]; do
        if [ "${WRITTEN_KEYS[$j]}" = "$key" ]; then
            already_written=1
            break
        fi
        j=$((j + 1))
    done
    if [ "$already_written" -eq 0 ]; then
        printf '%s=%s\n' "$key" "${RESOLVED_VALUES[$i]}" >> "$TMP_FILE"
    fi
    i=$((i + 1))
done

cp "$TMP_FILE" "$ENV_FILE"
echo "Successfully upserted keychain-managed secrets into $ENV_FILE."
