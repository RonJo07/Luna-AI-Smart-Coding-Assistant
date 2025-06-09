// Global variables
let currentSessionId = null;
let isDarkMode = false;

// DOM Elements
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const themeToggle = document.getElementById('theme-toggle');
const modelConfigButton = document.getElementById('model-config-button');
const modelConfigModal = document.getElementById('model-config-modal');
const modelConfigForm = document.getElementById('model-config-form');
const modelPathInput = document.getElementById('model-path');
const closeModalButton = document.getElementById('close-modal');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');

// Initialize application
async function initializeApp() {
    // Check model status first
    const status = await checkModelStatus();
    if (status.status === 'not_configured') {
        showModelConfigModal();
    }
    
    // Set up event listeners
    setupEventListeners();
    
    // Load theme preference
    loadThemePreference();
}

// Check model status
async function checkModelStatus() {
    try {
        const response = await fetch('/api/model/status');
        const data = await response.json();
        updateStatus(data);
        return data;
    } catch (error) {
        console.error('Error checking model status:', error);
        updateStatus({ status: 'error', detail: 'Failed to connect to server' });
        return { status: 'error' };
    }
}

// Update status indicator
function updateStatus(status) {
    if (status.status === 'ready') {
        statusIndicator.className = 'status-indicator ready';
        statusText.textContent = 'Ready';
        statusText.title = `Performance: ${status.performance?.avg_speed?.toFixed(2) || 0} tokens/s`;
    } else if (status.status === 'not_configured') {
        statusIndicator.className = 'status-indicator not-configured';
        statusText.textContent = 'Not Configured';
        statusText.title = 'Click to configure model';
    } else if (status.status === 'not_loaded') {
        statusIndicator.className = 'status-indicator not-loaded';
        statusText.textContent = 'Not Loaded';
        statusText.title = 'Model configuration error';
    } else {
        statusIndicator.className = 'status-indicator error';
        statusText.textContent = 'Error';
        statusText.title = status.detail || 'Unknown error';
    }
}

// Show model configuration modal
function showModelConfigModal() {
    modelConfigModal.style.display = 'flex';
    // Set default path if available
    const defaultPath = 'backend/model/phi-4-Q3_K_S.gguf';
    modelPathInput.value = defaultPath;
    modelPathInput.focus();
}

// Hide model configuration modal
function hideModelConfigModal() {
    modelConfigModal.style.display = 'none';
}

// Handle model configuration
async function handleModelConfig(event) {
    event.preventDefault();
    
    const modelPath = modelPathInput.value.trim();
    if (!modelPath) {
        alert('Please enter a model path');
        return;
    }
    
    try {
        const response = await fetch('/api/model/configure', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model_path: modelPath,
                model_config: {
                    n_ctx: 4096,
                    n_threads: 4,
                    n_batch: 512
                }
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            hideModelConfigModal();
            await checkModelStatus();
        } else {
            alert(`Configuration failed: ${data.detail}`);
        }
    } catch (error) {
        console.error('Error configuring model:', error);
        alert('Failed to configure model. Please try again.');
    }
}

// Set up event listeners
function setupEventListeners() {
    // Send message on button click
    sendButton.addEventListener('click', handleSendMessage);
    
    // Send message on Enter key
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    // Theme toggle
    themeToggle.addEventListener('click', toggleTheme);
    
    // Model configuration
    modelConfigButton.addEventListener('click', showModelConfigModal);
    modelConfigForm.addEventListener('submit', handleModelConfig);
    closeModalButton.addEventListener('click', hideModelConfigModal);
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === modelConfigModal) {
            hideModelConfigModal();
        }
    });
}

// Handle sending messages
async function handleSendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    userInput.value = '';
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addMessageToChat('assistant', data.response);
            if (data.performance) {
                console.log('Performance:', data.performance);
            }
        } else {
            addMessageToChat('error', `Error: ${data.detail}`);
        }
    } catch (error) {
        console.error('Error sending message:', error);
        addMessageToChat('error', 'Failed to send message. Please try again.');
    }
}

// Add message to chat
function addMessageToChat(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Toggle theme
function toggleTheme() {
    isDarkMode = !isDarkMode;
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
}

// Load theme preference
function loadThemePreference() {
    const savedTheme = localStorage.getItem('darkMode');
    if (savedTheme === 'true') {
        isDarkMode = true;
        document.body.classList.add('dark-mode');
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp); 