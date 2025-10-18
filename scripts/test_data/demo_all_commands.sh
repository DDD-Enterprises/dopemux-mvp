#!/bin/bash
#
# Comprehensive Demo of All ConPort Quick Win Commands
# Run this to see all 6 commands in action
#

echo "🎯 ConPort Quick Wins - Complete Demo"
echo "======================================"
echo

echo "📊 1. Decision Statistics (Last 30 days)"
echo "----------------------------------------"
python -m dopemux decisions stats
echo
echo "Press Enter to continue..." && read

echo "📋 2. Decision List (Recent 10)"
echo "----------------------------------------"
python -m dopemux decisions list -n 10
echo
echo "Press Enter to continue..." && read

echo "🔍 3. Decision Show (Detailed View)"
echo "----------------------------------------"
python -m dopemux decisions show c4b0b
echo
echo "Press Enter to continue..." && read

echo "🔔 4. Decision Review (Pending Attention)"
echo "----------------------------------------"
python -m dopemux decisions review
echo
echo "Press Enter to continue..." && read

echo "⚡ 5. Energy History (Last 7 Days)"
echo "----------------------------------------"
python -m dopemux decisions energy status --days 7
echo
echo "Press Enter to continue..." && read

echo "📊 6. Energy Analytics (Pattern Analysis)"
echo "----------------------------------------"
python -m dopemux decisions energy analytics --days 7
echo

echo "✅ Demo Complete!"
echo
echo "Available Commands:"
echo "  dopemux decisions stats              # Aggregate statistics"
echo "  dopemux decisions list               # Searchable list"
echo "  dopemux decisions show <ID>          # Detailed view"
echo "  dopemux decisions review             # Pending reviews"
echo "  dopemux decisions energy log <level> # Log energy"
echo "  dopemux decisions energy status      # Energy history"
echo "  dopemux decisions energy analytics   # Pattern analysis"
