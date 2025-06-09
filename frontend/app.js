// Constants
const API_URL = 'http://localhost:8000';
const PROMPT_TEMPLATES = {
    explain: "Please explain this code:\n\n",
    summarize: "Please summarize this:\n\n",
    debug: "Please help me debug this code:\n\n"
};

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const themeToggle = document.getElementById('themeToggle');
const templateButtons = document.querySelectorAll('.template-btn');
const modelConfigButton = document.getElementById('modelConfigButton');
const modelConfigModal = document.getElementById('modelConfigModal');
const modelPathInput = document.getElementById('modelPathInput');
const saveConfigButton = document.getElementById('saveConfigButton');
const closeModalButton = document.getElementById('closeModalButton');

// State
let chatHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
let isDarkMode = localStorage.getItem('darkMode') === 'true';
let isProcessing = false;

// Initialize
async function init() {
    // Set initial theme
    updateTheme();
    
    // Load chat history
    loadChatHistory();
    
    // Check model status
    await checkModelStatus();
    
    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });
    
    // Send message on Enter (but allow Shift+Enter for new line)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Send button click
    sendButton.addEventListener('click', sendMessage);
    
    // Theme toggle
    themeToggle.addEventListener('click', toggleTheme);
    
    // Template buttons
    templateButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const template = PROMPT_TEMPLATES[btn.dataset.template];
            messageInput.value = template;
            messageInput.focus();
        });
    });

    // Model config modal
    modelConfigButton.addEventListener('click', showModelConfig);
    closeModalButton.addEventListener('click', hideModelConfig);
    saveConfigButton.addEventListener('click', saveModelConfig);
}

// Theme handling
function toggleTheme() {
    isDarkMode = !isDarkMode;
    localStorage.setItem('darkMode', isDarkMode);
    updateTheme();
}

function updateTheme() {
    document.body.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    themeToggle.textContent = isDarkMode ? '☀️' : '🌙';
}

// Model configuration
async function checkModelStatus() {
    try {
        const response = await fetch(`${API_URL}/api/model/status`);
        const data = await response.json();
        
        console.log('Model status response:', data);

        if (!data.model_loaded) {
            showModelConfig();
            // Optionally, update the help text or show a message based on data.status
            // e.g., if (data.status.includes('not found')) { /* update UI */ }
        } else {
            hideModelConfig(); // Hide if model is loaded
        }
    } catch (error) {
        console.error('Error checking model status:', error);
        // In case of error, show config modal as a fallback
        showModelConfig();
    }
}

function showModelConfig() {
    modelConfigModal.style.display = 'flex';
    // Pre-fill with default model path if it exists or is known
    if (modelPathInput.value === '') {
        modelPathInput.value = 'backend/model/phi-4-Q3_K_S.gguf';
    }
}

function hideModelConfig() {
    modelConfigModal.style.display = 'none';
}

async function saveModelConfig() {
    const modelPath = modelPathInput.value.trim();
    if (!modelPath) {
        alert('Please enter a model path');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/model/configure`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model_path: modelPath
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to save configuration');
        }

        const data = await response.json();
        if (data.status === 'success') {
            hideModelConfig();
            location.reload(); // Reload to initialize the model
        }
    } catch (error) {
        console.error('Error saving configuration:', error);
        alert('Failed to save configuration. Please try again.');
    }
}

// Chat functionality
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isProcessing) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Show loading state
    isProcessing = true;
    sendButton.disabled = true;
    messageInput.disabled = true;
    addLoadingIndicator();
    
    try {
        // Prepare messages for API
        const messages = [
            ...chatHistory,
            { role: 'user', content: message }
        ];
        
        // Send to API
        const response = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ messages, stream: false }),
        });
        
        if (!response.ok) {
            throw new Error('API request failed');
        }
        
        const data = await response.json();
        
        // Remove loading indicator
        removeLoadingIndicator();
        
        // Add AI response to chat
        addMessageToChat('assistant', data.response);
        
        // Update chat history
        chatHistory = messages.concat([{ role: 'assistant', content: data.response }]);
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        
    } catch (error) {
        console.error('Error:', error);
        removeLoadingIndicator();
        addMessageToChat('assistant', 'Sorry, I encountered an error. Please try again.');
    } finally {
        // Reset processing state
        isProcessing = false;
        sendButton.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    }
}

function addMessageToChat(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addLoadingIndicator() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message ai-message loading';
    loadingDiv.innerHTML = '<div class="loading-dots"><span>.</span><span>.</span><span>.</span></div>';
    loadingDiv.id = 'loadingIndicator';
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeLoadingIndicator() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

function loadChatHistory() {
    chatHistory.forEach(msg => {
        addMessageToChat(msg.role, msg.content);
    });
}

// Initialize the app
init(); 