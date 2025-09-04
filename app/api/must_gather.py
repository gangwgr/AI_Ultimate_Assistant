from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from typing import Optional
import os
import tempfile
import shutil
import zipfile
import tarfile
from pathlib import Path
import logging
from app.services.must_gather_agent import MustGatherAgent, MustGatherAnalysis

logger = logging.getLogger(__name__)

must_gather_router = APIRouter(prefix="/api/must-gather", tags=["must-gather"])

# Global instance of the agent
must_gather_agent = MustGatherAgent()

@must_gather_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "must-gather-analyzer"}

@must_gather_router.post("/analyze")
async def analyze_must_gather(
    must_gather_file: UploadFile = File(...),
    cluster_name: Optional[str] = Form(None),
    model_preference: Optional[str] = Form("ollama")
):
    """
    Analyze must-gather logs from uploaded file
    """
    try:
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Processing must-gather file: {must_gather_file.filename}")
            
            # Save uploaded file
            file_path = os.path.join(temp_dir, must_gather_file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(must_gather_file.file, buffer)
            
            # Extract if it's an archive file
            extract_path = temp_dir
            lower_name = must_gather_file.filename.lower()
            if lower_name.endswith('.zip'):
                extract_path = os.path.join(temp_dir, "extracted")
                os.makedirs(extract_path, exist_ok=True)
                
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                # Find the must-gather directory
                for item in os.listdir(extract_path):
                    item_path = os.path.join(extract_path, item)
                    if os.path.isdir(item_path):
                        extract_path = item_path
                        break
            elif lower_name.endswith('.tar') or lower_name.endswith('.tar.gz') or lower_name.endswith('.tgz') or lower_name.endswith('.tar.bz2'):
                extract_path = os.path.join(temp_dir, "extracted")
                os.makedirs(extract_path, exist_ok=True)
                
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_path)
                
                # Find the must-gather directory
                for item in os.listdir(extract_path):
                    item_path = os.path.join(extract_path, item)
                    if os.path.isdir(item_path):
                        extract_path = item_path
                        break
            
            # Analyze the must-gather logs
            analysis = await must_gather_agent.analyze_must_gather(extract_path, model_preference)
            
            # Prepare response
            response = {
                "status": "success",
                "cluster_name": cluster_name or "Unknown",
                "analysis": {
                    "summary": analysis.summary,
                    "root_cause": analysis.root_cause,
                    "priority": analysis.priority,
                    "immediate_actions": analysis.immediate_actions,
                    "long_term_recommendations": analysis.long_term_recommendations,
                    "next_steps": analysis.next_steps,
                    "issues_count": len(analysis.issues),
                    "issues": [
                        {
                            "type": issue.issue_type,
                            "severity": issue.severity,
                            "description": issue.description,
                            "affected_components": issue.affected_components,
                            "recommendations": issue.recommendations,
                            "evidence_count": len(issue.evidence),
                            "evidence": issue.evidence[:3]  # Include first 3 evidence items
                        }
                        for issue in analysis.issues
                    ],
                    "log_evidence": analysis.log_evidence or [],
                    "analysis_metadata": analysis.analysis_metadata or {},
                    "confidence": getattr(analysis, 'confidence', 85),
                    "files_analyzed": getattr(analysis, 'files_analyzed', 'Multiple log files')
                }
            }
            
            return response
        
    except Exception as e:
        logger.error(f"Error analyzing must-gather: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@must_gather_router.post("/analyze-path")
async def analyze_must_gather_path(
    must_gather_path: str = Form(...),
    cluster_name: Optional[str] = Form(None),
    model_preference: Optional[str] = Form("ollama")
):
    """
    Analyze must-gather logs from a local path
    """
    try:
        logger.info(f"Analyzing must-gather from path: {must_gather_path}")
        
        # Analyze the must-gather logs
        analysis = await must_gather_agent.analyze_must_gather(must_gather_path, model_preference)
        
        # Prepare response
        response = {
            "status": "success",
            "cluster_name": cluster_name or "Unknown",
            "path": must_gather_path,
            "analysis": {
                "summary": analysis.summary,
                "root_cause": analysis.root_cause,
                "priority": analysis.priority,
                "immediate_actions": analysis.immediate_actions,
                "long_term_recommendations": analysis.long_term_recommendations,
                "next_steps": analysis.next_steps,
                "issues_count": len(analysis.issues),
                "issues": [
                    {
                        "type": issue.issue_type,
                        "severity": issue.severity,
                        "description": issue.description,
                        "affected_components": issue.affected_components,
                        "recommendations": issue.recommendations,
                        "evidence_count": len(issue.evidence),
                        "evidence": issue.evidence[:3]  # Include first 3 evidence items
                    }
                    for issue in analysis.issues
                ],
                "log_evidence": analysis.log_evidence or [],
                "analysis_metadata": analysis.analysis_metadata or {},
                "confidence": getattr(analysis, 'confidence', 85),
                "files_analyzed": getattr(analysis, 'files_analyzed', 'Multiple log files')
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing must-gather path: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@must_gather_router.get("/summary")
async def get_analysis_summary(analysis_id: str):
    """
    Get a formatted summary of a previous analysis
    """
    # This would typically retrieve from a database
    # For now, return a placeholder
    return {
        "status": "not_implemented",
        "message": "Analysis summary retrieval not yet implemented"
    }

@must_gather_router.post("/chat")
async def must_gather_chat(request: dict):
    """
    Chat about must-gather analysis results
    """
    try:
        from app.services.ai_agent_multi_model import MultiModelAIAgent, ModelType
        
        message = request.get("message", "")
        model_preference = request.get("model", "ollama")
        analysis_data = request.get("analysis_data", {})
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Create AI agent
        ai_agent = MultiModelAIAgent()
        
        # Map model preference to ModelType
        model_mapping = {
            "ollama": ModelType.OLLAMA,
            "claude": ModelType.CLAUDE,
            "gemini": ModelType.GEMINI,
            "openai": ModelType.OPENAI_GPT,
            "granite": ModelType.GRANITE
        }
        
        model_type = model_mapping.get(model_preference, ModelType.OLLAMA)
        
        # Create context with must-gather analysis
        context = {
            'task_type': 'cluster_analysis',
            'context_type': 'must_gather_chat',
            'analysis_data': analysis_data
        }
        
        # Enhance message with analysis context
        enhanced_message = f"""
        You are an expert OpenShift Site Reliability Engineer helping analyze must-gather logs. 
        
        User Question: {message}
        
        Analysis Context:
        {f"Cluster: {analysis_data.get('cluster_name', 'Unknown')}" if analysis_data.get('cluster_name') else ""}
        {f"Issues Found: {analysis_data.get('analysis', {}).get('issues_count', 0)}" if analysis_data.get('analysis') else ""}
        {f"Priority: {analysis_data.get('analysis', {}).get('priority', 'Unknown')}" if analysis_data.get('analysis') else ""}
        
        Recent Issues:
        {chr(10).join([f"- {issue.get('type', '')}: {issue.get('description', '')}" for issue in analysis_data.get('analysis', {}).get('issues', [])[:5]]) if analysis_data.get('analysis', {}).get('issues') else "No issues found"}
        
        Please provide specific, actionable advice based on the OpenShift must-gather analysis data.
        """
        
        # Generate response
        response = await ai_agent.generate_response_with_model(enhanced_message, model_type, context)
        
        # Generate suggestions based on the question
        suggestions = []
        question_lower = message.lower()
        if "operator" in question_lower:
            suggestions = [
                "Check operator status with 'oc get co'",
                "Review operator logs",
                "Verify operator configurations",
                "Check for resource constraints"
            ]
        elif "network" in question_lower:
            suggestions = [
                "Test network connectivity between nodes",
                "Check DNS resolution",
                "Verify load balancer health",
                "Review CNI configuration"
            ]
        elif "etcd" in question_lower:
            suggestions = [
                "Check etcd cluster health",
                "Verify etcd certificates",
                "Review etcd logs for errors",
                "Check disk space and performance"
            ]
        elif "api" in question_lower:
            suggestions = [
                "Check API server logs",
                "Verify certificates",
                "Test API server connectivity",
                "Review authentication configuration"
            ]
        else:
            suggestions = [
                "Review logs for specific error patterns",
                "Check cluster operator status",
                "Verify node health",
                "Examine recent events"
            ]
        
        return {
            "response": response,
            "suggestions": suggestions,
            "model_used": model_preference
        }
        
    except Exception as e:
        logger.error(f"Error in must-gather chat: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@must_gather_router.get("/ui", response_class=HTMLResponse)
async def get_must_gather_ui():
    """
    Serve the must-gather analysis UI
    """
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenShift Must-Gather Analyzer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .terminal {
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Courier New', monospace;
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            white-space: pre-wrap;
        }
        .loading {
            display: none;
        }
        .loading.show {
            display: block;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="max-w-4xl mx-auto">
            <h1 class="text-3xl font-bold text-gray-800 mb-8 text-center">
                🔍 OpenShift Must-Gather Analyzer
            </h1>
            
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h2 class="text-xl font-semibold mb-4">Upload Must-Gather Logs</h2>
                
                <form id="uploadForm" class="space-y-4">
                    <div>
                        <label for="clusterName" class="block text-sm font-medium text-gray-700 mb-2">
                            Cluster Name (Optional)
                        </label>
                        <input type="text" id="clusterName" name="clusterName" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                               placeholder="Enter cluster name">
                    </div>
                    
                    <div>
                        <label for="analysisModel" class="block text-sm font-medium text-gray-700 mb-2">
                            🧠 AI Model for Analysis
                        </label>
                        <select id="analysisModel" name="analysisModel" 
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="ollama">🏠 Local Models (Private & Fast) - Recommended</option>
                            <option value="claude">🧠 Claude (Anthropic) - Expert Analysis</option>
                            <option value="gemini">🔍 Gemini (Google) - Advanced</option>
                            <option value="openai">🧠 OpenAI GPT - High Quality</option>
                            <option value="granite">💎 Granite (IBM) - Enterprise</option>
                        </select>
                        <p class="text-sm text-gray-500 mt-1">Local models analyze data privately on your machine</p>
                    </div>
                    
                    <div>
                        <label for="mustGatherFile" class="block text-sm font-medium text-gray-700 mb-2">
                            Must-Gather File (ZIP/TAR)
                        </label>
                        <input type="file" id="mustGatherFile" name="mustGatherFile" accept=".zip,.tar,.gz,.tgz,.bz2"
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                               onchange="validateAndLogFileSelection()">
                        <p class="text-sm text-gray-500 mt-1">Upload a must-gather archive (.zip, .tar, .tar.gz, .tgz) for analysis</p>
                    </div>
                    
                    <button type="submit" 
                            class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        🔍 Analyze Must-Gather Logs
                    </button>
                </form>
            </div>
            
            <div id="loading" class="loading bg-white rounded-lg shadow-lg p-6 mb-8">
                <div class="flex items-center justify-center">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span class="ml-3 text-lg">Analyzing must-gather logs...</span>
                </div>
            </div>
            
            <div id="results" class="bg-white rounded-lg shadow-lg p-6 hidden">
                <h2 class="text-xl font-semibold mb-4">Analysis Results</h2>
                
                <div id="analysisContent" class="space-y-6">
                    <!-- Analysis content will be inserted here -->
                </div>
                
                <!-- Chat Section -->
                <div class="mt-8 border-t pt-6">
                    <h3 class="text-lg font-semibold mb-4">💬 Discuss Analysis & Get Insights</h3>
                    
                    <div class="mb-4">
                        <label for="aiModel" class="block text-sm font-medium text-gray-700 mb-2">
                            Choose AI Model:
                        </label>
                        <select id="aiModel" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="ollama">🏠 Local Models (Private & Fast) - Recommended</option>
                            <option value="claude">🧠 Claude (Anthropic) - Expert Analysis</option>
                            <option value="gemini">🔍 Gemini 2.0 Flash</option>
                            <option value="openai">🧠 OpenAI GPT</option>
                            <option value="granite">💎 IBM Granite 3.3</option>
                        </select>
                    </div>
                    
                    <div class="mb-4">
                        <label for="chatInput" class="block text-sm font-medium text-gray-700 mb-2">
                            Ask about the analysis:
                        </label>
                        <textarea id="chatInput" rows="3" 
                                  placeholder="Ask questions like: 'Why did this issue occur?', 'What are the root causes?', 'How to fix this?', 'Show me the evidence from logs...'"
                                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
                    </div>
                    
                    <button onclick="askAnalysisQuestion()" 
                            class="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500">
                        🤖 Ask AI
                    </button>
                    
                    <div id="chatResponse" class="mt-4 hidden">
                        <!-- Chat responses will appear here -->
                    </div>
                </div>
                
                <!-- Evidence Section -->
                <div class="mt-8 border-t pt-6">
                    <h3 class="text-lg font-semibold mb-4">🔍 Evidence & Logs</h3>
                    <div id="evidenceContent" class="space-y-4">
                        <!-- Evidence content will be inserted here -->
                    </div>
                </div>
            </div>
            
            <div id="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded hidden">
                <!-- Error messages will be inserted here -->
            </div>
        </div>
    </div>

    <script>
        // Add debugging
        console.log('Must-gather UI loaded');
        
        function validateAndLogFileSelection() {
            const fileInput = document.getElementById('mustGatherFile');
            const status = document.getElementById('error');
            
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const fileName = file.name.toLowerCase();
                
                console.log('File selected:', {
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    lastModified: new Date(file.lastModified).toLocaleString()
                });
                
                // Validate file extension
                const validExtensions = ['.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2'];
                const isValidFile = validExtensions.some(ext => fileName.endsWith(ext));
                
                if (isValidFile) {
                    status.innerHTML = `
                        <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
                            ✅ File selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)
                            <br><small>Extension: ${fileName.split('.').slice(-2).join('.')}</small>
                        </div>
                    `;
                    status.classList.remove('hidden');
                } else {
                    status.innerHTML = `
                        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                            ❌ Invalid file type: ${file.name}
                            <br><small>Supported formats: .zip, .tar, .tar.gz, .tgz, .tar.bz2</small>
                        </div>
                    `;
                    status.classList.remove('hidden');
                    fileInput.value = ''; // Clear the selection
                }
            } else {
                status.classList.add('hidden');
            }
        }
        
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Form submitted');
            
            const formData = new FormData();
            const fileInput = document.getElementById('mustGatherFile');
            const clusterNameInput = document.getElementById('clusterName');
            const modelInput = document.getElementById('analysisModel');
            
            console.log('File input:', fileInput);
            console.log('Files selected:', fileInput.files.length);
            
            if (!fileInput.files[0]) {
                console.log('No file selected');
                showError('Please select a must-gather file');
                return;
            }
            
            const file = fileInput.files[0];
            const fileName = file.name.toLowerCase();
            
            // Validate file extension before upload
            const validExtensions = ['.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2'];
            const isValidFile = validExtensions.some(ext => fileName.endsWith(ext));
            
            if (!isValidFile) {
                console.log('Invalid file type:', file.name);
                showError(`Invalid file type: ${file.name}. Supported formats: .zip, .tar, .tar.gz, .tgz, .tar.bz2`);
                return;
            }
            console.log('Selected file:', file.name, file.size, file.type);
            
            formData.append('must_gather_file', file);
            if (clusterNameInput.value) {
                formData.append('cluster_name', clusterNameInput.value);
            }
            formData.append('model_preference', modelInput.value);
            
            // Log FormData contents
            console.log('FormData entries:');
            for (let [key, value] of formData.entries()) {
                console.log(key, value);
            }
            
            showLoading();
            hideResults();
            hideError();
            
            try {
                console.log('Sending request to /api/must-gather/analyze');
                const response = await fetch('/api/must-gather/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);
                
                const result = await response.json();
                console.log('Response data:', result);
                
                if (response.ok) {
                    displayResults(result);
                } else {
                    showError(result.detail || 'Analysis failed');
                }
            } catch (error) {
                console.error('Upload error:', error);
                showError('Network error: ' + error.message);
            } finally {
                hideLoading();
            }
        });
        
        function showLoading() {
            document.getElementById('loading').classList.add('show');
        }
        
        function hideLoading() {
            document.getElementById('loading').classList.remove('show');
        }
        
        function showResults() {
            document.getElementById('results').classList.remove('hidden');
        }
        
        function hideResults() {
            document.getElementById('results').classList.add('hidden');
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
        }
        
        function hideError() {
            document.getElementById('error').classList.add('hidden');
        }
        
        function displayResults(result) {
            const content = document.getElementById('analysisContent');
            const analysis = result.analysis;
            
            content.innerHTML = `
                <div class="border-b pb-4 mb-6">
                    <div class="flex items-center justify-between">
                        <h3 class="text-xl font-bold">Cluster: ${result.cluster_name}</h3>
                        <span class="px-4 py-2 rounded-full text-sm font-bold ${
                            analysis.priority === 'critical' ? 'bg-red-100 text-red-800 border-2 border-red-300' :
                            analysis.priority === 'high' ? 'bg-orange-100 text-orange-800 border-2 border-orange-300' :
                            analysis.priority === 'medium' ? 'bg-yellow-100 text-yellow-800 border-2 border-yellow-300' :
                            'bg-green-100 text-green-800 border-2 border-green-300'
                        }">
                            🚨 Priority: ${analysis.priority.toUpperCase()}
                        </span>
                    </div>
                </div>
                
                <div class="space-y-8">
                    <!-- Primary Issue -->
                    <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
                        <h4 class="text-lg font-bold text-red-800 mb-2">🔍 Primary Issue</h4>
                        <p class="text-red-700 font-medium">${analysis.summary}</p>
                    </div>
                    
                    <!-- Root Cause -->
                    <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
                        <h4 class="text-lg font-bold text-blue-800 mb-2">🔧 Root Cause</h4>
                        <p class="text-blue-700">${analysis.root_cause}</p>
                    </div>
                    
                    <!-- Immediate Actions -->
                    <div class="bg-orange-50 border-l-4 border-orange-500 p-4 rounded-r-lg">
                        <h4 class="text-lg font-bold text-orange-800 mb-2">⚡ Immediate Actions Required</h4>
                        <ul class="list-disc list-inside space-y-2 text-orange-700">
                            ${analysis.immediate_actions.map(action => `<li class="font-medium">${action}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <!-- Next Steps -->
                    <div class="bg-green-50 border-l-4 border-green-500 p-4 rounded-r-lg">
                        <h4 class="text-lg font-bold text-green-800 mb-2">📋 Next Steps</h4>
                        <ol class="list-decimal list-inside space-y-2 text-green-700">
                            ${analysis.next_steps.map((step, index) => `<li class="font-medium">${step}</li>`).join('')}
                        </ol>
                    </div>
                    
                    <!-- Issues Found -->
                    <div class="bg-gray-50 border border-gray-200 p-4 rounded-lg">
                        <h4 class="text-lg font-bold text-gray-800 mb-3">📊 Issues Found (${analysis.issues_count || 0})</h4>
                        <div class="space-y-3 max-h-64 overflow-y-auto">
                            ${analysis.issues.map(issue => `
                                <div class="bg-white border-l-4 ${
                                    issue.severity === 'critical' ? 'border-red-500' :
                                    issue.severity === 'high' ? 'border-orange-500' :
                                    'border-yellow-500'
                                } pl-4 py-2 rounded-r">
                                    <div class="flex items-center justify-between">
                                        <h5 class="font-semibold text-gray-800">${issue.type.replace(/_/g, ' ').toUpperCase()}</h5>
                                        <span class="px-2 py-1 rounded text-xs font-bold ${
                                            issue.severity === 'critical' ? 'bg-red-100 text-red-800' :
                                            issue.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                                            'bg-yellow-100 text-yellow-800'
                                        }">${issue.severity}</span>
                                    </div>
                                    <p class="text-sm text-gray-600 mt-1">${issue.description}</p>
                                    <p class="text-xs text-gray-500 mt-1">Affected: ${issue.affected_components.join(', ')}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <!-- Long-term Recommendations -->
                    <div class="bg-purple-50 border-l-4 border-purple-500 p-4 rounded-r-lg">
                        <h4 class="text-lg font-bold text-purple-800 mb-2">🎯 Long-term Recommendations</h4>
                        <ul class="list-disc list-inside space-y-2 text-purple-700">
                            ${analysis.long_term_recommendations.map(rec => `<li class="font-medium">${rec}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
            
            showResults();
            
            // Store analysis data for chat context
            window.currentAnalysisData = result;
            
            // Display evidence and logs
            displayEvidence(result);
        }
        
        async function askAnalysisQuestion() {
            const chatInput = document.getElementById('chatInput');
            const aiModel = document.getElementById('aiModel');
            const chatResponse = document.getElementById('chatResponse');
            const question = chatInput.value.trim();
            
            if (!question) {
                showError('Please enter a question');
                return;
            }
            
            // Show loading
            chatResponse.innerHTML = `
                <div class="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded">
                    <div class="flex items-center">
                        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                        Thinking...
                    </div>
                </div>
            `;
            chatResponse.classList.remove('hidden');
            
            try {
                const response = await fetch('/api/must-gather/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: question,
                        context: 'must-gather-analysis',
                        model: aiModel.value,
                        analysis_data: window.currentAnalysisData || {}
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    chatResponse.innerHTML = `
                        <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
                            <div class="font-semibold mb-2">🤖 AI Response (${aiModel.options[aiModel.selectedIndex].text}):</div>
                            <div class="whitespace-pre-wrap">${result.response}</div>
                            ${result.suggestions ? `
                                <div class="mt-3">
                                    <div class="font-semibold">💡 Suggestions:</div>
                                    <ul class="list-disc list-inside mt-1">
                                        ${result.suggestions.map(s => `<li>${s}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    `;
                } else {
                    chatResponse.innerHTML = `
                        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                            Error: ${result.detail || 'Failed to get AI response'}
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Chat error:', error);
                chatResponse.innerHTML = `
                    <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                        Network error: ${error.message}
                    </div>
                `;
            }
        }
        
        function displayEvidence(result) {
            const evidenceContent = document.getElementById('evidenceContent');
            const analysis = result.analysis;
            
            let evidenceHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold mb-2">📊 Analysis Confidence</h4>
                        <div class="flex items-center">
                            <div class="w-full bg-gray-200 rounded-full h-2 mr-2">
                                <div class="bg-blue-600 h-2 rounded-full" style="width: ${analysis.confidence || 85}%"></div>
                            </div>
                            <span class="text-sm font-medium">${analysis.confidence || 85}%</span>
                        </div>
                    </div>
                    
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold mb-2">🔍 Files Analyzed</h4>
                        <p class="text-sm text-gray-600">${analysis.files_analyzed || 'Multiple log files'}</p>
                    </div>
                </div>
            `;
            
            // Add log evidence if available
            if (analysis.log_evidence && analysis.log_evidence.length > 0) {
                evidenceHTML += `
                    <div class="mt-4">
                        <h4 class="font-semibold mb-2">📋 Key Log Evidence</h4>
                        <div class="space-y-2 max-h-64 overflow-y-auto">
                            ${analysis.log_evidence.map(log => `
                                <div class="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded-r">
                                    <div class="flex items-center justify-between">
                                        <span class="font-medium text-sm text-yellow-800">${log.source}</span>
                                        <span class="text-xs text-gray-500">${log.timestamp || 'N/A'}</span>
                                    </div>
                                    <pre class="text-xs text-gray-700 mt-1 overflow-x-auto whitespace-pre-wrap">${log.message}</pre>
                                    ${log.severity ? `<span class="inline-block mt-1 px-2 py-1 text-xs rounded bg-${log.severity === 'critical' ? 'red' : log.severity === 'high' ? 'orange' : log.severity === 'medium' ? 'yellow' : 'blue'}-100 text-${log.severity === 'critical' ? 'red' : log.severity === 'high' ? 'orange' : log.severity === 'medium' ? 'yellow' : 'blue'}-800">${log.severity.toUpperCase()}</span>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            // Add evidence from individual issues
            const issuesWithEvidence = analysis.issues ? analysis.issues.filter(issue => issue.evidence && issue.evidence.length > 0) : [];
            if (issuesWithEvidence.length > 0) {
                evidenceHTML += `
                    <div class="mt-4">
                        <h4 class="font-semibold mb-2">🔍 Issue-Specific Evidence</h4>
                        <div class="space-y-3 max-h-64 overflow-y-auto">
                            ${issuesWithEvidence.slice(0, 5).map(issue => `
                                <div class="bg-gray-50 border rounded p-3">
                                    <div class="flex items-center justify-between mb-2">
                                        <span class="font-medium text-sm">${issue.type.replace(/_/g, ' ').toUpperCase()}</span>
                                        <span class="inline-block px-2 py-1 text-xs rounded bg-${issue.severity === 'critical' ? 'red' : issue.severity === 'high' ? 'orange' : issue.severity === 'medium' ? 'yellow' : 'blue'}-100 text-${issue.severity === 'critical' ? 'red' : issue.severity === 'high' ? 'orange' : issue.severity === 'medium' ? 'yellow' : 'blue'}-800">${issue.severity.toUpperCase()}</span>
                                    </div>
                                    <div class="text-xs text-gray-600 mb-2">${issue.description}</div>
                                    <div class="space-y-1">
                                        ${issue.evidence.slice(0, 2).map(evidence => `
                                            <div class="bg-white border-l-2 border-gray-300 p-2 text-xs">
                                                <pre class="whitespace-pre-wrap text-gray-700">${evidence}</pre>
                                            </div>
                                        `).join('')}
                                        ${issue.evidence.length > 2 ? `<div class="text-xs text-gray-500 italic">... and ${issue.evidence.length - 2} more evidence entries</div>` : ''}
                                    </div>
                                </div>
                            `).join('')}
                            ${issuesWithEvidence.length > 5 ? `<div class="text-sm text-gray-500 italic text-center p-2">... and ${issuesWithEvidence.length - 5} more issues with evidence</div>` : ''}
                        </div>
                    </div>
                `;
            }
            
            // Add cluster information
            if (analysis.cluster_info) {
                evidenceHTML += `
                    <div class="mt-4">
                        <h4 class="font-semibold mb-2">🏗️ Cluster Information</h4>
                        <div class="bg-blue-50 p-3 rounded">
                            <div class="grid grid-cols-2 gap-2 text-sm">
                                <div><strong>Version:</strong> ${analysis.cluster_info.version || 'N/A'}</div>
                                <div><strong>Platform:</strong> ${analysis.cluster_info.platform || 'N/A'}</div>
                                <div><strong>Nodes:</strong> ${analysis.cluster_info.node_count || 'N/A'}</div>
                                <div><strong>Status:</strong> ${analysis.cluster_info.status || 'N/A'}</div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Add analysis metadata
            const metadata = analysis.analysis_metadata || {};
            evidenceHTML += `
                <div class="mt-4">
                    <h4 class="font-semibold mb-2">📈 Analysis Details</h4>
                    <div class="bg-gray-50 p-3 rounded text-sm">
                        <div class="grid grid-cols-2 gap-2">
                            <div><strong>Analysis Time:</strong> ${metadata.analysis_time ? new Date(metadata.analysis_time).toLocaleString() : new Date().toLocaleString()}</div>
                            <div><strong>Issues Found:</strong> ${analysis.issues_count || 0}</div>
                            <div><strong>Priority:</strong> ${analysis.priority || 'medium'}</div>
                            <div><strong>Model Used:</strong> ${metadata.ai_model_used || 'Multi-Model AI'}</div>
                        </div>
                    </div>
                </div>
            `;
            
            evidenceContent.innerHTML = evidenceHTML;
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content) 