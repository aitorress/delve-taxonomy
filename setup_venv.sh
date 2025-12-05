#!/bin/bash
# Quick setup script for Delve using uv

set -e  # Exit on error

echo "🚀 Setting up Delve with uv..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Project root should contain pyproject.toml"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo ""
    echo "⚠️  Please restart your terminal or run: source \$HOME/.cargo/env"
    echo "   Then run this script again."
    exit 1
fi

echo "✓ Found uv: $(uv --version)"

# Remove existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo "⚠️  Virtual environment '.venv' already exists"
    read -p "   Remove and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing virtual environment..."
        rm -rf .venv
    else
        echo "✓ Using existing virtual environment"
    fi
fi

# Create virtual environment with uv
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment with uv..."
    uv venv
    echo "✓ Virtual environment created"
fi

# Install the package and dependencies
echo "📥 Installing Delve package and dependencies..."
uv pip install -e .

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use Delve in future sessions, activate your virtual environment:"
echo ""
echo "   cd \"/Users/antorres/Documents/Codebases/AI Projects/taxonomy_generator\""
echo "   source .venv/bin/activate"
echo "   delve --version"
echo ""
echo "Then you can use delve commands directly!"
echo ""

