#!/bin/bash

# Recruitment Sales Intelligence - Setup Script
# Run this to set up the environment and validate your data

echo "=========================================="
echo "Recruitment Sales Intelligence"
echo "Setup & Validation"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"
echo ""

# Check if Python 3.8+
required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8+ required"
    echo "Current version: $python_version"
    exit 1
fi

echo "✅ Python version OK"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt --break-system-packages

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Add your data files to data/raw/"
echo "   - clients.csv (MySQL export)"
echo "   - spocs.csv (MySQL export)"
echo "   - emails.mbox (email archive)"
echo ""
echo "2. Validate your data:"
echo "   python scripts/validate_data.py"
echo ""
echo "3. Run the pipeline:"
echo "   python scripts/orchestrator.py"
echo ""
echo "For help, see:"
echo "  - QUICK_START.md (15 min guide)"
echo "  - docs/workflow.md (detailed walkthrough)"
echo "  - docs/schema.md (data format reference)"
echo ""
echo "=========================================="
