#!/usr/bin/env python3
"""
Test script to simulate browser file upload to the must-gather GUI
"""

import os
import tempfile
import tarfile
import asyncio
import aiohttp
import json

async def test_gui_upload():
    """Test file upload through the GUI endpoint"""
    
    # Create a test TAR file
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
        
        # Create TAR file
        tar_path = os.path.join(temp_dir, "test_must_gather.tar")
        with tarfile.open(tar_path, "w") as tar:
            tar.add(cluster_dir, arcname="cluster-scoped-resources")
            tar.add(hosts_dir, arcname="hosts")
        
        print(f"✅ Created test TAR file: {tar_path}")
        
        # Test upload through GUI endpoint
        async with aiohttp.ClientSession() as session:
            base_url = "http://127.0.0.1:8000"
            
            # Test 1: Check if GUI is accessible
            print("\n🧪 Testing GUI accessibility...")
            async with session.get(f"{base_url}/api/must-gather/ui") as response:
                if response.status == 200:
                    print("✅ GUI is accessible")
                else:
                    print(f"❌ GUI not accessible: {response.status}")
                    return
            
            # Test 2: Test file upload
            print("\n🧪 Testing file upload...")
            with open(tar_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('must_gather_file', f, filename='test_must_gather.tar')
                data.add_field('cluster_name', 'test-cluster')
                
                async with session.post(f"{base_url}/api/must-gather/analyze", data=data) as response:
                    print(f"Upload response status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ File upload successful")
                        print(f"   - Status: {result.get('status')}")
                        print(f"   - Issues found: {result.get('analysis', {}).get('issues_count', 0)}")
                    else:
                        error_text = await response.text()
                        print(f"❌ File upload failed: {response.status}")
                        print(f"   Error: {error_text}")
            
            # Test 3: Test with different file types
            print("\n🧪 Testing different file types...")
            
            # Create TAR.GZ file
            tar_gz_path = os.path.join(temp_dir, "test_must_gather.tar.gz")
            with tarfile.open(tar_gz_path, "w:gz") as tar:
                tar.add(cluster_dir, arcname="cluster-scoped-resources")
                tar.add(hosts_dir, arcname="hosts")
            
            # Test TAR.GZ upload
            with open(tar_gz_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('must_gather_file', f, filename='test_must_gather.tar.gz')
                data.add_field('cluster_name', 'test-cluster-targz')
                
                async with session.post(f"{base_url}/api/must-gather/analyze", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("✅ TAR.GZ upload successful")
                    else:
                        error_text = await response.text()
                        print(f"❌ TAR.GZ upload failed: {response.status}")

if __name__ == "__main__":
    print("🧪 Testing Must-Gather GUI Upload")
    print("=" * 50)
    
    asyncio.run(test_gui_upload())
    
    print("\n" + "=" * 50)
    print("✅ GUI upload test completed!")
    print("\nTo test manually:")
    print("1. Open browser and go to: http://127.0.0.1:8000/api/must-gather/ui")
    print("2. Try uploading a TAR/TGZ file")
    print("3. Check browser console for any JavaScript errors")
