#!/usr/bin/env python3
"""
Test script for enhanced Must-Gather analysis with structured output
"""

import os
import tempfile
import tarfile
import asyncio
import aiohttp
import json

async def test_enhanced_analysis():
    """Test the enhanced structured analysis"""
    
    print("🧪 Testing Enhanced Structured Analysis")
    print("=" * 60)
    
    # Create a test TAR.GZ file with realistic must-gather content
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create must-gather structure
        cluster_dir = os.path.join(temp_dir, "cluster-scoped-resources")
        hosts_dir = os.path.join(temp_dir, "hosts")
        namespaces_dir = os.path.join(temp_dir, "namespaces")
        
        os.makedirs(cluster_dir, exist_ok=True)
        os.makedirs(hosts_dir, exist_ok=True)
        os.makedirs(namespaces_dir, exist_ok=True)
        
        # Create realistic log files with specific issues
        with open(os.path.join(cluster_dir, "etcd.log"), "w") as f:
            f.write("2024-01-01 10:00:00 ERROR: rejected stream from remote peer because it was removed\n")
            f.write("2024-01-01 10:01:00 ERROR: raft communication timeout\n")
            f.write("2024-01-01 10:02:00 ERROR: etcd connection failed\n")
            f.write("2024-01-01 10:03:00 ERROR: etcdserver: no leader\n")
        
        with open(os.path.join(hosts_dir, "apiserver.log"), "w") as f:
            f.write("2024-01-01 10:00:00 ERROR: 503 server is currently unable to handle the request\n")
            f.write("2024-01-01 10:01:00 ERROR: openshift-apiserver failed to start\n")
            f.write("2024-01-01 10:02:00 ERROR: API timeout occurred\n")
            f.write("2024-01-01 10:03:00 ERROR: authentication service unavailable\n")
        
        with open(os.path.join(hosts_dir, "network.log"), "w") as f:
            f.write("2024-01-01 10:00:00 ERROR: dial tcp 10.200.213.74:2380: i/o timeout\n")
            f.write("2024-01-01 10:01:00 ERROR: connection refused\n")
            f.write("2024-01-01 10:02:00 ERROR: network unreachable\n")
            f.write("2024-01-01 10:03:00 ERROR: DNS lookup failed\n")
        
        with open(os.path.join(namespaces_dir, "operators.log"), "w") as f:
            f.write("2024-01-01 10:00:00 ERROR: cluster operator openshift-apiserver not available\n")
            f.write("2024-01-01 10:01:00 ERROR: operator authentication failed\n")
            f.write("2024-01-01 10:02:00 ERROR: degraded operator console\n")
            f.write("2024-01-01 10:03:00 ERROR: operator monitoring degraded\n")
        
        # Create TAR.GZ file
        tar_gz_path = os.path.join(temp_dir, "structured_analysis_test.tar.gz")
        with tarfile.open(tar_gz_path, "w:gz") as tar:
            tar.add(cluster_dir, arcname="cluster-scoped-resources")
            tar.add(hosts_dir, arcname="hosts")
            tar.add(namespaces_dir, arcname="namespaces")
        
        print(f"✅ Created test TAR.GZ file: {tar_gz_path}")
        print(f"   File size: {os.path.getsize(tar_gz_path)} bytes")
        
        # Test upload and analysis
        async with aiohttp.ClientSession() as session:
            base_url = "http://127.0.0.1:8000"
            
            print(f"\n📤 Uploading file for enhanced analysis...")
            
            with open(tar_gz_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('must_gather_file', f, filename='structured_analysis_test.tar.gz')
                data.add_field('cluster_name', 'test-cluster-structured')
                
                async with session.post(f"{base_url}/api/must-gather/analyze", data=data) as response:
                    print(f"Upload response status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Enhanced structured analysis successful!")
                        
                        # Display enhanced analysis results
                        analysis = result.get('analysis', {})
                        print(f"\n🎯 ENHANCED ANALYSIS RESULTS:")
                        print("=" * 60)
                        
                        # Primary Issue
                        print(f"\n🔍 PRIMARY ISSUE:")
                        print(f"   {analysis.get('summary', 'N/A')}")
                        
                        # Root Cause
                        print(f"\n🔧 ROOT CAUSE:")
                        print(f"   {analysis.get('root_cause', 'N/A')}")
                        
                        # Immediate Actions
                        print(f"\n⚡ IMMEDIATE ACTIONS REQUIRED:")
                        for i, action in enumerate(analysis.get('immediate_actions', []), 1):
                            print(f"   {i}. {action}")
                        
                        # Next Steps
                        print(f"\n📋 NEXT STEPS:")
                        for i, step in enumerate(analysis.get('next_steps', []), 1):
                            print(f"   {i}. {step}")
                        
                        # Issues Found
                        print(f"\n📊 ISSUES FOUND ({analysis.get('issues_count', 0)}):")
                        for issue in analysis.get('issues', [])[:5]:  # Show first 5
                            severity_icon = "🔴" if issue.get('severity') == 'critical' else "🟠" if issue.get('severity') == 'high' else "🟡"
                            print(f"   {severity_icon} {issue.get('type', 'Unknown').replace('_', ' ').upper()}")
                            print(f"      Severity: {issue.get('severity', 'Unknown')}")
                            print(f"      Description: {issue.get('description', 'N/A')}")
                            print(f"      Affected: {', '.join(issue.get('affected_components', []))}")
                            print()
                        
                        # Long-term Recommendations
                        print(f"\n🎯 LONG-TERM RECOMMENDATIONS:")
                        for i, rec in enumerate(analysis.get('long_term_recommendations', []), 1):
                            print(f"   {i}. {rec}")
                        
                        # Priority and Metadata
                        print(f"\n📈 ANALYSIS METADATA:")
                        print(f"   Priority: {analysis.get('priority', 'N/A').upper()}")
                        print(f"   Confidence: {analysis.get('confidence', 'N/A')}%")
                        print(f"   Files Analyzed: {analysis.get('files_analyzed', 'N/A')}")
                        
                        if analysis.get('analysis_metadata'):
                            metadata = analysis['analysis_metadata']
                            print(f"   Analysis Time: {metadata.get('analysis_time', 'N/A')}")
                            print(f"   Total Issues: {metadata.get('total_issues', 'N/A')}")
                            print(f"   AI Model Used: {metadata.get('ai_model_used', 'N/A')}")
                            print(f"   Evidence Quality: {metadata.get('confidence_factors', {}).get('evidence_quality', 'N/A')}")
                        
                        print("\n" + "=" * 60)
                        print("✅ Enhanced structured analysis test completed!")
                        print("\n🌐 Access the enhanced UI at:")
                        print("   http://127.0.0.1:8000/api/must-gather/ui")
                        
                    else:
                        error_text = await response.text()
                        print(f"❌ Analysis failed: {response.status}")
                        print(f"   Error: {error_text}")

if __name__ == "__main__":
    print("🚀 Enhanced Structured Analysis Test")
    print("Features being tested:")
    print("✅ Structured analysis format (Primary Issue, Root Cause, Remedy, Next Steps)")
    print("✅ Clear, actionable insights")
    print("✅ Color-coded priority levels")
    print("✅ Evidence-based recommendations")
    print("✅ Professional SRE-style analysis")
    print("=" * 60)
    
    asyncio.run(test_enhanced_analysis())
