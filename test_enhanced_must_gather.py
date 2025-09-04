#!/usr/bin/env python3
"""
Test script for enhanced Must-Gather features:
- Chat functionality with AI model selection
- Evidence and log display
- Analysis confidence metrics
"""

import os
import tempfile
import tarfile
import asyncio
import aiohttp
import json

async def test_enhanced_must_gather():
    """Test enhanced Must-Gather features"""
    
    print("🧪 Testing Enhanced Must-Gather Features")
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
        
        # Create realistic log files with issues
        with open(os.path.join(cluster_dir, "etcd.log"), "w") as f:
            f.write("2024-01-01 10:00:00 ERROR: rejected stream from remote peer because it was removed\n")
            f.write("2024-01-01 10:01:00 ERROR: raft communication timeout\n")
            f.write("2024-01-01 10:02:00 ERROR: etcd connection failed\n")
        
        with open(os.path.join(hosts_dir, "apiserver.log"), "w") as f:
            f.write("2024-01-01 10:00:00 ERROR: 503 server is currently unable to handle the request\n")
            f.write("2024-01-01 10:01:00 ERROR: openshift-apiserver failed to start\n")
            f.write("2024-01-01 10:02:00 ERROR: API timeout occurred\n")
        
        with open(os.path.join(hosts_dir, "network.log"), "w") as f:
            f.write("2024-01-01 10:00:00 ERROR: dial tcp 10.200.213.74:2380: i/o timeout\n")
            f.write("2024-01-01 10:01:00 ERROR: connection refused\n")
            f.write("2024-01-01 10:02:00 ERROR: network unreachable\n")
        
        with open(os.path.join(namespaces_dir, "operators.log"), "w") as f:
            f.write("2024-01-01 10:00:00 ERROR: cluster operator openshift-apiserver not available\n")
            f.write("2024-01-01 10:01:00 ERROR: operator authentication failed\n")
            f.write("2024-01-01 10:02:00 ERROR: degraded operator console\n")
        
        # Create TAR.GZ file
        tar_gz_path = os.path.join(temp_dir, "enhanced_must_gather.tar.gz")
        with tarfile.open(tar_gz_path, "w:gz") as tar:
            tar.add(cluster_dir, arcname="cluster-scoped-resources")
            tar.add(hosts_dir, arcname="hosts")
            tar.add(namespaces_dir, arcname="namespaces")
        
        print(f"✅ Created enhanced test TAR.GZ file: {tar_gz_path}")
        print(f"   File size: {os.path.getsize(tar_gz_path)} bytes")
        
        # Test upload and analysis
        async with aiohttp.ClientSession() as session:
            base_url = "http://127.0.0.1:8000"
            
            print(f"\n📤 Uploading file for analysis...")
            
            with open(tar_gz_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('must_gather_file', f, filename='enhanced_must_gather.tar.gz')
                data.add_field('cluster_name', 'test-cluster-enhanced')
                
                async with session.post(f"{base_url}/api/must-gather/analyze", data=data) as response:
                    print(f"Upload response status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Enhanced analysis successful!")
                        
                        # Display analysis results
                        analysis = result.get('analysis', {})
                        print(f"\n📊 Analysis Results:")
                        print(f"   - Status: {result.get('status')}")
                        print(f"   - Cluster: {result.get('cluster_name')}")
                        print(f"   - Priority: {analysis.get('priority', 'N/A')}")
                        print(f"   - Issues Found: {analysis.get('issues_count', 0)}")
                        print(f"   - Confidence: {analysis.get('confidence', 'N/A')}%")
                        print(f"   - Files Analyzed: {analysis.get('files_analyzed', 'N/A')}")
                        
                        # Display evidence
                        if analysis.get('log_evidence'):
                            print(f"\n🔍 Log Evidence Found:")
                            for i, evidence in enumerate(analysis['log_evidence'][:3], 1):
                                print(f"   {i}. {evidence.get('source', 'Unknown')}: {evidence.get('message', 'N/A')[:80]}...")
                        
                        # Display metadata
                        if analysis.get('analysis_metadata'):
                            metadata = analysis['analysis_metadata']
                            print(f"\n📈 Analysis Metadata:")
                            print(f"   - Analysis Time: {metadata.get('analysis_time', 'N/A')}")
                            print(f"   - Total Issues: {metadata.get('total_issues', 'N/A')}")
                            print(f"   - AI Model Used: {metadata.get('ai_model_used', 'N/A')}")
                            print(f"   - Evidence Quality: {metadata.get('confidence_factors', {}).get('evidence_quality', 'N/A')}")
                        
                        # Test chat functionality
                        print(f"\n💬 Testing Chat Functionality...")
                        await test_chat_functionality(session, base_url, result)
                        
                    else:
                        error_text = await response.text()
                        print(f"❌ Analysis failed: {response.status}")
                        print(f"   Error: {error_text}")

async def test_chat_functionality(session, base_url, analysis_result):
    """Test the chat functionality with different AI models"""
    
    test_questions = [
        "Why did this issue occur?",
        "What are the root causes?",
        "How to fix this?",
        "Show me the evidence from logs"
    ]
    
    ai_models = ["gemini", "granite", "ollama"]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n   Question {i}: {question}")
        
        for model in ai_models:
            try:
                chat_data = {
                    "message": question,
                    "context": "must-gather-analysis",
                    "model": model,
                    "analysis_data": analysis_result
                }
                
                async with session.post(f"{base_url}/api/agent/chat", json=chat_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"     🤖 {model.upper()}: {result.get('response', 'No response')[:100]}...")
                    else:
                        print(f"     ❌ {model.upper()}: Failed ({response.status})")
                        
            except Exception as e:
                print(f"     ❌ {model.upper()}: Error - {e}")
        
        # Only test first question to avoid spam
        if i == 1:
            break

if __name__ == "__main__":
    print("🚀 Enhanced Must-Gather Test Suite")
    print("Features being tested:")
    print("✅ File upload (.tar.gz support)")
    print("✅ AI-powered analysis")
    print("✅ Evidence and log extraction")
    print("✅ Analysis confidence metrics")
    print("✅ Chat functionality with model selection")
    print("✅ Metadata and analysis details")
    print("=" * 60)
    
    asyncio.run(test_enhanced_must_gather())
    
    print("\n" + "=" * 60)
    print("✅ Enhanced Must-Gather test completed!")
    print("\n🌐 Access the enhanced UI at:")
    print("   http://127.0.0.1:8000/api/must-gather/ui")
    print("\n💡 Features available:")
    print("   • Upload .tar.gz files")
    print("   • View detailed analysis with evidence")
    print("   • Chat with AI about the analysis")
    print("   • Choose between Gemini, Granite, or Ollama models")
    print("   • View confidence metrics and log evidence")
