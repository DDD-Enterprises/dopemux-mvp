#!/bin/bash
# Proof bundle script with plan and scope enforcement

set -e

# Default settings
REQUIRE_PLAN=true
ALLOW_DIRTY=false
ALLOW_FILES=""
TP_ID="TP-WORKDIR-GATE-0001"
OUTPUT_DIR="proof/${TP_ID}"

# Parse arguments first
COMMANDS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --tp)
            shift
            TP_ID="$1"
            OUTPUT_DIR="proof/${TP_ID}"
            shift
            ;;
        --no-plan)
            REQUIRE_PLAN=false
            shift
            ;;
        --allow-dirty)
            ALLOW_DIRTY=true
            shift
            ;;
        --allow-files)
            shift
            ALLOW_FILES="$1"
            shift
            ;;
        --cmd)
            shift
            COMMANDS+=("$1")
            shift
            ;;
        --*)
            echo "Unknown option: $1"
            exit 1
            ;;
        *)
            break
            ;;
    esac
done

# Clean-start gate: ensure repo is clean unless explicitly allowed
if [ "${ALLOW_DIRTY}" = false ]; then
    if [ -n "$(git status --porcelain)" ]; then
        echo "❌ Clean-start gate failed: repository has uncommitted changes"
        echo "Run 'git status' to see changes, or use --allow-dirty to bypass"
        exit 2
    fi
fi

# Plan gate: ensure plan exists unless explicitly bypassed
if [ "${REQUIRE_PLAN}" = true ]; then
    if [ ! -f "proof/PLAN.md" ]; then
        echo "❌ Plan gate failed: proof/PLAN.md not found"
        echo "A signed/vetted PLAN.md is required before generating a proof bundle."
        echo "Create a plan file first, or use --no-plan to bypass if strictly necessary."
        exit 3
    fi
fi

mkdir -p "${OUTPUT_DIR}"

echo "=== Proof Bundle ${TP_ID} ===" > "${OUTPUT_DIR}/proof.txt"
echo "Configuration:" >> "${OUTPUT_DIR}/proof.txt"
echo "  Require Plan: ${REQUIRE_PLAN}" >> "${OUTPUT_DIR}/proof.txt"
echo "  Allow Dirty: ${ALLOW_DIRTY}" >> "${OUTPUT_DIR}/proof.txt"
echo "  Allow Files: ${ALLOW_FILES}" >> "${OUTPUT_DIR}/proof.txt"
echo "" >> "${OUTPUT_DIR}/proof.txt"
echo "Commands executed:" >> "${OUTPUT_DIR}/proof.txt"

# Run each command and capture output
for CMD in "${COMMANDS[@]}"; do
    echo "" >> "${OUTPUT_DIR}/proof.txt"
    echo "Command: ${CMD}" >> "${OUTPUT_DIR}/proof.txt"
    
    # Execute command and capture output verbatim
    OUTPUT_FILE="${OUTPUT_DIR}/$(echo "${CMD}" | tr -s '[:space:]' '_' | sed 's/[^a-zA-Z0-9_]//g').txt"
    eval "${CMD}" > "${OUTPUT_FILE}" 2>&1
    EXIT_CODE=$?
    
    echo "Output:" >> "${OUTPUT_DIR}/proof.txt"
    cat "${OUTPUT_FILE}" >> "${OUTPUT_DIR}/proof.txt"
    echo "" >> "${OUTPUT_DIR}/proof.txt"
    echo "[exit=${EXIT_CODE}]" >> "${OUTPUT_DIR}/proof.txt"
    
    if [ ${EXIT_CODE} -eq 0 ]; then
        echo "✅ Command succeeded" >> "${OUTPUT_DIR}/proof.txt"
    else
        echo "❌ Command failed with exit code ${EXIT_CODE}" >> "${OUTPUT_DIR}/proof.txt"
    fi
done

echo "" >> "${OUTPUT_DIR}/proof.txt"

# Scope gate: enforce allowlist if provided
if [ -n "${ALLOW_FILES}" ]; then
    echo "Enforcing scope gate with allowed files: ${ALLOW_FILES}" >> "${OUTPUT_DIR}/proof.txt"
    
    # Get list of changed files
    CHANGED_FILES=$(git diff --name-only HEAD~1..HEAD 2>/dev/null || git diff --name-only HEAD 2>/dev/null || echo "")
    
    if [ -n "${CHANGED_FILES}" ]; then
        echo "Changed files:" >> "${OUTPUT_DIR}/proof.txt"
        for file in ${CHANGED_FILES}; do
            echo "  - ${file}" >> "${OUTPUT_DIR}/proof.txt"
        done
        
        # Check each changed file against allowlist
        IFS=',' read -ra ALLOWED <<< "${ALLOW_FILES}"
        for file in ${CHANGED_FILES}; do
            ALLOWED_FILE=false
            for allowed in "${ALLOWED[@]}"; do
                # Check if file matches allowed exactly OR is within allowed directory
                if [[ "${file}" == "${allowed}"* ]]; then
                    ALLOWED_FILE=true
                    break
                fi
            done
            
            if [ "${ALLOWED_FILE}" = false ]; then
                echo "❌ Scope gate failed: ${file} not in allowed scope (${ALLOW_FILES})" >> "${OUTPUT_DIR}/proof.txt"
                echo "ERROR: Scope gate violation. File '${file}' is outside allowed scope '${ALLOW_FILES}'."
                exit 4
            fi
        done
        
        echo "✅ All changed files are in allowed scope" >> "${OUTPUT_DIR}/proof.txt"
    else
        echo "No changed files detected" >> "${OUTPUT_DIR}/proof.txt"
    fi
fi

echo "=== Proof Bundle Complete ===" >> "${OUTPUT_DIR}/proof.txt"
echo "Generated: $(date)" >> "${OUTPUT_DIR}/proof.txt"

echo "Proof bundle created at: ${OUTPUT_DIR}/proof.txt"