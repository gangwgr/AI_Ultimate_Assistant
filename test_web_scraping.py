#!/usr/bin/env python3
"""
Test script for web scraping functionality
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AI_Ultimate_Assistant'))
from continuous_learning import ContinuousLearningSystem

async def test_web_scraping():
    """Test web scraping functionality"""
    system = ContinuousLearningSystem()
    
    # Test URLs
    test_urls = [
        "https://issues.redhat.com/browse/OCPQE-30241",
        "https://example.com",
        "https://httpbin.org/html"
    ]
    
    print("🔍 Testing Web Scraping Functionality")
    print("=" * 50)
    
    for url in test_urls:
        print(f"\n📝 Testing URL: {url}")
        try:
            content = await system.scrape_web_url(url)
            if content:
                print(f"✅ Success! Content length: {len(content)} characters")
                print(f"📄 First 200 characters: {content[:200]}...")
            else:
                print("❌ No content retrieved")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Testing with Continuous Learning System")
    print("=" * 50)
    
    # Test the full continuous learning process
    try:
        result = await system.update_model_continuously(
            "granite3.3-balanced-enhanced:latest",
            ["https://httpbin.org/html"],
            progress_callback=lambda msg: print(f"📊 {msg}")
        )
        print(f"✅ Continuous learning result: {result}")
    except Exception as e:
        print(f"❌ Continuous learning error: {e}")

if __name__ == "__main__":
    asyncio.run(test_web_scraping())
