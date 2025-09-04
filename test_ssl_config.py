#!/usr/bin/env python3

import json
from pydantic import BaseModel

class ReportPortalConfig(BaseModel):
    rp_url: str
    rp_token: str
    project: str
    ssl_verify: bool = False  # Default to False for Red Hat internal systems

# Test 1: When ssl_verify is not provided
config1 = ReportPortalConfig(
    rp_url="https://test.com",
    rp_token="token123",
    project="PROW"
)
print(f"Test 1 - No ssl_verify provided: {config1.ssl_verify}")

# Test 2: When ssl_verify is explicitly False
config2 = ReportPortalConfig(
    rp_url="https://test.com",
    rp_token="token123",
    project="PROW",
    ssl_verify=False
)
print(f"Test 2 - ssl_verify=False: {config2.ssl_verify}")

# Test 3: When ssl_verify is explicitly True
config3 = ReportPortalConfig(
    rp_url="https://test.com",
    rp_token="token123",
    project="PROW",
    ssl_verify=True
)
print(f"Test 3 - ssl_verify=True: {config3.ssl_verify}")

# Test 4: Simulate JSON from frontend (no ssl_verify field)
json_data = {
    "rp_url": "https://test.com",
    "rp_token": "token123",
    "project": "PROW"
}
config4 = ReportPortalConfig(**json_data)
print(f"Test 4 - JSON without ssl_verify: {config4.ssl_verify}")

# Test 5: Simulate JSON from frontend (with ssl_verify field)
json_data2 = {
    "rp_url": "https://test.com",
    "rp_token": "token123",
    "project": "PROW",
    "ssl_verify": False
}
config5 = ReportPortalConfig(**json_data2)
print(f"Test 5 - JSON with ssl_verify=False: {config5.ssl_verify}")
