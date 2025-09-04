#!/usr/bin/env python3

import requests
import socket
import subprocess
import sys

def test_network_connectivity():
    """Test network connectivity to Report Portal"""
    
    hostname = "reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com"
    
    print("🔍 Testing Network Connectivity to Report Portal")
    print("=" * 50)
    
    # Test 1: DNS Resolution
    print("\n1️⃣ Testing DNS Resolution...")
    try:
        ip_address = socket.gethostbyname(hostname)
        print(f"✅ DNS Resolution: {hostname} -> {ip_address}")
    except socket.gaierror as e:
        print(f"❌ DNS Resolution Failed: {e}")
        print("   This suggests a network/VPN issue")
        return False
    
    # Test 2: Ping
    print("\n2️⃣ Testing Ping...")
    try:
        result = subprocess.run(['ping', '-c', '3', hostname], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Ping successful")
        else:
            print(f"❌ Ping failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("❌ Ping timeout")
    except FileNotFoundError:
        print("⚠️  Ping command not available")
    
    # Test 3: HTTP Connection
    print("\n3️⃣ Testing HTTP Connection...")
    try:
        response = requests.get(f"https://{hostname}", 
                              timeout=10, 
                              verify=False,
                              headers={'User-Agent': 'Mozilla/5.0'})
        print(f"✅ HTTP Connection: Status {response.status_code}")
    except requests.exceptions.ConnectTimeout:
        print("❌ HTTP Connection Timeout")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTP Connection Error: {e}")
    except Exception as e:
        print(f"❌ HTTP Connection Failed: {e}")
    
    # Test 4: API Endpoint
    print("\n4️⃣ Testing API Endpoint...")
    try:
        response = requests.get(f"https://{hostname}/api/v1/PROW/user", 
                              timeout=10, 
                              verify=False,
                              headers={'User-Agent': 'Mozilla/5.0'})
        print(f"✅ API Endpoint: Status {response.status_code}")
    except requests.exceptions.ConnectTimeout:
        print("❌ API Endpoint Timeout")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ API Endpoint Error: {e}")
    except Exception as e:
        print(f"❌ API Endpoint Failed: {e}")
    
    print("\n" + "=" * 50)
    print("💡 Recommendations:")
    print("   • Check if you're connected to the Red Hat VPN")
    print("   • Verify network access to Red Hat internal services")
    print("   • Try accessing the Report Portal URL in your browser")
    print("   • Contact your network administrator if issues persist")

if __name__ == "__main__":
    test_network_connectivity()
