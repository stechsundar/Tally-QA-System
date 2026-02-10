#!/bin/bash

echo "🔍 Testing HuggingFace Space endpoints..."
echo ""

BASE_URL="https://tallysundar-tally-ai-wind.hf.space"

echo "Testing root endpoint:"
curl -s $BASE_URL/ | jq . || echo "Failed to connect to root endpoint"
echo ""

echo "Testing health endpoint:"
curl -s $BASE_URL/health | jq . || echo "Failed to connect to health endpoint"
echo ""

echo "Testing status endpoint:"
curl -s $BASE_URL/status | jq . || echo "Failed to connect to status endpoint"
echo ""

echo "Testing config endpoint:"
curl -s $BASE_URL/config | jq . || echo "Failed to connect to config endpoint"
echo ""

echo "If all endpoints show 'Failed', you need to:"
echo "1. Replace server.py with server_clean.py content"
echo "2. Restart your HuggingFace Space"
echo "3. Wait 2-3 minutes for redeployment"
