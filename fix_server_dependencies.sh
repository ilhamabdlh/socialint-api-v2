#!/bin/bash

echo "🔧 Fixing server dependencies..."

# Navigate to project directory
cd /home/ubuntu/socialint-api-v2

# Activate virtual environment
source .venv/bin/activate

# Install missing dependencies
echo "📦 Installing missing dependencies..."
pip install aiohttp
pip install httpx
pip install asyncio

# Install all requirements
echo "📦 Installing all requirements..."
pip install -r requirements.txt

# Check if installation was successful
echo "✅ Checking installation..."
python -c "import aiohttp; print('aiohttp installed successfully')"
python -c "import httpx; print('httpx installed successfully')"

# Restart the application
echo "🔄 Restarting application..."
pkill -f uvicorn
sleep 2

# Start the application
echo "🚀 Starting application..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 > app.log 2>&1 &

echo "✅ Application restarted successfully!"
echo "📋 Check logs with: tail -f app.log"
