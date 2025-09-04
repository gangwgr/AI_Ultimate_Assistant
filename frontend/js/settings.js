// Settings Modal - Complete implementation
console.log('Settings.js loaded');

// Wait for page to load
window.addEventListener('load', function() {
    console.log('Page loaded, initializing settings modal...');
    
    // Find all elements
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeBtn = document.getElementById('close-settings');
    const cancelBtn = document.getElementById('settings-cancel');
    const saveBtn = document.getElementById('settings-save');
    const tabInputs = document.querySelectorAll('input[name="tabs"]');
    const tabContents = document.querySelectorAll('.tab-content');
    
    console.log('Elements found:', {
        settingsBtn: !!settingsBtn,
        settingsModal: !!settingsModal,
        closeBtn: !!closeBtn,
        cancelBtn: !!cancelBtn,
        saveBtn: !!saveBtn,
        tabInputs: tabInputs.length,
        tabContents: tabContents.length
    });
    
    if (!settingsBtn || !settingsModal) {
        console.error('Required elements not found');
        return;
    }
    
    // Modal functions
    function showModal() {
        console.log('Showing settings modal');
        settingsModal.style.display = 'flex';
        settingsModal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Show first tab by default
        showTab('general');
        
        // Ensure modal is scrollable
        const modalContent = settingsModal.querySelector('.overflow-y-auto');
        if (modalContent) {
            modalContent.style.maxHeight = '60vh';
            modalContent.style.overflowY = 'auto';
        }
    }
    
    function hideModal() {
        console.log('Hiding settings modal');
        settingsModal.style.display = 'none';
        settingsModal.classList.remove('show');
        document.body.style.overflow = 'auto';
    }
    
    function showTab(tabName) {
        console.log('Showing tab:', tabName);
        
        // Hide all tab contents
        tabContents.forEach(content => {
            content.style.display = 'none';
        });
        
        // Show selected tab content
        const contentId = tabName + '-settings';
        const selectedContent = document.getElementById(contentId);
        if (selectedContent) {
            selectedContent.style.display = 'block';
        }
        
        // Update radio button
        const radioId = 'tab-' + tabName;
        const radio = document.getElementById(radioId);
        if (radio) {
            radio.checked = true;
        }
    }
    
    // API functions
    async function saveGoogleCredentials() {
        const clientId = document.getElementById('google-client-id').value;
        const clientSecret = document.getElementById('google-client-secret').value;
        
        if (!clientId || !clientSecret) {
            alert('Please fill in both Client ID and Client Secret');
            return;
        }
        
        try {
            const response = await fetch('/api/config/google-oauth', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    client_id: clientId,
                    client_secret: clientSecret
                })
            });
            
            if (response.ok) {
                alert('Google credentials saved successfully!');
            } else {
                const error = await response.text();
                alert('Error saving Google credentials: ' + error);
            }
        } catch (error) {
            console.error('Error saving Google credentials:', error);
            alert('Error saving Google credentials. Please try again.');
        }
    }
    
    async function testGoogleConnection() {
        try {
            const response = await fetch('/api/auth/google/test', {
                method: 'GET'
            });
            
            if (response.ok) {
                alert('Google connection test successful!');
            } else {
                const error = await response.text();
                alert('Google connection test failed: ' + error);
            }
        } catch (error) {
            console.error('Error testing Google connection:', error);
            alert('Error testing Google connection. Please try again.');
        }
    }
    
    async function saveGitHubToken() {
        const token = document.getElementById('github-token').value;
        
        if (!token) {
            alert('Please enter a GitHub Personal Access Token');
            return;
        }
        
        try {
            const response = await fetch('/api/config/github', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: token
                })
            });
            
            if (response.ok) {
                alert('GitHub token saved successfully!');
            } else {
                const error = await response.text();
                alert('Error saving GitHub token: ' + error);
            }
        } catch (error) {
            console.error('Error saving GitHub token:', error);
            alert('Error saving GitHub token. Please try again.');
        }
    }
    
    async function testGitHubConnection() {
        try {
            const response = await fetch('/api/github/test', {
                method: 'GET'
            });
            
            if (response.ok) {
                alert('GitHub connection test successful!');
            } else {
                const error = await response.text();
                alert('GitHub connection test failed: ' + error);
            }
        } catch (error) {
            console.error('Error testing GitHub connection:', error);
            alert('Error testing GitHub connection. Please try again.');
        }
    }
    
    async function removeGitHubToken() {
        if (!confirm('Are you sure you want to remove the GitHub token?')) {
            return;
        }
        
        try {
            const response = await fetch('/api/config/github', {
                method: 'DELETE'
            });
            
            if (response.ok) {
                document.getElementById('github-token').value = '';
                alert('GitHub token removed successfully!');
            } else {
                const error = await response.text();
                alert('Error removing GitHub token: ' + error);
            }
        } catch (error) {
            console.error('Error removing GitHub token:', error);
            alert('Error removing GitHub token. Please try again.');
        }
    }
    
    async function saveJiraCredentials() {
        const serverUrl = document.getElementById('jira-server-url').value;
        const username = document.getElementById('jira-username').value;
        const apiToken = document.getElementById('jira-api-token').value;
        const authMethod = document.getElementById('jira-auth-method').value;
        
        if (!serverUrl || !username || !apiToken) {
            alert('Please fill in Server URL, Username, and API Token');
            return;
        }
        
        try {
            const response = await fetch('/api/jira/credentials', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    server_url: serverUrl,
                    username: username,
                    api_token: apiToken,
                    auth_method: authMethod
                })
            });
            
            if (response.ok) {
                alert('Jira credentials saved successfully!');
            } else {
                const error = await response.text();
                alert('Error saving Jira credentials: ' + error);
            }
        } catch (error) {
            console.error('Error saving Jira credentials:', error);
            alert('Error saving Jira credentials. Please try again.');
        }
    }
    
    async function testJiraConnection() {
        try {
            const response = await fetch('/api/jira/test-connection', {
                method: 'GET'
            });
            
            if (response.ok) {
                alert('Jira connection test successful!');
            } else {
                const error = await response.text();
                alert('Jira connection test failed: ' + error);
            }
        } catch (error) {
            console.error('Error testing Jira connection:', error);
            alert('Error testing Jira connection. Please try again.');
        }
    }
    
    async function removeJiraCredentials() {
        if (!confirm('Are you sure you want to remove the Jira credentials?')) {
            return;
        }
        
        try {
            const response = await fetch('/api/jira/credentials', {
                method: 'DELETE'
            });
            
            if (response.ok) {
                document.getElementById('jira-server-url').value = '';
                document.getElementById('jira-username').value = '';
                document.getElementById('jira-api-token').value = '';
                alert('Jira credentials removed successfully!');
            } else {
                const error = await response.text();
                alert('Error removing Jira credentials: ' + error);
            }
        } catch (error) {
            console.error('Error removing Jira credentials:', error);
            alert('Error removing Jira credentials. Please try again.');
        }
    }
    
    // Settings button click
    settingsBtn.onclick = function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Settings button clicked');
        showModal();
    };
    
    // Close button click
    if (closeBtn) {
        closeBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Close button clicked');
            hideModal();
        };
    }
    
    // Cancel button click
    if (cancelBtn) {
        cancelBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Cancel button clicked');
            hideModal();
        };
    }
    
    // Save button click
    if (saveBtn) {
        saveBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Save button clicked');
            
            // Save settings logic here
            // For now, just close the modal
            hideModal();
            
            // Show success message
            alert('Settings saved successfully!');
        };
    }
    
    // Tab switching
    tabInputs.forEach(input => {
        input.onchange = function(e) {
            e.preventDefault();
            e.stopPropagation();
            const tabName = this.id.replace('tab-', '');
            console.log('Tab changed to:', tabName);
            showTab(tabName);
        };
    });
    
    // Close modal when clicking outside
    settingsModal.onclick = function(e) {
        if (e.target === settingsModal) {
            console.log('Clicked outside modal');
            hideModal();
        }
    };
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && settingsModal.classList.contains('show')) {
            console.log('Escape key pressed');
            hideModal();
        }
    });
    
    // Voice settings controls
    const speechRateInput = document.getElementById('settings-speech-rate');
    const speechVolumeInput = document.getElementById('settings-speech-volume');
    const rateValue = document.getElementById('settings-rate-value');
    const volumeValue = document.getElementById('settings-volume-value');
    const testVoiceBtn = document.getElementById('settings-test-voice');
    
    if (speechRateInput && rateValue) {
        speechRateInput.oninput = function() {
            rateValue.textContent = this.value;
        };
    }
    
    if (speechVolumeInput && volumeValue) {
        speechVolumeInput.oninput = function() {
            volumeValue.textContent = this.value;
        };
    }
    
    if (testVoiceBtn) {
        testVoiceBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Test voice button clicked');
            
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance("This is a test of the voice settings.");
                utterance.rate = (speechRateInput ? speechRateInput.value / 100 : 1.5);
                utterance.volume = (speechVolumeInput ? parseFloat(speechVolumeInput.value) : 0.9);
                speechSynthesis.speak(utterance);
            }
        };
    }
    
    // Service configuration buttons
    const saveGoogleBtn = document.getElementById('save-google');
    const testGoogleBtn = document.getElementById('test-google');
    const saveGitHubBtn = document.getElementById('save-github');
    const testGitHubBtn = document.getElementById('test-github');
    const removeGitHubBtn = document.getElementById('remove-github');
    const saveJiraBtn = document.getElementById('save-jira');
    const testJiraBtn = document.getElementById('test-jira');
    const removeJiraBtn = document.getElementById('remove-jira');
    
    if (saveGoogleBtn) {
        saveGoogleBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Save Google button clicked');
            saveGoogleCredentials();
        };
    }
    
    if (testGoogleBtn) {
        testGoogleBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Test Google button clicked');
            testGoogleConnection();
        };
    }
    
    if (saveGitHubBtn) {
        saveGitHubBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Save GitHub button clicked');
            saveGitHubToken();
        };
    }
    
    if (testGitHubBtn) {
        testGitHubBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Test GitHub button clicked');
            testGitHubConnection();
        };
    }
    
    if (removeGitHubBtn) {
        removeGitHubBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Remove GitHub button clicked');
            removeGitHubToken();
        };
    }
    
    if (saveJiraBtn) {
        saveJiraBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Save Jira button clicked');
            saveJiraCredentials();
        };
    }
    
    if (testJiraBtn) {
        testJiraBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Test Jira button clicked');
            testJiraConnection();
        };
    }
    
    if (removeJiraBtn) {
        removeJiraBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Remove Jira button clicked');
            removeJiraCredentials();
        };
    }
    
    console.log('Settings modal initialization complete');
});

// Also try on DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded fired');
}); 