#!/bin/bash

echo "🧪 ReSemantic Proposition Extraction Experiment"
echo "================================================"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env and add your API keys, then run again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Run comparison test
echo ""
echo "🚀 Running comparison test..."
echo ""
python test_comparison.py

echo ""
echo "✅ Experiment complete!"
echo "📄 Results saved in comparison_results.json"
