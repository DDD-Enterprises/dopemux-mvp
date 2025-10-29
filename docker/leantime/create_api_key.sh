#!/bin/bash
# Leantime API Key Creator
# Run this after Leantime installation is complete

set -e

echo "════════════════════════════════════════════════════════════"
echo "  Leantime API Key Creator for MCP Integration"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if Leantime is installed
echo "Checking Leantime installation status..."
INSTALL_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)

if [ "$INSTALL_CHECK" = "303" ] || [ "$INSTALL_CHECK" = "302" ]; then
    echo "⚠️  Leantime is not yet installed!"
    echo ""
    echo "Please complete the installation first:"
    echo "  1. Open http://localhost:8080 in your browser"
    echo "  2. Follow the installation wizard"
    echo "  3. Create your admin account"
    echo "  4. Then run this script again"
    echo ""
    exit 1
fi

echo "✓ Leantime appears to be installed"
echo ""

# Check if user can access the web UI
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MANUAL STEPS REQUIRED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To create an API key, please:"
echo ""
echo "1. Open Leantime in your browser:"
echo "   → http://localhost:8080"
echo ""
echo "2. Log in with your admin account"
echo ""
echo "3. Navigate to Company Settings:"
echo "   → Click the gear icon (⚙️) in the top right"
echo "   → Select 'Company Settings'"
echo "   → Or go to: http://localhost:8080/setting/editCompanySettings"
echo ""
echo "4. Find the API section and create a new key:"
echo "   → Look for 'API' or 'API Keys' tab"
echo "   → Click 'Create New API Key' or '+ New API Key'"
echo ""
echo "5. Fill in the details:"
echo "   Key Name: Dopemux MCP Bridge"
echo "   Role: Admin (for full access)"
echo "   Projects: All Projects (or select specific ones)"
echo ""
echo "6. Click Save/Create"
echo ""
echo "7. IMPORTANT: Copy the full API key immediately!"
echo "   It will look like: lt_abc123..._xyz789..."
echo "   You'll only see it once!"
echo ""
echo "8. Then run the configuration script:"
echo "   → ./docker/leantime/configure_bridge.sh <your-api-key>"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Alternative: If you have API key creation permissions via CLI,"
echo "you can use the Leantime admin interface to manage keys."
echo ""
echo "For more details, see: LEANTIME_API_SETUP_GUIDE.md"
echo ""
