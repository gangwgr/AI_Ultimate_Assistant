#!/usr/bin/env python3
"""
Test script specifically for testing .tar.gz file handling
"""

import os
import tempfile
import tarfile
import asyncio
import aiohttp
import json

async def test_targz_specific():
    """Test .tar.gz file handling specifically"""
    
    # Create a test TAR.GZ file
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
        
        # Create TAR.GZ file with the exact name from user
        tar_gz_path = os.path.join(temp_dir, "must-gather.local.7676646060719736617.tar.gz")
        with tarfile.open(tar_gz_path, "w:gz") as tar:
            tar.add(cluster_dir, arcname="cluster-scoped-resources")
            tar.add(hosts_dir, arcname="hosts")
        
        print(f"✅ Created test TAR.GZ file: {tar_gz_path}")
        print(f"   File size: {os.path.getsize(tar_gz_path)} bytes")
        
        # Test upload through API
        async with aiohttp.ClientSession() as session:
            base_url = "http://127.0.0.1:8000"
            
            print(f"\n🧪 Testing .tar.gz upload with filename: {os.path.basename(tar_gz_path)}")
            
            with open(tar_gz_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('must_gather_file', f, filename=os.path.basename(tar_gz_path))
                data.add_field('cluster_name', 'test-cluster-targz')
                
                async with session.post(f"{base_url}/api/must-gather/analyze", data=data) as response:
                    print(f"Upload response status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ TAR.GZ upload successful")
                        print(f"   - Status: {result.get('status')}")
                        print(f"   - Issues found: {result.get('analysis', {}).get('issues_count', 0)}")
                        print(f"   - Cluster: {result.get('cluster_name')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ TAR.GZ upload failed: {response.status}")
                        print(f"   Error: {error_text}")
            
            # Test with different .tar.gz filename
            tar_gz_path2 = os.path.join(temp_dir, "test_must_gather.tar.gz")
            with tarfile.open(tar_gz_path2, "w:gz") as tar:
                tar.add(cluster_dir, arcname="cluster-scoped-resources")
                tar.add(hosts_dir, arcname="hosts")
            
            print(f"\n🧪 Testing .tar.gz upload with filename: test_must_gather.tar.gz")
            
            with open(tar_gz_path2, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('must_gather_file', f, filename='test_must_gather.tar.gz')
                data.add_field('cluster_name', 'test-cluster-targz2')
                
                async with session.post(f"{base_url}/api/must-gather/analyze", data=data) as response:
                    print(f"Upload response status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ TAR.GZ upload successful")
                        print(f"   - Status: {result.get('status')}")
                        print(f"   - Issues found: {result.get('analysis', {}).get('issues_count', 0)}")
                    else:
                        error_text = await response.text()
                        print(f"❌ TAR.GZ upload failed: {response.status}")
                        print(f"   Error: {error_text}")

if __name__ == "__main__":
    print("🧪 Testing .tar.gz File Handling")
    print("=" * 50)
    
    asyncio.run(test_targz_specific())
    
    print("\n" + "=" * 50)
    print("✅ .tar.gz test completed!")
