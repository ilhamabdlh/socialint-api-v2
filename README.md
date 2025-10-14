# 🧠 Social Intelligence API v2.0

AI-powered Social Media Intelligence Analysis Platform menggunakan Google Gemini untuk analisis sentiment, topik, dan audience profiling dari berbagai platform social media dengan MongoDB persistence.

## 📋 Features

### 🚀 Core Features
- ✅ **Multi-Platform Support**: TikTok, Instagram, Twitter/X, YouTube
- ✅ **AI-Powered Analysis**: Sentiment & Topic Analysis menggunakan Google Gemini 2.0 Flash
- ✅ **Smart Data Cleansing**: Duplicate removal, keyword filtering, language detection
- ✅ **Parallel Processing**: Analisis cepat dengan concurrent processing (20 workers)
- ✅ **MongoDB Persistence**: Semua hasil analisis tersimpan permanen
- ✅ **REST API**: FastAPI-based API untuk integrasi mudah
- ✅ **CSV Export**: Backup files untuk setiap analisis
- ✅ **Batch Processing**: Multi-brand analysis dalam satu request

### 📊 Analysis Capabilities
- **Sentiment Analysis**: Positive, Negative, Neutral classification
- **Topic Analysis**: Dynamic topic discovery & categorization
- **Audience Profiling**: Interests, communication styles, values
- **Language Detection**: Automatic Indonesian language filtering
- **Historical Tracking**: Time-series sentiment analysis
- **Brand Comparison**: Multi-brand competitive analysis

## 🏗️ Architecture

### Project Structure
```
socialint-api/
├── app/
│   ├── api/
│   │   ├── routes.py              # Main API endpoints
│   │   └── results_routes.py      # Results retrieval endpoints
│   ├── services/
│   │   ├── ai_service.py          # Google Gemini integration
│   │   ├── analysis_service.py    # Legacy analysis service
│   │   ├── analysis_service_v2.py # MongoDB-enabled service
│   │   └── database_service.py    # MongoDB CRUD operations
│   ├── models/
│   │   ├── schemas.py             # Pydantic API schemas
│   │   └── database.py            # Beanie ODM models
│   ├── database/
│   │   └── mongodb.py             # MongoDB connection
│   ├── utils/
│   │   └── data_helpers.py        # Helper functions
│   ├── config/
│   │   └── settings.py            # Configuration
│   └── main.py                    # FastAPI app
├── run_analysis.py                # CLI tool
├── requirements.txt               # Python dependencies
├── .env                           # Environment configuration
├── README.md                      # This file
├── QUICK_START.md                 # 5-minute setup guide
└── MONGODB_MANUAL_INSTALL.md      # MongoDB installation guide
```

### MongoDB Collections
```
social_intelligence (database)
├── brands                 # Brand metadata
├── platform_analyses      # Analysis results per platform
├── posts                  # Analyzed posts with sentiment/topic
├── comments               # Analyzed comments (Layer 2)
├── analysis_jobs          # Job tracking & history
└── topic_interests        # Aggregated topics & interests
```

## 🚀 Quick Start

### Prerequisites
- ✅ Python 3.13+
- ✅ MongoDB 7.0+ (REQUIRED)
- ✅ Google Gemini API Key

### 1️⃣ Install MongoDB

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

**Linux:**
```bash
sudo apt-get install mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

**Windows:**
Download installer: https://www.mongodb.com/try/download/community

📖 **Detailed guide**: See `MONGODB_MANUAL_INSTALL.md`

### 2️⃣ Setup Python Environment

```bash
# Clone repository
cd /Users/ilhamabdullah/Documents/teorema/socialint-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3️⃣ Configure Environment

Create `.env` file:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=social_intelligence
APP_NAME=Social Intelligence API
DEBUG=True
MAX_WORKERS=20
BATCH_SIZE=100
```

### 4️⃣ Start API

```bash
uvicorn app.main:app --reload
```

✅ **API Ready!** Open: http://localhost:8000/docs

📖 **Quick setup guide**: See `QUICK_START.md`

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Main Endpoints

#### 1. 📊 Analyze Single Platform
**POST** `/analyze/platform`

Analyze data from a single social media platform and save to MongoDB.

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/platform" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "tiktok",
    "brand_name": "hufagripp",
    "file_path": "dataset_tiktok-scraper_hufagripp.json",
    "keywords": ["hufagrip", "hufagripp"]
  }'
```

**Response:**
```json
{
  "platform": "tiktok",
  "brand_name": "hufagripp",
  "layer": "layer1",
  "total_analyzed": 28,
  "cleansing_stats": {
    "initial_count": 28,
    "after_duplicates": 28,
    "after_keywords": 28,
    "after_language": 28,
    "final_count": 28
  },
  "sentiment_distribution": {
    "Positive": 25,
    "Neutral": 2,
    "Negative": 1
  },
  "topics_found": ["Obat Batuk Pilek", "Kesehatan Anak", ...],
  "output_file": "tiktok_hufagripp_layer1.csv",
  "processing_time": 45.2
}
```

---

#### 2. 🎯 Analyze Brand (Multi-Platform)
**POST** `/analyze/brand`

Analyze a brand across multiple platforms simultaneously.

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/brand" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "hufagripp",
    "keywords": ["hufagrip", "hufagripp"],
    "platforms": ["tiktok", "instagram"]
  }'
```

**Note**: Files must exist with naming: `dataset_{platform}-scraper_{brand_name}.json`

**Response:**
```json
{
  "brand_name": "hufagripp",
  "platforms_analyzed": ["tiktok", "instagram"],
  "total_posts": 150,
  "overall_sentiment": {
    "Positive": 120,
    "Neutral": 20,
    "Negative": 10
  },
  "top_topics": ["Obat Batuk", "Kesehatan Anak", "Flu Season", ...],
  "results": [...],
  "saved_to_db": true,
  "message": "Analysis completed and saved to MongoDB. CSV files also generated."
}
```

---

#### 3. 📦 Batch Analysis (Multiple Brands)
**POST** `/analyze/batch`

Process multiple brands in a single batch job.

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "brands": [
      {
        "brand_name": "hufagripp",
        "keywords": ["hufagrip", "hufagripp"],
        "platforms_data": {
          "tiktok": "dataset_tiktok-scraper_hufagripp.json"
        }
      },
      {
        "brand_name": "competitor1",
        "keywords": ["competitor1"],
        "platforms_data": {
          "tiktok": "dataset_tiktok-scraper_competitor1.json"
        }
      }
    ]
  }'
```

---

#### 4. 📤 Upload Data File
**POST** `/upload/data`

Upload a data file for later analysis.

```bash
curl -X POST "http://localhost:8000/api/v1/upload/data" \
  -F "file=@dataset.json" \
  -F "platform=tiktok" \
  -F "brand_name=hufagripp"
```

---

### Results Endpoints

#### 5. 📋 List All Brands
**GET** `/results/brands`

```bash
curl "http://localhost:8000/api/v1/results/brands"
```

#### 6. 📊 Get Brand Summary
**GET** `/results/brands/{brand_name}/summary`

```bash
curl "http://localhost:8000/api/v1/results/brands/hufagripp/summary"
```

**Response:**
```json
{
  "brand_name": "hufagripp",
  "total_analyses": 3,
  "total_posts": 150,
  "platforms": ["tiktok", "instagram"],
  "sentiment_summary": {
    "Positive": 120,
    "Neutral": 20,
    "Negative": 10
  },
  "top_topics": ["Obat Batuk", "Kesehatan Anak", ...]
}
```

#### 7. 🔥 Trending Topics
**GET** `/results/brands/{brand_name}/trending-topics`

```bash
curl "http://localhost:8000/api/v1/results/brands/hufagripp/trending-topics?limit=10"
```

#### 8. 👥 Audience Insights
**GET** `/results/brands/{brand_name}/audience-insights`

```bash
curl "http://localhost:8000/api/v1/results/brands/hufagripp/audience-insights"
```

#### 9. 📈 Sentiment Timeline
**GET** `/results/brands/{brand_name}/sentiment-timeline`

```bash
curl "http://localhost:8000/api/v1/results/brands/hufagripp/sentiment-timeline"
```

#### 10. 📝 Get Posts
**GET** `/results/posts`

```bash
# All posts
curl "http://localhost:8000/api/v1/results/posts?limit=50"

# Filter by brand
curl "http://localhost:8000/api/v1/results/posts?brand_name=hufagripp&limit=50"

# Filter by platform
curl "http://localhost:8000/api/v1/results/posts?platform=tiktok&limit=50"

# Filter by sentiment
curl "http://localhost:8000/api/v1/results/posts?sentiment=Positive&limit=50"
```

#### 11. 🔍 Analysis Jobs
**GET** `/results/jobs`

```bash
# List all jobs
curl "http://localhost:8000/api/v1/results/jobs"

# Get specific job
curl "http://localhost:8000/api/v1/results/jobs/{job_id}"
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | Required |
| `MONGODB_URL` | MongoDB connection URL | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | Database name | `social_intelligence` |
| `APP_NAME` | Application name | `Social Intelligence API` |
| `DEBUG` | Debug mode | `True` |
| `MAX_WORKERS` | Parallel processing workers | `20` |
| `BATCH_SIZE` | AI processing batch size | `100` |
| `GEMINI_MODEL` | Gemini model version | `gemini-2.0-flash` |

### Supported Platforms
- `tiktok` - TikTok videos & posts
- `instagram` - Instagram posts & stories
- `twitter` - Twitter/X tweets
- `youtube` - YouTube videos & comments

---

## 📊 Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT DATA (JSON/CSV)                    │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA CLEANSING LAYER                     │
│  • Remove Duplicates                                        │
│  • Keyword Filtering (explicit content filter)             │
│  • Language Detection (Indonesian only)                     │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 AI ANALYSIS LAYER (Gemini)                  │
│  • Sentiment Analysis (Positive/Negative/Neutral)          │
│  • Topic Discovery & Categorization                         │
│  • (Optional) Audience Profiling:                           │
│    - Interests                                              │
│    - Communication Styles                                   │
│    - Values                                                 │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    PERSISTENCE LAYER                        │
│  • Save to MongoDB                                          │
│  • Generate CSV Export                                      │
│  • Create Analysis Job Record                               │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    RESULTS & INSIGHTS                       │
│  • API Access via /results/* endpoints                      │
│  • Historical Analysis                                      │
│  • Trend Detection                                          │
│  • Multi-Brand Comparison                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 Data Output

### 1. MongoDB Collections
All analysis results stored in structured format:
- **brands**: Brand metadata & keywords
- **platform_analyses**: Analysis summaries per platform
- **posts**: Individual posts with sentiment/topic
- **comments**: Layer 2 comments analysis
- **analysis_jobs**: Job tracking & history
- **topic_interests**: Aggregated topics & trends

### 2. CSV Files
Backup files generated for each analysis:
```
{platform}_{brand_name}_layer1.csv
```

Example:
```
tiktok_hufagripp_layer1.csv
instagram_hufagripp_layer1.csv
```

---

## 🛠️ CLI Tool

For standalone analysis without running the API:

```bash
# Analyze single platform
python run_analysis.py \
  --brand hufagripp \
  --platform tiktok \
  --file dataset_tiktok-scraper_hufagripp.json \
  --keywords hufagrip hufagripp \
  --save-db

# Without MongoDB (CSV only)
python run_analysis.py \
  --brand hufagripp \
  --platform tiktok \
  --file dataset_tiktok-scraper_hufagripp.json \
  --keywords hufagrip hufagripp

# With layer 2 (comments)
python run_analysis.py \
  --brand hufagripp \
  --platform instagram \
  --file comments_data.json \
  --layer 2 \
  --save-db
```

---

## 🧪 Testing

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/api/v1/

# Get supported platforms
curl http://localhost:8000/api/v1/platforms

# Interactive testing
# Open: http://localhost:8000/docs
```

### Run Test Suite

```bash
# Run all tests
python -m pytest test_api.py -v

# Run specific test
python -m pytest test_api.py::test_analyze_platform -v
```

---

## 🆘 Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB status
brew services list | grep mongodb  # macOS
sudo systemctl status mongod       # Linux
Get-Service MongoDB                # Windows

# Test connection
mongosh "mongodb://localhost:27017"

# Check API connection
python -c "from app.database.mongodb import connect_to_mongodb; import asyncio; asyncio.run(connect_to_mongodb())"
```

### API Errors

```bash
# Check logs
uvicorn app.main:app --reload --log-level debug

# Verify dependencies
pip list | grep -E "fastapi|beanie|motor|pandas"

# Reinstall if needed
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Kill existing process
pkill -f uvicorn

# Or use different port
uvicorn app.main:app --reload --port 8001
```

---

## 📖 Additional Documentation

- **QUICK_START.md** - 5-minute setup guide
- **MONGODB_MANUAL_INSTALL.md** - Detailed MongoDB installation
- **Swagger UI** - Interactive API docs at http://localhost:8000/docs
- **ReDoc** - Alternative docs at http://localhost:8000/redoc

---

## 🏆 Tech Stack

- **Backend**: FastAPI 0.115+
- **AI**: Google Gemini 2.0 Flash
- **Database**: MongoDB 7.0 + Beanie ODM
- **Data Processing**: Pandas, NumPy
- **Async**: Motor (async MongoDB driver)
- **Validation**: Pydantic v2
- **Concurrency**: ThreadPoolExecutor (20 workers)

---

## 📝 License

This project is proprietary software for Teorema.

---

## 🙏 Acknowledgments

- Google Gemini API for AI-powered analysis
- FastAPI framework
- MongoDB & Beanie ODM
- Python asyncio ecosystem

---

## 📞 Support

For issues or questions:
1. Check documentation files
2. Review error logs
3. Test with Swagger UI at http://localhost:8000/docs
4. Verify MongoDB is running

---

**Built with ❤️ for Social Media Intelligence Analysis**

🚀 **Version**: 2.0.0  
📅 **Last Updated**: October 2025  
🔧 **Status**: Production Ready
