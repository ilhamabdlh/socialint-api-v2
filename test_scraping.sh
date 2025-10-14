#!/bin/bash

echo "================================================================================"
echo "🧪 TESTING AUTOMATED SCRAPING & ANALYSIS"
echo "================================================================================"
echo ""

# Test 1: Scrape dengan auto-analyze
echo "Test 1: Scraping TikTok dengan auto-analyze..."
echo "================================================================================"
curl -s -X POST 'http://localhost:8000/api/v1/scrape/' \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "testbrand2",
    "keywords": ["technology"],
    "platforms": ["tiktok"],
    "max_posts_per_platform": 15,
    "auto_analyze": true
  }' | python3 -m json.tool

echo ""
echo ""

# Wait for analysis
echo "⏳ Waiting 30 seconds for scraping and analysis to complete..."
sleep 30

# Test 2: Check MongoDB
echo ""
echo "Test 2: Checking MongoDB for saved data..."
echo "================================================================================"
curl -s http://localhost:8000/api/v1/results/brands/testbrand2/summary | python3 -m json.tool

echo ""
echo ""
echo "================================================================================"
echo "✅ TESTING COMPLETE"
echo "================================================================================"
