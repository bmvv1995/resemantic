#!/bin/bash

# Run ReSemantic Streamlit app

echo "🚀 Starting ReSemantic Streamlit App..."
echo ""

# Check for .env
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your OPENAI_API_KEY"
    echo ""
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Starting Streamlit..."
echo "🌐 Access the app at: http://localhost:8501"
echo "📱 Mobile friendly! Open on your phone too."
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run app.py --server.port=8501 --server.address=0.0.0.0
