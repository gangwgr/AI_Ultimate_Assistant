#!/usr/bin/env python3
"""
Test script to verify TAR/TGZ support in the must-gather analyzer
"""

import os
import tempfile
import tarfile
import zipfile
import asyncio
import aiohttp
import json

async def test_tar_support():
    """Test TAR/TGZ file upload support"""
    
    # Create test must-gather content
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create must-gather structure
        cluster_dir = os.path.join(temp_dir, "cluster-scoped-resources")
        hosts_dir = os.path.join(temp_dir, "hosts")
        os.makedirs(cluster_dir, exist_ok=True)
        os.makedirs(hosts_dir, exist_ok=True)
        
        # Create sample log files
        with open(os.path.join(cluster_dir, "etcd.log"), "w") as f:
            f.write("2024-01-01 10:00:00 ERROR: etcd connection failed\n")
            f.write("2024-01-01 10:01:00 ERROR: raft communication timeout\n")
        
        with open(os.path.join(hosts_dir, "apiserver.log"), "w") as f:
            f.write("2024-01-01 10:00:00 ERROR: API server not responding\n")
            f.write("2024-01-01 10:01:00 ERROR: authentication failed\n")
        
        # Test 1: Create TAR file
        tar_path = os.path.join(temp_dir, "test_must_gather.tar")
        with tarfile.open(tar_path, "w") as tar:
            tar.add(cluster_dir, arcname="cluster-scoped-resources")
            tar.add(hosts_dir, arcname="hosts")
        
        print(f"✅ Created TAR file: {tar_path}")
        
        # Test 2: Create TAR.GZ file
        tar_gz_path = os.path.join(temp_dir, "test_must_gather.tar.gz")
        with tarfile.open(tar_gz_path, "w:gz") as tar:
            tar.add(cluster_dir, arcname="cluster-scoped-resources")
            tar.add(hosts_dir, arcname="hosts")
        
        print(f"✅ Created TAR.GZ file: {tar_gz_path}")
        
        # Test 3: Create TGZ file
        tgz_path = os.path.join(temp_dir, "test_must_gather.tgz")
        with tarfile.open(tgz_path, "w:gz") as tar:
            tar.add(cluster_dir, arcname="cluster-scoped-resources")
            tar.add(hosts_dir, arcname="hosts")
        
        print(f"✅ Created TGZ file: {tgz_path}")
        
        # Test 4: Create ZIP file for comparison
        zip_path = os.path.join(temp_dir, "test_must_gather.zip")
        with zipfile.ZipFile(zip_path, 'w') as zip_ref:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.log'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zip_ref.write(file_path, arcname)
        
        print(f"✅ Created ZIP file: {zip_path}")
        
        # Test API endpoints
        async with aiohttp.ClientSession() as session:
            base_url = "http://127.0.0.1:8000"
            
            # Test health endpoint
            async with session.get(f"{base_url}/api/must-gather/health") as response:
                if response.status == 200:
                    print("✅ Must-gather health endpoint working")
                else:
                    print(f"❌ Health endpoint failed: {response.status}")
            
            # Test file uploads
            test_files = [
                ("test_must_gather.tar", tar_path),
                ("test_must_gather.tar.gz", tar_gz_path),
                ("test_must_gather.tgz", tgz_path),
                ("test_must_gather.zip", zip_path)
            ]
            
            for filename, filepath in test_files:
                print(f"\n🧪 Testing {filename}...")
                
                with open(filepath, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('must_gather_file', f, filename=filename)
                    data.add_field('cluster_name', 'test-cluster')
                    
                    async with session.post(f"{base_url}/api/must-gather/analyze", data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ {filename} upload successful")
                            print(f"   - Status: {result.get('status')}")
                            print(f"   - Issues found: {result.get('analysis', {}).get('issues_count', 0)}")
                        else:
                            error_text = await response.text()
                            print(f"❌ {filename} upload failed: {response.status}")
                            print(f"   Error: {error_text}")

if __name__ == "__main__":
    print("🧪 Testing TAR/TGZ support in Must-Gather Analyzer")
    print("=" * 60)
    
    asyncio.run(test_tar_support())
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
