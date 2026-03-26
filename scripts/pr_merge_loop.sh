#!/bin/bash

# Script to run PR Merge Specialist in a loop until all PRs are processed

echo "Starting PR Merge Loop..."

while true; do
    echo "Running dopemux pr-merge queue-drain..."
    output=$(dopemux pr-merge queue-drain 2>&1)
    
    # Extract the number of merged PRs
    merged=$(echo "$output" | grep -oP 'Merged: \K\d+')
    
    echo "Merged PRs in this run: $merged"
    
    # Check if any PRs were merged
    if [ "$merged" -eq 0 ]; then
        echo "No PRs were merged. Checking if all PRs are processed..."
        
        # Check if there are any blocked PRs
        blocked=$(echo "$output" | grep -c "PRState.APPLY_BLOCKED")
        
        if [ "$blocked" -eq 0 ]; then
            echo "No blocked PRs found. All PRs are processed."
            break
        else
            echo "PRs are still blocked. Retrying in 30 seconds..."
            sleep 30
        fi
    else
        echo "PRs were merged. Retrying to process remaining PRs..."
        sleep 10
    fi
done

echo "PR Merge Loop completed."
