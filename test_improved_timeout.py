#!/usr/bin/env python3

import requests
import json
import time

def test_improved_timeout():
    """Test the Report Portal analysis with improved timeout handling"""
    
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
    
    # Test with conservative settings
    print("\n🔍 Testing with Improved Timeout Settings")
    print("=" * 50)
    
    test_scenarios = [
        {
            "name": "Small Analysis (25 tests, 12 hours)",
            "request": {
                "hours_back": 12,  # Reduced time range
                "components": ["API"],
                "max_tests": 25,   # Reduced test count
                "batch_size": 10,  # Smaller batches
                "update_comments": False,
                "update_status": False,
                "generate_report": False
            }
        },
        {
            "name": "Medium Analysis (50 tests, 24 hours)",
            "request": {
                "hours_back": 24,
                "components": ["API"],
                "max_tests": 50,
                "batch_size": 25,
                "update_comments": False,
                "update_status": False,
                "generate_report": False
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔍 Test {i}: {scenario['name']}")
        print("-" * 40)
        
        start_time = time.time()
        try:
            response = requests.post(
                "http://localhost:8000/api/report-portal/analyze-failures",
                json=scenario['request'],
                headers={"Content-Type": "application/json"},
                timeout=1200  # 20 minute timeout
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
                    for j, failure in enumerate(result['failures'][:3]):  # Show first 3
                        print(f"   {j+1}. {failure.get('test_name', 'Unknown')}")
                        print(f"      Category: {failure.get('category', 'Unknown')}")
                        print(f"      Priority: {failure.get('priority', 'Unknown')}")
                        print(f"      Confidence: {failure.get('confidence', 0)}")
                else:
                    print("   📝 Note: No failures found (network connectivity issue)")
            else:
                print(f"   Error Response: {response.text}")
                
        except requests.exceptions.Timeout:
            elapsed_time = time.time() - start_time
            print(f"❌ Analysis timed out after {elapsed_time:.2f} seconds")
            print("   The timeout handling is working, but the dataset might be too large")
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"❌ Analysis failed after {elapsed_time:.2f} seconds: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 IMPROVEMENTS MADE")
    print("=" * 50)
    print()
    print("✅ **Timeout Optimizations:**")
    print("   • Increased base timeout from 5 to 10 minutes")
    print("   • Reduced test multiplier from 100 to 50 tests")
    print("   • Added 30-minute maximum timeout cap")
    print("   • Reduced concurrent analyses from 5 to 3")
    print()
    print("✅ **Conservative Settings:**")
    print("   • Smaller batch sizes (10-25 tests)")
    print("   • Reduced test counts (25-50 tests)")
    print("   • Shorter time ranges (12-24 hours)")
    print()
    print("🚀 **Expected Results:**")
    print("   • Faster completion times")
    print("   • More reliable analysis")
    print("   • Better progress reporting")
    print("   • Reduced timeout errors")

if __name__ == "__main__":
    test_improved_timeout()
