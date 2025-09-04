#!/usr/bin/env python3
"""
Test script for Must-Gather Analysis functionality
"""

import os
import tempfile
import zipfile
from pathlib import Path
from app.services.must_gather_agent import MustGatherAgent

def create_sample_must_gather():
    """Create a sample must-gather structure for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample cluster version file
        cluster_version_dir = Path(temp_dir) / "cluster-scoped-resources" / "config.openshift.io"
        cluster_version_dir.mkdir(parents=True, exist_ok=True)
        
        cluster_version_content = """
apiVersion: config.openshift.io/v1
kind: ClusterVersion
metadata:
  name: version
spec:
  channel: stable-4.20
status:
  desired:
    version: 4.20.0-0.nightly-2025-07-31-063120
"""
        
        with open(cluster_version_dir / "clusterversions.yaml", "w") as f:
            f.write(cluster_version_content)
        
        # Create sample node directories
        nodes_dir = Path(temp_dir) / "hosts"
        nodes_dir.mkdir(parents=True, exist_ok=True)
        
        # Create master node
        master_dir = nodes_dir / "master-0"
        master_dir.mkdir()
        etcd_dir = master_dir / "etcd"
        etcd_dir.mkdir()
        
        # Create sample etcd logs with issues
        etcd_log_content = """
2025-08-11T15:30:00Z ERROR rejected stream from remote peer because it was removed
2025-08-11T15:30:01Z ERROR raft communication failed between members
2025-08-11T15:30:02Z ERROR etcd timeout connecting to peer 10.200.213.74:2380
2025-08-11T15:30:03Z ERROR connection refused to etcd peer 10.200.213.73:2380
"""
        
        with open(etcd_dir / "etcd.log", "w") as f:
            f.write(etcd_log_content)
        
        # Create sample API server logs
        api_dir = master_dir / "openshift-apiserver"
        api_dir.mkdir()
        
        api_log_content = """
2025-08-11T15:30:00Z ERROR 503 server is currently unable to handle the request
2025-08-11T15:30:01Z ERROR openshift-apiserver failed to start
2025-08-11T15:30:02Z ERROR API timeout connecting to etcd
2025-08-11T15:30:03Z ERROR connection refused to API server
"""
        
        with open(api_dir / "apiserver.log", "w") as f:
            f.write(api_log_content)
        
        # Create sample network logs
        network_dir = master_dir / "network"
        network_dir.mkdir()
        
        network_log_content = """
2025-08-11T15:30:00Z ERROR dial tcp 10.200.213.74:2380: i/o timeout
2025-08-11T15:30:01Z ERROR connection refused to 10.232.143.215:50051
2025-08-11T15:30:02Z ERROR network unreachable to 10.200.213.28:443
2025-08-11T15:30:03Z ERROR i/o timeout connecting to cluster services
"""
        
        with open(network_dir / "network.log", "w") as f:
            f.write(network_log_content)
        
        # Create sample operator logs
        operator_dir = master_dir / "operators"
        operator_dir.mkdir()
        
        operator_log_content = """
2025-08-11T15:30:00Z ERROR cluster operator openshift-apiserver not available
2025-08-11T15:30:01Z ERROR operator authentication failed to start
2025-08-11T15:30:02Z ERROR degraded operator console showing issues
2025-08-11T15:30:03Z ERROR operator monitoring not responding
"""
        
        with open(operator_dir / "operators.log", "w") as f:
            f.write(operator_log_content)
        
        # Create a ZIP file
        zip_path = Path(temp_dir).parent / "sample_must_gather.zip"
        print(f"   Creating ZIP: {zip_path}")
        print(f"   Files to include:")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)
                    print(f"     - {arcname}")
        
        print(f"   ZIP created with {len(zipf.namelist())} files")
        
        return str(zip_path)

async def test_must_gather_analysis():
    """Test the must-gather analysis functionality"""
    print("🔍 Testing Must-Gather Analysis")
    print("=" * 50)
    
    # Create sample must-gather
    print("📦 Creating sample must-gather data...")
    sample_zip = create_sample_must_gather()
    print(f"✅ Created sample must-gather: {sample_zip}")
    
    # Initialize the agent
    print("\n🤖 Initializing Must-Gather Agent...")
    agent = MustGatherAgent()
    print("✅ Agent initialized")
    
    # Extract and analyze
    print("\n🔍 Extracting and analyzing must-gather logs...")
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract the ZIP
        with zipfile.ZipFile(sample_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Use the root directory as the must-gather path
        extract_path = temp_dir
        print(f"   Extracted to: {temp_dir}")
        print(f"   Contents: {os.listdir(temp_dir)}")
        
        # Check if we have the expected structure
        hosts_dir = os.path.join(temp_dir, "hosts")
        if os.path.exists(hosts_dir):
            print(f"   Found hosts directory: {hosts_dir}")
            print(f"   Hosts contents: {os.listdir(hosts_dir)}")
        
        cluster_scoped_dir = os.path.join(temp_dir, "cluster-scoped-resources")
        if os.path.exists(cluster_scoped_dir):
            print(f"   Found cluster-scoped-resources directory: {cluster_scoped_dir}")
        
        # Analyze
        print(f"   Analyzing path: {extract_path}")
        print(f"   Files found: {len([f for f in Path(extract_path).rglob('*') if f.is_file()])}")
        
        analysis = await agent.analyze_must_gather(extract_path)
        
        # Display results
        print("\n📊 Analysis Results:")
        print("=" * 50)
        
        summary = agent.get_analysis_summary(analysis)
        print(summary)
        
        # Display detailed issues
        print("\n🔍 Detailed Issues Found:")
        print("=" * 50)
        for i, issue in enumerate(analysis.issues, 1):
            print(f"\n{i}. {issue.issue_type.upper()} ({issue.severity})")
            print(f"   Description: {issue.description}")
            print(f"   Affected Components: {', '.join(issue.affected_components)}")
            print(f"   Evidence Count: {len(issue.evidence)}")
            print(f"   Recommendations:")
            for rec in issue.recommendations:
                print(f"     - {rec}")
    
    # Clean up
    os.remove(sample_zip)
    print(f"\n🧹 Cleaned up: {sample_zip}")

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)
    
    import requests
    import json
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/api/must-gather/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test UI endpoint
    try:
        response = requests.get("http://localhost:8000/api/must-gather/ui")
        print(f"✅ UI endpoint: {response.status_code}")
        print(f"   Content length: {len(response.text)} characters")
    except Exception as e:
        print(f"❌ UI endpoint failed: {e}")

if __name__ == "__main__":
    import asyncio
    
    print("🚀 Starting Must-Gather Analysis Tests")
    print("=" * 60)
    
    # Test the analysis functionality
    asyncio.run(test_must_gather_analysis())
    
    # Test API endpoints (if server is running)
    test_api_endpoints()
    
    print("\n✅ All tests completed!")
    print("\n📝 To use the web interface:")
    print("   1. Start the server: python start_optimized.py")
    print("   2. Open: http://localhost:8000/api/must-gather/ui")
    print("   3. Upload a must-gather ZIP file for analysis")
