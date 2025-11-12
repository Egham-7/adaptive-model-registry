#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════"
echo "🚀 Railway Pre-Deploy: Database Setup"
echo "════════════════════════════════════════════════════════"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

echo "✓ Database URL configured"

# Navigate to scripts directory
cd scripts

# Check if uv is installed, if not install it
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✓ uv installed successfully"
else
    echo "✓ uv already installed"
fi

# Sync Python dependencies
echo "📦 Syncing Python dependencies..."
uv sync --frozen
echo "✓ Dependencies synced"

# Run the database setup
echo ""
echo "🔄 Syncing OpenRouter models to database..."
echo "════════════════════════════════════════════════════════"
uv run python -m setup --db-url "$DATABASE_URL" --no-cache

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "✅ Pre-Deploy Setup Completed Successfully!"
    echo "════════════════════════════════════════════════════════"
    exit 0
else
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "❌ Pre-Deploy Setup Failed!"
    echo "════════════════════════════════════════════════════════"
    exit 1
fi