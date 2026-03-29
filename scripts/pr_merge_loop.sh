#!/bin/bash

# Script to run PR Merge Specialist in a loop until all PRs are processed

echo "Starting PR Merge Loop..."

while true; do
    echo "Running dopemux pr-merge queue-drain..."
    # Capture output and also show it on terminal
    output=$(dopemux pr-merge queue-drain 2>&1 | tee /dev/tty)
    
    # Extract the number of merged PRs from the final summary
    merged=$(echo "$output" | grep -oP 'Merged: \K\d+')
    
    # If merged is empty (e.g. crash), default to 0
    merged=${merged:-0}
    
    echo "Merged PRs in this run: $merged"
    
    # Check for blocked or failing PRs in the summary table
    # render_operator_summary uses "blocked" for confidence if blockers exist
    blocked_count=$(echo "$output" | grep -c "| blocked |")
    
    # Also check if any fix attempts failed validation
    validation_failed_count=$(echo "$output" | grep -c "validation still failing")
    
    total_stuck=$((blocked_count + validation_failed_count))
    
    if [ "$merged" -gt 0 ]; then
        echo "PRs were merged. Retrying to process remaining PRs..."
        sleep 5
    elif [ "$total_stuck" -gt 0 ]; then
        echo "No PRs merged, but $total_stuck PRs are blocked or failing validation."
        echo "Exiting loop to avoid infinite retry."
        break
    else
        echo "No merged or blocked PRs detected. All done."
        break
    fi
done

echo "PR Merge Loop completed."
