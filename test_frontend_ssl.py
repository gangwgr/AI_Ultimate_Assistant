#!/usr/bin/env python3

import requests
import json

# Test the backend endpoint directly
def test_ssl_config():
    # Test 1: Send with ssl_verify=False (unchecked checkbox)
    config1 = {
        "rp_url": "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com",
        "rp_token": "test-token",
        "project": "PROW",
        "ssl_verify": False
    }
    
    print("Test 1: Sending ssl_verify=False")
    print(f"Config: {config1}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/report-portal/configure",
            json=config1,
            headers={"Content-Type": "application/json"}
        )
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Send without ssl_verify field (should default to False)
    config2 = {
        "rp_url": "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com",
        "rp_token": "test-token",
        "project": "PROW"
    }
    
    print("Test 2: Sending without ssl_verify field")
    print(f"Config: {config2}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/report-portal/configure",
            json=config2,
            headers={"Content-Type": "application/json"}
        )
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ssl_config()
