#!/bin/bash

# Tally AI - HuggingFace Deployment Script
echo "🚀 Deploying Tally AI to HuggingFace Spaces..."

# Check if we're in the right directory
if [ ! -f "server.py" ]; then
    echo "❌ Error: server.py not found. Please run this from the project root."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p .huggingface

# Create space configuration
cat > .huggingface/README.md << 'EOF'
---
title: Tally AI Backend
emoji: 🎯
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# Tally AI Backend

Backend API for Tally Expert AI system.

## Features
- RAG-based Q&A system
- FastAPI endpoints
- Gradio admin interface
- Chroma vector database

## Environment Variables
Set `ANTHROPIC_API_KEY` in your Space secrets.

## API Endpoints
- `/` - API info
- `/health` - Health check
- `/status` - System status
- `/ask` - Q&A endpoint
- `/admin` - Gradio interface
EOF

# Create requirements file for HF
echo "📦 Creating requirements.txt..."
cat > requirements-hf.txt << 'EOF'
fastapi
uvicorn
pydantic
python-multipart
gradio
langchain
langchain-community
langchain-anthropic
langchain-text-splitters
langchain-huggingface
langchain-experimental
langchain-chroma
chromadb
sentence-transformers
beautifulsoup4
requests
lxml
html2text
anthropic
python-dotenv
pandas
tabulate
EOF

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Create a new HuggingFace Space"
echo "2. Upload these files to the Space:"
echo "   - server.py"
echo "   - qa_system.py"
echo "   - analytics_engine.py"
echo "   - tally_docs.json"
echo "   - tally_chroma_db/ (entire directory)"
echo "   - subdomains.json"
echo "   - Dockerfile"
echo "   - requirements-hf.txt (as requirements.txt)"
echo "   - .huggingface/README.md (as README.md)"
echo ""
echo "3. Set ANTHROPIC_API_KEY in Space secrets"
echo "4. Deploy and test the endpoints"
echo ""
echo "🔍 Test endpoints after deployment:"
echo "   - GET https://your-space.hf.space/health"
echo "   - GET https://your-space.hf.space/status"
echo "   - POST https://your-space.hf.space/ask"
