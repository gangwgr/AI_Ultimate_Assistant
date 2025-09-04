#!/usr/bin/env python3

import requests
import json
import time

def test_limited_analysis():
    """Test the improved analysis with limits"""
    
    # Configure with real API token
    config = {
        "rp_url": "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com",
        "rp_token": "rgangwar_jEwGN5nJSCu0ff5r1RJl0cgdL4mYfUiXKRsE7Si6wn9xHfOeE-eIAKRxyDSyGH7v",
        "project": "PROW",
        "ssl_verify": False
    }
    
    print("🔧 Step 1: Configuring Report Portal...")
    try:
        response = requests.post(
            "http://localhost:8000/api/report-portal/configure",
            json=config,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Configuration: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return
    
    # Test analysis with limited tests
    analysis_request = {
        "hours_back": 24,
        "components": ["API"],
        "max_tests": 50,  # Limit to 50 tests
        "batch_size": 25,  # Process in batches of 25
        "update_comments": False,
        "update_status": False,
        "generate_report": False
    }
    
    print("\n🔍 Step 2: Testing Limited Analysis (50 tests max)...")
    print("   This should complete much faster with the new limits")
    
    start_time = time.time()
    try:
        response = requests.post(
            "http://localhost:8000/api/report-portal/analyze-failures",
            json=analysis_request,
            headers={"Content-Type": "application/json"},
            timeout=600  # 10 minute timeout
        )
        
        elapsed_time = time.time() - start_time
        print(f"✅ Analysis completed in {elapsed_time:.2f} seconds")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Total Failures: {result.get('total_failures', 0)}")
            print(f"   Analyzed Failures: {result.get('analyzed_failures', 0)}")
            print(f"   Categories: {result.get('categories', {})}")
            print(f"   Priorities: {result.get('priorities', {})}")
            
            # Show some sample results
            if result.get('failures'):
                print(f"\n📋 Sample Analysis Results:")
                for i, failure in enumerate(result['failures'][:3]):  # Show first 3
                    print(f"   {i+1}. {failure.get('test_name', 'Unknown')}")
                    print(f"      Category: {failure.get('category', 'Unknown')}")
                    print(f"      Priority: {failure.get('priority', 'Unknown')}")
                    print(f"      Confidence: {failure.get('confidence', 0)}")
        else:
            print(f"   Error Response: {response.text}")
            
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        print(f"❌ Analysis timed out after {elapsed_time:.2f} seconds")
        print("   The timeout handling is working, but the dataset might be too large")
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ Analysis failed after {elapsed_time:.2f} seconds: {e}")

if __name__ == "__main__":
    test_limited_analysis()
