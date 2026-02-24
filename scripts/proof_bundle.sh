#!/bin/bash
# Simple proof bundle script for verification

set -e

TP_ID="TP-WORKDIR-GATE-0001"
OUTPUT_DIR="proof/${TP_ID}"

# Parse --tp argument first
while [ $# -gt 0 ]; do
    if [ "$1" = "--tp" ]; then
        shift
        TP_ID="$1"
        OUTPUT_DIR="proof/${TP_ID}"
        shift
        break
    else
        shift
    fi
done

mkdir -p "${OUTPUT_DIR}"

echo "=== Proof Bundle ${TP_ID} ===" > "${OUTPUT_DIR}/proof.txt"
echo "Commands executed:" >> "${OUTPUT_DIR}/proof.txt"

# Run each command and capture output
while [ $# -gt 0 ]; do
    if [ "$1" = "--cmd" ]; then
        shift
        CMD="$1"
        shift
        
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
    else
        shift
    fi
done

echo "" >> "${OUTPUT_DIR}/proof.txt"
echo "=== Proof Bundle Complete ===" >> "${OUTPUT_DIR}/proof.txt"
echo "Generated: $(date)" >> "${OUTPUT_DIR}/proof.txt"

echo "Proof bundle created at: ${OUTPUT_DIR}/proof.txt"