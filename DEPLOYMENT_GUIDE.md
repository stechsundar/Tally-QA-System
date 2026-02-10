# Tally AI Deployment Guide

## Fixed Issues ✅

1. **Environment Variables**: Added proper logging and validation for `ANTHROPIC_API_KEY`
2. **Error Handling**: Improved error messages and logging for debugging
3. **Health Checks**: Added `/health` endpoint for detailed system status
4. **CORS Configuration**: Already properly configured for cross-origin requests
5. **Frontend Configuration**: Updated to support HuggingFace backend URLs

## HuggingFace Deployment Steps

### 1. Prepare Your Space
1. Create a new HuggingFace Space (Docker SDK)
2. Clone the space locally or use the web interface

### 2. Upload Required Files
Upload these files to your HuggingFace Space:
```
server.py                 # Main FastAPI server
qa_system.py             # QA system logic
analytics_engine.py      # Analytics engine
tally_docs.json          # Your scraped documentation
tally_chroma_db/         # Entire vector database directory
subdomains.json          # Configuration
Dockerfile               # Already configured for HF
requirements.txt         # Python dependencies
```

### 3. Set Environment Variables
In your HuggingFace Space settings, add a secret:
- **Name**: `ANTHROPIC_API_KEY`
- **Value**: Your actual Anthropic API key

### 4. Test Deployment
After deployment, test these endpoints:
- `https://your-space.hf.space/` - Root endpoint
- `https://your-space.hf.space/health` - Detailed health check
- `https://your-space.hf.space/status` - System status
- `https://your-space.hf.space/admin` - Gradio testing interface

### 5. Update Frontend
Update your Netlify frontend environment variable:
- **VITE_API_BASE**: `https://your-space.hf.space`

## Common Issues & Solutions

### Issue: "QA system not initialized"
**Solution**: 
1. Check if `ANTHROPIC_API_KEY` is set in Space secrets
2. Verify `tally_docs.json` and `tally_chroma_db/` are uploaded
3. Check the `/health` endpoint for detailed status

### Issue: CORS errors
**Solution**: The backend already allows all origins. If you still get CORS errors, check if the frontend URL is correct.

### Issue: Memory errors
**Solution**: 
1. Use a larger Space tier if available
2. Consider reducing the vector database size
3. Add memory optimization to the embeddings model

## Testing Commands

```bash
# Test health endpoint
curl https://your-space.hf.space/health

# Test status endpoint  
curl https://your-space.hf.space/status

# Test Q&A endpoint
curl -X POST https://your-space.hf.space/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I enable BOM in TallyPrime?"}'
```

## Next Steps

1. Deploy the backend to HuggingFace Spaces
2. Update your Netlify frontend with the new backend URL
3. Test the full integration
4. Monitor logs for any issues
