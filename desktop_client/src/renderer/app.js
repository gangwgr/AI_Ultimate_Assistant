class AIAssistant {
    constructor() {
        this.websocket = null;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.recognition = null;
        this.voiceResponsesEnabled = false; // Voice responses disabled by default
        this.backendUrl = 'http://localhost:8000';
        this.initializeElements();
        this.setupEventListeners();
        this.connectWebSocket();
        this.setupSpeechRecognition();
        this.checkStatus();
        this.updateUnreadEmailCount(); // Initial call to update badge
        
        // Set up periodic unread email count updates (every 30 seconds)
        setInterval(() => {
            this.updateUnreadEmailCount();
        }, 30000);
    }

    initializeElements() {
        this.chatContainer = document.getElementById('chat-container');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.voiceButton = document.getElementById('voice-button');
        this.voiceToggle = document.getElementById('voice-toggle');
        this.refreshButton = document.getElementById('refresh-status');
        this.testVoiceButton = document.getElementById('test-voice');
        this.speechRateSlider = document.getElementById('speech-rate');
        this.speechVolumeSlider = document.getElementById('speech-volume');
        this.rateValueSpan = document.getElementById('rate-value');
        this.volumeValueSpan = document.getElementById('volume-value');
        this.notificationContainer = document.getElementById('notification-container');
        
        // Notification test buttons
        this.testEmailButton = document.getElementById('test-email-notification');
        this.testCalendarButton = document.getElementById('test-calendar-notification');
        this.testMeetingButton = document.getElementById('test-meeting-reminder');
        
        // Settings modal elements
        this.settingsBtn = document.getElementById('settings-btn');
        this.settingsModal = document.getElementById('settings-modal');
        this.closeSettingsBtn = document.getElementById('close-settings');
        this.settingsCancelBtn = document.getElementById('settings-cancel');
        this.settingsSaveBtn = document.getElementById('settings-save');
        this.aiModelSetting = document.getElementById('ai-model-setting');
        this.testModelBtn = document.getElementById('test-model-btn');
        this.unreadBadge = document.getElementById('unread-badge'); // Add unread badge element
    }
    
    setupEventListeners() {
        // Chat functionality
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Voice functionality
        this.voiceButton.addEventListener('click', () => this.toggleVoiceRecording());
        this.voiceToggle.addEventListener('click', () => this.toggleVoiceResponses());
        this.testVoiceButton.addEventListener('click', () => this.testVoice());
        
        // Voice activation keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+Shift+V to activate voice
            if (e.ctrlKey && e.shiftKey && e.key === 'V') {
                e.preventDefault();
                this.toggleVoiceRecording();
            }
            // Escape to stop voice recording
            if (e.key === 'Escape' && this.isRecording) {
                e.preventDefault();
                this.stopVoiceRecording();
            }
            // Space bar (when input not focused) to activate voice
            if (e.code === 'Space' && document.activeElement !== this.messageInput) {
                e.preventDefault();
                this.toggleVoiceRecording();
            }
        });
        
        // Voice settings
        this.speechRateSlider.addEventListener('input', (e) => {
            this.rateValueSpan.textContent = e.target.value;
        });
        
        this.speechVolumeSlider.addEventListener('input', (e) => {
            this.volumeValueSpan.textContent = e.target.value;
        });
        
        // Status refresh
        this.refreshButton.addEventListener('click', () => this.checkStatus());
        
        // Quick actions
        document.querySelectorAll('.quick-action').forEach(button => {
            button.addEventListener('click', () => {
                const action = button.getAttribute('data-action');
                this.sendMessage(action);
            });
        });
        
        // Suggestions
        document.querySelectorAll('.suggestion').forEach(suggestion => {
            suggestion.addEventListener('click', () => {
                const text = suggestion.getAttribute('data-suggestion');
                this.messageInput.value = text;
                this.sendMessage();
            });
        });
        
        // Notification test buttons
        this.testEmailButton.addEventListener('click', () => this.testNotification('email'));
        this.testCalendarButton.addEventListener('click', () => this.testNotification('calendar'));
        this.testMeetingButton.addEventListener('click', () => this.testNotification('meeting'));
        document.getElementById('check-unread-emails').addEventListener('click', () => this.checkUnreadEmails());
        
        // Notification Service Control
        document.getElementById('restart-notifications').addEventListener('click', () => this.restartNotificationService());
        document.getElementById('check-notification-status').addEventListener('click', () => this.checkNotificationStatus());
        
        // Settings modal functionality
        this.settingsBtn.addEventListener('click', () => this.openSettings());
        this.closeSettingsBtn.addEventListener('click', () => this.closeSettings());
        this.settingsCancelBtn.addEventListener('click', () => this.closeSettings());
        this.settingsSaveBtn.addEventListener('click', () => this.saveSettings());
        
        // Settings tab switching
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchSettingsTab(e.target.dataset.tab));
        });
        
        // Settings voice controls
        document.getElementById('settings-speech-rate').addEventListener('input', (e) => {
            document.getElementById('settings-rate-value').textContent = e.target.value;
        });

        // Model switching
        this.aiModelSetting.addEventListener('change', () => this.changeModel());
        this.testModelBtn.addEventListener('click', () => this.testCurrentModel());
        
        document.getElementById('settings-speech-volume').addEventListener('input', (e) => {
            document.getElementById('settings-volume-value').textContent = e.target.value;
        });
        
        document.getElementById('settings-test-voice').addEventListener('click', () => {
            this.testSettingsVoice();
        });
        
        // Service configuration buttons
        document.getElementById('save-google-creds').addEventListener('click', () => this.saveGoogleCredentials());
        document.getElementById('test-google-connection').addEventListener('click', () => this.testGoogleConnection());
        document.getElementById('save-slack-creds').addEventListener('click', () => this.saveSlackCredentials());
        document.getElementById('test-slack-connection').addEventListener('click', () => this.testSlackConnection());
        
        // Close modal when clicking outside
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) {
                this.closeSettings();
            }
        });
    }

    connectWebSocket() {
        const protocol = this.backendUrl.startsWith('https') ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${this.backendUrl.replace(/^https?:\/\//, '')}/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                // Handle different message types
                if (data.type === 'notification') {
                    // Show in-app notification
                    this.showInAppNotification(
                        data.notification_type, 
                        data.title, 
                        data.message
                    );
                } else {
                    // Handle regular chat responses
                    const response = data.response || data;
                    this.addMessage(response, 'assistant');
                }
            } catch (error) {
                // If it's not JSON, treat as regular message
                const response = JSON.parse(event.data);
                this.addMessage(response.response || response, 'assistant');
            }
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected. Attempting to reconnect...');
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }

    setupSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = navigator.language || 'en-US';
            
            this.recognition.onstart = () => {
                this.isRecording = true;
                this.voiceButton.classList.add('recording');
                this.voiceButton.innerHTML = '<i class="fas fa-stop"></i>';
                this.messageInput.placeholder = 'Listening... Speak now!';
                console.log('🎤 Voice recognition started');
                this.showInAppNotification('🎤 Voice Active', 'Listening... Speak now!', 'info');
            };
            
            this.recognition.onresult = (event) => {
                let finalTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    }
                }
                
                if (finalTranscript) {
                    console.log('🎤 Voice recognized:', finalTranscript);
                    this.messageInput.value = finalTranscript;
                this.sendMessage();
                }
            };
            
            this.recognition.onerror = (event) => {
                console.error('🎤 Voice recognition error:', event.error);
                this.isRecording = false;
                this.voiceButton.classList.remove('recording');
                this.voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
                this.messageInput.placeholder = 'Type your message or press Ctrl+Shift+V for voice...';
                
                let errorMsg = '';
                switch(event.error) {
                    case 'network':
                        errorMsg = '🌐 Network connection issue - Speech recognition requires internet';
                        break;
                    case 'not-allowed':
                        errorMsg = '🚫 Microphone access denied - Please enable microphone permissions';
                        break;
                    case 'no-speech':
                        errorMsg = '🔇 No speech detected - Try speaking more clearly';
                        break;
                    case 'aborted':
                        errorMsg = '⏹️ Voice recognition stopped';
                        break;
                    case 'audio-capture':
                        errorMsg = '🎤 Audio capture failed - Check your microphone';
                        break;
                    case 'service-not-allowed':
                        errorMsg = '🚫 Speech service not allowed';
                        break;
                    default:
                        errorMsg = `❗ Voice error: ${event.error}`;
                }
                
                this.showInAppNotification('Voice Recognition Error', errorMsg, 'error');
                this.addMessage(`🎤 ${errorMsg}. You can continue typing your message normally.`, 'system');
            };
            
            this.recognition.onend = () => {
                this.isRecording = false;
                this.voiceButton.classList.remove('recording');
                this.voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
                this.messageInput.placeholder = 'Type your message or press Ctrl+Shift+V for voice...';
                console.log('🎤 Voice recognition ended');
            };
            
            // Enable voice button and show availability
            this.voiceButton.disabled = false;
            this.voiceButton.title = 'Click or press Ctrl+Shift+V for voice input';
            this.showInAppNotification('🎤 Voice Ready', 'Voice recognition is available! Use Ctrl+Shift+V or click the microphone.', 'success');
        } else {
            // Voice not supported
            console.warn('🎤 Voice recognition not supported');
            this.voiceButton.disabled = true;
            this.voiceButton.title = 'Voice recognition not supported in this environment';
            this.voiceButton.style.opacity = '0.5';
            this.addMessage('🎤 Voice recognition is not supported in this environment. Please use text input.', 'system');
        }
    }
    
    toggleVoiceRecording() {
        if (!this.recognition) {
            this.addMessage('🎤 Voice recognition not supported in this environment', 'system');
            return;
        }
        
        if (this.isRecording) {
            this.recognition.stop();
        } else {
            try {
            this.recognition.start();
            } catch (error) {
                console.error('Error starting voice recognition:', error);
                this.addMessage('🎤 Error starting voice recognition: ' + error.message, 'system');
            }
        }
    }

    sendMessage(text = null) {
        const message = text || this.messageInput.value.trim();
        if (!message) return;
        
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'message',
                content: message
            }));
            } else {
            this.addMessage('❌ Not connected to AI Assistant. Trying to reconnect...', 'system');
            this.connectWebSocket();
        }
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} mb-4`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `message-bubble p-4 rounded-lg max-w-4xl ${
            sender === 'user' ? 'user-message text-white' : 
            sender === 'assistant' ? 'assistant-message text-white' : 
            'bg-gray-200 text-gray-800'
        }`;
        
        // Properly render HTML content and format code blocks
        const contentDiv = document.createElement('div');
        contentDiv.style.cssText = 'white-space: pre-wrap; word-wrap: break-word; line-height: 1.6;';
        
        // Process the content to handle various formatting
        let processedContent = content;
        
        // Handle code blocks with backticks
        processedContent = processedContent.replace(/`([^`]+)`/g, '<code style="background-color: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 3px; font-family: monospace;">$1</code>');
        
        // Handle **bold** text
        processedContent = processedContent.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Convert <br> and <br/> to actual line breaks
        processedContent = processedContent.replace(/<br\s*\/?>/gi, '\n');
        
        contentDiv.innerHTML = processedContent;
        bubbleDiv.appendChild(contentDiv);
        
        messageDiv.appendChild(bubbleDiv);
        this.chatContainer.appendChild(messageDiv);
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }
    
    toggleVoiceResponses() {
        this.voiceResponsesEnabled = !this.voiceResponsesEnabled;
        
        if (this.voiceResponsesEnabled) {
            this.voiceToggle.classList.remove('bg-gray-500');
            this.voiceToggle.classList.add('bg-green-500');
            this.voiceToggle.innerHTML = '<i class="fas fa-volume-up"></i>';
            this.voiceToggle.title = 'Voice responses enabled - Click to disable';
            this.showInAppNotification('success', '🔊 Voice Enabled', 'Assistant will now speak responses aloud');
        } else {
            this.voiceToggle.classList.remove('bg-green-500');
            this.voiceToggle.classList.add('bg-gray-500');
            this.voiceToggle.innerHTML = '<i class="fas fa-volume-mute"></i>';
            this.voiceToggle.title = 'Voice responses disabled - Click to enable';
            this.showInAppNotification('info', '🔇 Voice Disabled', 'Assistant will not speak responses');
        }
    }

    speakMessage(text) {
        // Only speak if voice responses are enabled
        if (this.voiceResponsesEnabled && 'speechSynthesis' in window) {
            // Cancel any ongoing speech
            speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = this.speechRateSlider.value / 100;
            utterance.volume = parseFloat(this.speechVolumeSlider.value);
            utterance.lang = navigator.language || 'en-US';
            
            speechSynthesis.speak(utterance);
        }
    }

    testVoice() {
        const testText = "Hello! This is a test of the AI Assistant voice system. The voice settings are working correctly.";
        this.speakMessage(testText);
    }

    // Custom In-App Notification System
    showInAppNotification(type, title, message) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icons = {
            email: 'fas fa-envelope',
            calendar: 'fas fa-calendar-plus',
            meeting: 'fas fa-clock',
            info: 'fas fa-info-circle',
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-triangle'
        };
        
        notification.innerHTML = `
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
            <div class="flex items-start">
                <i class="${icons[type] || 'fas fa-bell'} text-xl mr-3 mt-1"></i>
                <div>
                    <h4 class="font-bold text-lg">${title}</h4>
                    <p class="text-sm mt-1">${message}</p>
                    <div class="text-xs mt-2 opacity-75">${new Date().toLocaleTimeString()}</div>
                </div>
            </div>
        `;
        
        this.notificationContainer.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.add('slide-out');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    async testNotification(type) {
        try {
            const response = await fetch(`${this.backendUrl}/api/notifications/test/${type}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const result = await response.json();
                this.addMessage(`✅ ${type.charAt(0).toUpperCase() + type.slice(1)} notification test sent!`, 'assistant');
                
                // Show custom in-app notification
                const notifications = {
                    email: {
                        title: '📧 New Email Notification Test',
                        message: 'This is a test email notification from AI Assistant'
                    },
                    calendar: {
                        title: '📅 Calendar Invite Notification Test', 
                        message: 'This is a test calendar notification from AI Assistant'
                    },
                    meeting: {
                        title: '⏰ Meeting Reminder Test',
                        message: 'This is a test meeting reminder from AI Assistant'
                    }
                };
                
                const notif = notifications[type];
                this.showInAppNotification(type, notif.title, notif.message);
            } else {
                this.addMessage(`❌ Failed to send ${type} notification test.`, 'assistant');
            }
        } catch (error) {
            console.error('Error testing notification:', error);
            this.addMessage(`❌ Error testing ${type} notification: ${error.message}`, 'assistant');
        }
    }

    async checkUnreadEmails() {
        try {
            const response = await fetch(`${this.backendUrl}/api/notifications/unread-emails`);
            if (response.ok) {
                const data = await response.json();
                const unreadEmails = data.unread_emails || [];
                const count = data.count || 0;
                
                if (count > 0) {
                    // Format unread emails for display
                    let emailDisplay = `📧 **Found ${count} Unread Email${count > 1 ? 's' : ''}:**\n\n`;
                    
                    unreadEmails.forEach((email, index) => {
                        // Clean sender name
                        let sender = email.sender;
                        if (sender.includes('<') && sender.includes('>')) {
                            sender = sender.split('<')[0].trim().replace(/"/g, '');
                        }
                        
                        emailDisplay += `**${index + 1}. ${email.subject}**\n`;
                        emailDisplay += `From: ${sender}\n`;
                        emailDisplay += `Date: ${email.date}\n`;
                        emailDisplay += `Preview: ${email.snippet}\n\n`;
                        emailDisplay += `${'─'.repeat(50)}\n\n`;
                    });
                    
                    this.addMessage(emailDisplay, 'assistant');
                    this.showInAppNotification('info', '📧 Unread Emails', `Found ${count} unread email${count > 1 ? 's' : ''} in your inbox.`);
                } else {
                    this.addMessage('✅ No unread emails found in your inbox.', 'assistant');
                    this.showInAppNotification('success', '📧 Inbox Clear', 'No unread emails found in your inbox.');
                }
                
                this.updateUnreadEmailCount(); // Update badge after checking
            } else {
                this.addMessage('❌ Failed to fetch unread emails.', 'assistant');
                this.showInAppNotification('error', '📧 Error', 'Failed to fetch unread emails.');
            }
        } catch (error) {
            console.error('Error fetching unread emails:', error);
            this.addMessage('❌ Error fetching unread emails: ' + error.message, 'assistant');
            this.showInAppNotification('error', '📧 Error', 'Error fetching unread emails.');
        }
    }

    async restartNotificationService() {
        try {
            const response = await fetch(`${this.backendUrl}/api/notifications/restart`, {
                method: 'POST'
            });
            const result = await response.json();
            if (response.ok) {
                this.addMessage('✅ Notification service restarted successfully!', 'system');
                this.showInAppNotification('info', 'Notification Service', 'Notification service restarted.');
            } else {
                this.addMessage('❌ Failed to restart notification service: ' + result.message, 'system');
                this.showInAppNotification('error', 'Notification Service', 'Failed to restart notification service.', 'error');
            }
        } catch (error) {
            console.error('Error restarting notification service:', error);
            this.addMessage('❌ Error restarting notification service: ' + error.message, 'system');
            this.showInAppNotification('error', 'Notification Service', 'Error restarting notification service.', 'error');
        }
    }

    async checkNotificationStatus() {
        try {
            const response = await fetch(`${this.backendUrl}/api/notifications/debug-status`);
            const result = await response.json();
            if (response.ok) {
                const statusMessage = `📊 Service Status:\n` +
                    `• Running: ${result.is_running ? '✅ Yes' : '❌ No'}\n` +
                    `• Seen Emails: ${result.seen_emails_count}\n` +
                    `• Gmail Available: ${result.gmail_service_available ? '✅ Yes' : '❌ No'}\n` +
                    `• Last Email Check: ${result.last_email_check ? new Date(result.last_email_check).toLocaleString() : 'Never'}`;
                
                this.addMessage(statusMessage, 'system');
                this.showInAppNotification('info', 'Notification Status', 'Status details added to chat.');
        } else {
                this.addMessage('❌ Failed to check notification status.', 'system');
                this.showInAppNotification('error', 'Notification Status', 'Failed to check notification status.', 'error');
            }
        } catch (error) {
            console.error('Error checking notification status:', error);
            this.addMessage('❌ Error checking notification status: ' + error.message, 'system');
            this.showInAppNotification('error', 'Notification Status', 'Error checking notification status.', 'error');
        }
    }
    
    async checkStatus() {
        try {
            const response = await fetch(`${this.backendUrl}/api/auth/status`);
            if (response.ok) {
                const status = await response.json();
                this.updateStatusDisplay(status);
                this.updateUnreadEmailCount(); // Update unread badge when refreshing status
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }
    
    updateStatusDisplay(status) {
        const services = ['google', 'slack'];
        const elements = {
            google: 'gmail-status',
            slack: 'slack-status'
        };
        
        services.forEach(service => {
            const element = document.getElementById(elements[service]);
            if (element) {
                const connected = status[service];
                const serviceName = service.charAt(0).toUpperCase() + service.slice(1);
                element.textContent = `${serviceName}: ${connected ? 'Connected' : 'Disconnected'}`;
                element.className = `text-sm ${connected ? 'text-green-600' : 'text-red-600'}`;
            }
        });

        // Update calendar and contacts status based on Google connection
        const calendarElement = document.getElementById('calendar-status');
        const contactsElement = document.getElementById('contacts-status');
        
        if (calendarElement) {
            const connected = status.google;
            calendarElement.textContent = `Calendar: ${connected ? 'Connected' : 'Disconnected'}`;
            calendarElement.className = `text-sm ${connected ? 'text-green-600' : 'text-red-600'}`;
        }
        
        if (contactsElement) {
            const connected = status.google;
            contactsElement.textContent = `Contacts: ${connected ? 'Connected' : 'Disconnected'}`;
            contactsElement.className = `text-sm ${connected ? 'text-green-600' : 'text-red-600'}`;
        }
    }

    // Settings Modal Functionality
    openSettings() {
        this.loadCurrentSettings();
        this.settingsModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    closeSettings() {
        this.settingsModal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }

    switchSettingsTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.classList.remove('active', 'border-blue-500', 'text-blue-600');
            tab.classList.add('text-gray-500');
        });
        
        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        activeTab.classList.add('active', 'border-blue-500', 'text-blue-600');
        activeTab.classList.remove('text-gray-500');

        // Update content
        document.querySelectorAll('.settings-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        document.getElementById(`${tabName}-settings`).classList.remove('hidden');
    }

    loadCurrentSettings() {
        // Sync voice settings from main interface
        const mainRate = this.speechRateSlider.value;
        const mainVolume = this.speechVolumeSlider.value;
        
        document.getElementById('settings-speech-rate').value = mainRate;
        document.getElementById('settings-speech-volume').value = mainVolume;
        document.getElementById('settings-rate-value').textContent = mainRate;
        document.getElementById('settings-volume-value').textContent = mainVolume;
        
        // Load other settings from localStorage or defaults
        document.getElementById('backend-url-setting').value = this.backendUrl;
        document.getElementById('theme-setting').value = localStorage.getItem('theme') || 'auto';
        document.getElementById('ai-model-setting').value = localStorage.getItem('aiModel') || 'granite';
        document.getElementById('language-setting').value = localStorage.getItem('language') || 'en-US';
        
        // Load desktop settings
        document.getElementById('auto-launch-setting').checked = localStorage.getItem('autoLaunch') === 'true';
        document.getElementById('notifications-setting').checked = localStorage.getItem('notifications') !== 'false';
        document.getElementById('minimize-tray-setting').checked = localStorage.getItem('minimizeToTray') === 'true';
        document.getElementById('auto-hide-menu-setting').checked = localStorage.getItem('autoHideMenu') === 'true';
        
        // Load service credentials
        document.getElementById('google-client-id').value = localStorage.getItem('googleClientId') || '';
        document.getElementById('google-client-secret').value = localStorage.getItem('googleClientSecret') || '';
        document.getElementById('slack-client-id').value = localStorage.getItem('slackClientId') || '';
        document.getElementById('slack-client-secret').value = localStorage.getItem('slackClientSecret') || '';
    }

    saveSettings() {
        try {
            // Save general settings
            const backendUrl = document.getElementById('backend-url-setting').value;
            const theme = document.getElementById('theme-setting').value;
            const aiModel = document.getElementById('ai-model-setting').value;
            const language = document.getElementById('language-setting').value;
            
            localStorage.setItem('backendUrl', backendUrl);
            localStorage.setItem('theme', theme);
            localStorage.setItem('aiModel', aiModel);
            localStorage.setItem('language', language);
            
            // Update backend URL if changed
            if (backendUrl !== this.backendUrl) {
                this.backendUrl = backendUrl;
                this.connectWebSocket(); // Reconnect with new URL
            }
            
            // Save voice settings and sync with main interface
            const settingsRate = document.getElementById('settings-speech-rate').value;
            const settingsVolume = document.getElementById('settings-speech-volume').value;
            
            this.speechRateSlider.value = settingsRate;
            this.speechVolumeSlider.value = settingsVolume;
            this.rateValueSpan.textContent = settingsRate;
            this.volumeValueSpan.textContent = settingsVolume;
            
            localStorage.setItem('speechRate', settingsRate);
            localStorage.setItem('speechVolume', settingsVolume);
            
            // Save desktop settings
            localStorage.setItem('autoLaunch', document.getElementById('auto-launch-setting').checked);
            localStorage.setItem('notifications', document.getElementById('notifications-setting').checked);
            localStorage.setItem('minimizeToTray', document.getElementById('minimize-tray-setting').checked);
            localStorage.setItem('autoHideMenu', document.getElementById('auto-hide-menu-setting').checked);
            
            // Apply theme
            this.applyTheme(theme);
            
            // Show success message
            this.addMessage('✅ Settings saved successfully!', 'system');
            this.closeSettings();
            
        } catch (error) {
            console.error('Error saving settings:', error);
            this.addMessage('❌ Error saving settings: ' + error.message, 'system');
        }
    }

    testSettingsVoice() {
        const rate = document.getElementById('settings-speech-rate').value;
        const volume = document.getElementById('settings-speech-volume').value;
        
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance("This is a test of the voice settings. The speech rate and volume are working correctly.");
            utterance.rate = rate / 100;
            utterance.volume = parseFloat(volume);
            utterance.lang = navigator.language || 'en-US';
            
            speechSynthesis.speak(utterance);
        }
    }

    applyTheme(theme) {
        // Basic theme application - can be expanded
        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
    }

    async saveGoogleCredentials() {
        const clientId = document.getElementById('google-client-id').value.trim();
        const clientSecret = document.getElementById('google-client-secret').value.trim();
        
        if (!clientId || !clientSecret) {
            this.addMessage('❌ Please fill in both Google Client ID and Client Secret', 'system');
            return;
        }
        
        try {
            localStorage.setItem('googleClientId', clientId);
            localStorage.setItem('googleClientSecret', clientSecret);
            
            // Also save to backend if available
            const response = await fetch(`${this.backendUrl}/api/config/google-credentials`, {
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
                this.addMessage('✅ Google credentials saved successfully', 'system');
            } else {
                throw new Error('Failed to save credentials to backend');
            }
        } catch (error) {
            console.error('Error saving Google credentials:', error);
            this.addMessage('⚠️ Credentials saved locally, but backend save failed: ' + error.message, 'system');
        }
    }

    async testGoogleConnection() {
        try {
            const response = await fetch(`${this.backendUrl}/api/auth/google/test`);
            const result = await response.json();
            
            if (response.ok && result.valid) {
                this.addMessage('✅ Google connection test successful', 'system');
            } else {
                this.addMessage('❌ Google connection test failed: Invalid credentials', 'system');
            }
        } catch (error) {
            console.error('Error testing Google connection:', error);
            this.addMessage('❌ Google connection test failed: ' + error.message, 'system');
        }
    }

    async saveSlackCredentials() {
        const clientId = document.getElementById('slack-client-id').value.trim();
        const clientSecret = document.getElementById('slack-client-secret').value.trim();
        
        try {
            localStorage.setItem('slackClientId', clientId);
            localStorage.setItem('slackClientSecret', clientSecret);
            
            if (clientId && clientSecret) {
                // Save to backend if both values provided
                const response = await fetch(`${this.backendUrl}/api/config/slack-credentials`, {
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
                    this.addMessage('✅ Slack credentials saved successfully', 'system');
                } else {
                    throw new Error('Failed to save credentials to backend');
                }
            } else {
                this.addMessage('✅ Slack credentials cleared', 'system');
            }
        } catch (error) {
            console.error('Error saving Slack credentials:', error);
            this.addMessage('⚠️ Credentials saved locally, but backend save failed: ' + error.message, 'system');
        }
    }

    async testSlackConnection() {
        try {
            const response = await fetch(`${this.backendUrl}/api/auth/slack/test`);
            const result = await response.json();
            
            if (response.ok && result.valid) {
                this.addMessage('✅ Slack connection test successful', 'system');
            } else {
                this.addMessage('❌ Slack connection test failed: Invalid credentials', 'system');
            }
        } catch (error) {
            console.error('Error testing Slack connection:', error);
            this.addMessage('❌ Slack connection test failed: ' + error.message, 'system');
        }
    }

    async changeModel() {
        const selectedModel = this.aiModelSetting.value;
        
        try {
            const response = await fetch(`${this.backendUrl}/api/agent/model/change`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    provider: selectedModel,
                    model: selectedModel === 'ollama' ? 'granite3.3-balanced:latest' : ''
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                // Save the model selection to localStorage
                localStorage.setItem('aiModel', selectedModel);
                this.showInAppNotification('success', '🤖 Model Changed', `Successfully switched to ${data.current_model}`);
                this.addMessage(`🤖 AI Model switched to: ${data.current_model}`, 'assistant');
            } else {
                throw new Error('Failed to change model');
            }
        } catch (error) {
            console.error('Error changing model:', error);
            this.showInAppNotification('error', '❌ Model Error', 'Failed to change AI model');
        }
    }

    async testCurrentModel() {
        this.testModelBtn.disabled = true;
        this.testModelBtn.textContent = 'Testing...';
        
        try {
            const testMessage = "Hello! Please introduce yourself and tell me which AI model you are.";
            const response = await fetch(`${this.backendUrl}/api/agent/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: testMessage })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.addMessage(testMessage, 'user');
                this.addMessage(data.response, 'assistant');
                this.showInAppNotification('success', '✅ Model Test', 'Model test completed successfully!');
            } else {
                throw new Error('Model test failed');
            }
        } catch (error) {
            console.error('Error testing model:', error);
            this.showInAppNotification('error', '❌ Test Failed', 'Could not test the current model');
        } finally {
            this.testModelBtn.disabled = false;
            this.testModelBtn.textContent = 'Test Current Model';
        }
    }

    async updateUnreadEmailCount() {
        try {
            const response = await fetch(`${this.backendUrl}/api/notifications/unread-count`);
            if (response.ok) {
                const data = await response.json();
                const unreadCount = data.unread_count;
                if (this.unreadBadge) {
                    this.unreadBadge.textContent = unreadCount > 0 ? unreadCount.toString() : '';
                    if (unreadCount > 0) {
                        this.unreadBadge.classList.remove('hidden');
                        this.unreadBadge.classList.add('pulse-red');
                        // Update button text to show unread count
                        const emailButton = document.getElementById('check-unread-emails');
                        const icon = emailButton.querySelector('i');
                        emailButton.innerHTML = `${icon.outerHTML} ${unreadCount} Unread Email${unreadCount > 1 ? 's' : ''} <span id="unread-badge" class="absolute top-1 right-1 bg-red-500 text-white text-xs rounded-full px-2 py-1 min-w-6 text-center pulse-red">${unreadCount}</span>`;
                        this.unreadBadge = document.getElementById('unread-badge'); // Re-reference after DOM update
                    } else {
                        this.unreadBadge.classList.add('hidden');
                        this.unreadBadge.classList.remove('pulse-red');
                        // Reset button text when no unread emails
                        const emailButton = document.getElementById('check-unread-emails');
                        emailButton.innerHTML = '<i class="fas fa-envelope-open-text text-yellow-600 mr-2"></i> Show Unread Emails <span id="unread-badge" class="hidden absolute top-1 right-1 bg-red-500 text-white text-xs rounded-full px-2 py-1 min-w-6 text-center">0</span>';
                        this.unreadBadge = document.getElementById('unread-badge'); // Re-reference after DOM update
                    }
                }
            } else {
                console.error('Failed to fetch unread email count:', response.status);
            }
        } catch (error) {
            console.error('Error updating unread email count:', error);
        }
    }
}

// Initialize the AI Assistant when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new AIAssistant();
}); 