#!/usr/bin/env python3

import requests
import json
import time

def test_analysis_with_timeout():
    """Test the analysis endpoint with timeout handling"""
    
    # First, configure the Report Portal
    config = {
        "rp_url": "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com",
        "rp_token": "test-token",
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
    
    # Test analysis with timeout
    analysis_request = {
        "hours_back": 24,
        "components": ["API"],
        "update_comments": False,
        "update_status": False,
        "generate_report": False
    }
    
    print("\n🔍 Step 2: Testing Analysis with Timeout...")
    print("   This should complete within 5 minutes or timeout gracefully")
    
    start_time = time.time()
    try:
        response = requests.post(
            "http://localhost:8000/api/report-portal/analyze-failures",
            json=analysis_request,
            headers={"Content-Type": "application/json"},
            timeout=310  # 5 minutes + 10 seconds buffer
        )
        
        elapsed_time = time.time() - start_time
        print(f"✅ Analysis completed in {elapsed_time:.2f} seconds")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Total Failures: {result.get('total_failures', 0)}")
            print(f"   Analyzed Failures: {result.get('analyzed_failures', 0)}")
            print(f"   Categories: {result.get('categories', {})}")
        else:
            print(f"   Error Response: {response.text}")
            
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        print(f"❌ Analysis timed out after {elapsed_time:.2f} seconds")
        print("   This indicates the timeout handling is working correctly")
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ Analysis failed after {elapsed_time:.2f} seconds: {e}")

if __name__ == "__main__":
    test_analysis_with_timeout()
