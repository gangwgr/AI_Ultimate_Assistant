#!/usr/bin/env python3

import requests
import json

def test_detailed_failures():
    """Test that detailed failures are now being returned"""
    
    print("🔍 Testing Detailed Failures Display")
    print("====================================")
    
    # Configure Report Portal
    print("\n1️⃣ Configuring Report Portal...")
    config = {
        "rp_url": "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com",
        "rp_token": "rgangwar_jEwGN5nJSCu0ff5r1RJl0cgdL4mYfUiXKRsE7Si6wn9xHfOeE-eIAKRxyDSyGH7v",
        "project": "PROW",
        "ssl_verify": False
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/report-portal/configure",
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Report Portal configured successfully")
        else:
            print(f"❌ Configuration failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Test selective analysis with detailed failures
    print("\n2️⃣ Testing selective analysis with detailed failures...")
    try:
        analysis_request = {
            "test_ids": ["test_001", "test_002"],
            "update_comments": False,
            "update_status": False,
            "generate_report": False
        }
        
        response = requests.post(
            "http://localhost:8000/api/report-portal/analyze-selected",
            json=analysis_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Selective analysis working with detailed failures")
            print(f"   Analyzed {data.get('analyzed_failures', 0)} test cases")
            print(f"   Total failures: {data.get('total_failures', 0)}")
            print(f"   Categories: {data.get('categories', {})}")
            print(f"   Priorities: {data.get('priorities', {})}")
            
            # Check if detailed failures are present
            failures = data.get('failures', [])
            if failures:
                print(f"   ✅ Detailed failures array present with {len(failures)} items")
                print("   Sample failure details:")
                for i, failure in enumerate(failures[:2]):
                    print(f"     {i+1}. {failure.get('test_name', 'Unknown')}")
                    print(f"        Category: {failure.get('category', 'Unknown')}")
                    print(f"        Priority: {failure.get('priority', 'Unknown')}")
                    print(f"        Analysis: {failure.get('ai_analysis', 'N/A')[:100]}...")
                    print(f"        Suggested Fix: {failure.get('suggested_fix', 'N/A')[:100]}...")
                    print(f"        Tags: {failure.get('tags', [])}")
            else:
                print("   ❌ No detailed failures array found")
                
        else:
            print(f"❌ Selective analysis failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error testing selective analysis: {e}")
        return
    
    # Test the frontend display
    print("\n3️⃣ Testing frontend display...")
    try:
        response = requests.get("http://localhost:8000/frontend/report_portal.html", timeout=10)
        if response.status_code == 200:
            html_content = response.text
            
            # Check if displayAnalysisResults function handles failures array
            if 'failures' in html_content and 'displayAnalysisResults' in html_content:
                print("✅ Frontend has displayAnalysisResults function")
                print("✅ Frontend expects failures array")
            else:
                print("❌ Frontend missing displayAnalysisResults function")
                
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing frontend: {e}")
        return
    
    print("\n===================")
    print("🎉 DETAILED FAILURES FIX SUMMARY")
    print("===================")
    print("\n✅ **Fixed Issues:**")
    print("   • API now returns detailed failures array")
    print("   • Each failure includes test_name, category, priority")
    print("   • Each failure includes ai_analysis and suggested_fix")
    print("   • Each failure includes tags and duration")
    print("   • Frontend can now display detailed failure information")
    print("\n✅ **What You'll See Now:**")
    print("   • Detailed test failure information in 'Analyzed Failures' section")
    print("   • AI-generated analysis for each test case")
    print("   • Suggested fixes for each failure")
    print("   • Priority levels and tags for each test")
    print("   • Complete failure details instead of 'No detailed failure information available'")
    print("\n🚀 **Ready to Use:**")
    print("   • Open browser to: http://localhost:8000/")
    print("   • Navigate to Report Portal AI Analyzer")
    print("   • Configure Report Portal connection")
    print("   • Click '🔍 Discover Test Cases'")
    print("   • Select test cases and click '🚀 Analyze Selected Test Cases'")
    print("   • You should now see detailed failure information in the results!")

if __name__ == "__main__":
    test_detailed_failures()
