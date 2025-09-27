#!/bin/bash

# Dopemux Documentation Recovery Script
# Systematically recovers all deleted documentation from git history

set -e

RECOVERY_DIR="./ALL_RECOVERED_DOCS"
LOG_FILE="./recovery.log"

echo "🚀 Starting comprehensive Dopemux documentation recovery..."
echo "📅 $(date)" | tee -a "$LOG_FILE"

# Create recovery directory
mkdir -p "$RECOVERY_DIR/commit_11b6b52"
mkdir -p "$RECOVERY_DIR/commit_347e523"
mkdir -p "$RECOVERY_DIR/commit_e682f11"

echo "📁 Created recovery directories" | tee -a "$LOG_FILE"

# Function to recover files from a commit
recover_from_commit() {
    local commit=$1
    local target_dir=$2
    local description=$3

    echo "🔍 Recovering from $description ($commit)..." | tee -a "$LOG_FILE"

    # Get list of deleted markdown files
    git show --name-only "$commit" | grep "^docs.*\.md$" > "${commit}_deleted_files.txt" 2>/dev/null || true

    local count=0
    while IFS= read -r file; do
        if [ -n "$file" ]; then
            # Create directory structure
            mkdir -p "$target_dir/$(dirname "$file")"

            # Recover the file
            if git show "$commit^:$file" > "$target_dir/$file" 2>/dev/null; then
                echo "✅ Recovered: $file" | tee -a "$LOG_FILE"
                ((count++))
            else
                echo "❌ Failed to recover: $file" | tee -a "$LOG_FILE"
            fi
        fi
    done < "${commit}_deleted_files.txt"

    echo "📊 Recovered $count files from $description" | tee -a "$LOG_FILE"
    return $count
}

# Recovery from major cleanup (117 files)
echo "🎯 Phase 1: Major cleanup recovery..." | tee -a "$LOG_FILE"
recover_from_commit "11b6b52" "$RECOVERY_DIR/commit_11b6b52" "major documentation cleanup"
phase1_count=$?

# Recovery from architecture improvements (28 files)
echo "🎯 Phase 2: Architecture improvements recovery..." | tee -a "$LOG_FILE"
recover_from_commit "347e523" "$RECOVERY_DIR/commit_347e523" "architecture improvements"
phase2_count=$?

# Recovery from integration updates (19 files)
echo "🎯 Phase 3: Integration updates recovery..." | tee -a "$LOG_FILE"
recover_from_commit "e682f11" "$RECOVERY_DIR/commit_e682f11" "integration updates"
phase3_count=$?

# Count total recovered files
total_files=$(find "$RECOVERY_DIR" -name "*.md" | wc -l)
total_size=$(du -sh "$RECOVERY_DIR" | cut -f1)

echo "🎉 RECOVERY COMPLETE!" | tee -a "$LOG_FILE"
echo "📊 Total files recovered: $total_files" | tee -a "$LOG_FILE"
echo "💾 Total size: $total_size" | tee -a "$LOG_FILE"
echo "📁 Recovery location: $RECOVERY_DIR" | tee -a "$LOG_FILE"

# Create summary report
echo "=== DOPEMUX DOCUMENTATION RECOVERY SUMMARY ===" > recovery_summary.txt
echo "Recovery Date: $(date)" >> recovery_summary.txt
echo "Phase 1 (Major cleanup): $phase1_count files" >> recovery_summary.txt
echo "Phase 2 (Architecture): $phase2_count files" >> recovery_summary.txt
echo "Phase 3 (Integration): $phase3_count files" >> recovery_summary.txt
echo "TOTAL RECOVERED: $total_files files ($total_size)" >> recovery_summary.txt
echo "" >> recovery_summary.txt
echo "Files ready for docuXtractor processing!" >> recovery_summary.txt

echo "📋 Recovery summary saved to recovery_summary.txt"
echo "🎯 Ready for docuXtractor processing of $total_files files!"