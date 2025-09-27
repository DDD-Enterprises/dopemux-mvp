#!/bin/bash

# Dopemux Documentation Recovery - Past 3 Days Expansion
# Systematically finds and recovers ALL documentation deleted in past 3 days

set -e

EXPANDED_DIR="./ALL_RECOVERED_DOCS_EXPANDED"
LOG_FILE="./recovery_3_days.log"

echo "🔍 Starting 3-day documentation recovery expansion..."
echo "📅 $(date)" | tee -a "$LOG_FILE"

# Create expanded recovery directory
mkdir -p "$EXPANDED_DIR"
echo "📁 Created expanded recovery directory" | tee -a "$LOG_FILE"

# Find ALL commits from past 3 days
echo "🕐 Finding commits from past 3 days..." | tee -a "$LOG_FILE"
git log --since="3 days ago" --oneline > past_3_days_commits.txt

echo "📊 Commits found:" | tee -a "$LOG_FILE"
cat past_3_days_commits.txt | tee -a "$LOG_FILE"

# Function to check each commit for deleted markdown files
check_commit_for_deletions() {
    local commit=$1
    local commit_short=${commit:0:7}

    echo "🔍 Checking commit $commit_short for deletions..." | tee -a "$LOG_FILE"

    # Get deleted markdown files
    git show --name-only "$commit" | grep "^D.*\.md$" > "${commit_short}_deletions.txt" 2>/dev/null || touch "${commit_short}_deletions.txt"

    local deletion_count=$(wc -l < "${commit_short}_deletions.txt")

    if [ "$deletion_count" -gt 0 ]; then
        echo "🎯 Found $deletion_count deletions in $commit_short" | tee -a "$LOG_FILE"

        # Create directory for this commit
        mkdir -p "$EXPANDED_DIR/commit_$commit_short"

        # Recover each deleted file
        local recovered=0
        while IFS= read -r file; do
            if [ -n "$file" ]; then
                # Create directory structure
                mkdir -p "$EXPANDED_DIR/commit_$commit_short/$(dirname "$file")"

                # Recover the file
                if git show "$commit^:$file" > "$EXPANDED_DIR/commit_$commit_short/$file" 2>/dev/null; then
                    echo "✅ Recovered: $file" | tee -a "$LOG_FILE"
                    ((recovered++))
                else
                    echo "❌ Failed to recover: $file" | tee -a "$LOG_FILE"
                fi
            fi
        done < "${commit_short}_deletions.txt"

        echo "📊 Recovered $recovered/$deletion_count files from $commit_short" | tee -a "$LOG_FILE"
    else
        echo "ℹ️  No deletions in $commit_short" | tee -a "$LOG_FILE"
    fi
}

# Check each commit from past 3 days
total_commits=$(wc -l < past_3_days_commits.txt)
echo "🎯 Checking $total_commits commits for deletions..." | tee -a "$LOG_FILE"

commit_count=0
while IFS= read -r line; do
    commit=$(echo "$line" | cut -d' ' -f1)
    ((commit_count++))
    echo "📈 Progress: $commit_count/$total_commits" | tee -a "$LOG_FILE"
    check_commit_for_deletions "$commit"
done < past_3_days_commits.txt

# Count total recovered files
total_files=$(find "$EXPANDED_DIR" -name "*.md" | wc -l)
total_size=$(du -sh "$EXPANDED_DIR" | cut -f1)

echo "🎉 3-DAY RECOVERY EXPANSION COMPLETE!" | tee -a "$LOG_FILE"
echo "📊 Total additional files recovered: $total_files" | tee -a "$LOG_FILE"
echo "💾 Total size: $total_size" | tee -a "$LOG_FILE"
echo "📁 Location: $EXPANDED_DIR" | tee -a "$LOG_FILE"

# Create summary
echo "=== 3-DAY RECOVERY EXPANSION SUMMARY ===" > recovery_3_days_summary.txt
echo "Recovery Date: $(date)" >> recovery_3_days_summary.txt
echo "Commits Checked: $total_commits" >> recovery_3_days_summary.txt
echo "Additional Files Recovered: $total_files" >> recovery_3_days_summary.txt
echo "Total Size: $total_size" >> recovery_3_days_summary.txt
echo "" >> recovery_3_days_summary.txt
echo "Ready for docuXtractor processing!" >> recovery_3_days_summary.txt

echo "📋 3-day expansion summary saved to recovery_3_days_summary.txt"
echo "🎯 Ready to process $total_files additional recovered files!"