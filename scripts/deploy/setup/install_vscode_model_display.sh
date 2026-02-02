#!/bin/bash
# Install Dopemux Model Display extension for VS Code / Claude Code

EXTENSION_DIR="$HOME/.vscode/extensions/dopemux-model-display"

echo "📦 Installing Dopemux Model Display for VS Code..."

# Check if extension directory exists
if [ -d "$EXTENSION_DIR" ]; then
    echo "✅ Extension files already installed at: $EXTENSION_DIR"
else
    echo "❌ Extension directory not found. Please ensure the extension was created."
    exit 1
fi

# Verify required files
REQUIRED_FILES=(
    "$EXTENSION_DIR/package.json"
    "$EXTENSION_DIR/extension.js"
    "$EXTENSION_DIR/README.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All extension files present"

# Create symlink for easier access
if [ ! -L "$HOME/Library/Application Support/Code/extensions/dopemux-model-display" ]; then
    ln -sf "$EXTENSION_DIR" "$HOME/Library/Application Support/Code/extensions/dopemux-model-display" 2>/dev/null || true
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Installation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Restart VS Code / Claude Code"
echo "2. Look for the model indicator in the bottom-right status bar"
echo "3. The extension updates every 5 seconds automatically"
echo ""
echo "🔧 Configuration:"
echo "   Open VS Code Settings and search for 'Dopemux Model Display'"
echo ""
echo "🧪 Test:"
echo "   ./scripts/set_model_display.sh gpt-5-pro"
echo "   (Watch the status bar change in ~5 seconds)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
