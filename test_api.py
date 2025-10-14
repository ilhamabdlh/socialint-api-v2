"""
Simple script to test the API
Run the API server first: uvicorn app.main:app --reload
Then run this script: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health_check():
    """Test if API is running"""
    response = requests.get(f"{BASE_URL}/")
    print("Health Check:", response.json())
    return response.status_code == 200

def test_get_platforms():
    """Test get supported platforms"""
    response = requests.get(f"{BASE_URL}/platforms")
    print("\nSupported Platforms:", response.json())
    return response.status_code == 200

def test_analyze_platform():
    """Test single platform analysis"""
    payload = {
        "platform": "tiktok",
        "brand_name": "hufagripp",
        "file_path": "dataset_tiktok-scraper_hufagripp.json",
        "keywords": ["hufagrip", "hufagripp"]
    }
    
    print("\nTesting platform analysis...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/analyze/platform",
        params=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ Analysis Result:")
        print(f"Platform: {result['platform']}")
        print(f"Total Analyzed: {result['total_analyzed']}")
        print(f"Sentiment Distribution: {result['sentiment_distribution']}")
        print(f"Topics Found: {len(result['topics_found'])}")
        print(f"Output File: {result['output_file']}")
        print(f"Processing Time: {result['processing_time']}s")
        return True
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        return False

def main():
    print("="*80)
    print("SOCIAL INTELLIGENCE API - TEST SUITE")
    print("="*80)
    
    tests = [
        ("Health Check", test_health_check),
        ("Get Platforms", test_get_platforms),
        ("Analyze Platform", test_analyze_platform)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"Running: {test_name}")
        print(f"{'='*80}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()

