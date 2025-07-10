const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const restartBtn = document.getElementById('restart-btn');

function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    msgDiv.appendChild(bubble);
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function sendMessage(msg) {
    appendMessage('user', msg);
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
    })
    .then(res => res.json())
    .then(data => {
        appendMessage('assistant', data.reply);
        if (data.end) {
            userInput.disabled = true;
            restartBtn.style.display = 'block';
        }
    });
}

chatForm.addEventListener('submit', e => {
    e.preventDefault();
    const msg = userInput.value.trim();
    if (!msg) return;
    sendMessage(msg);
    userInput.value = '';
});

// Theme switching
const themeToggle = document.getElementById('theme-toggle');
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    if(document.body.classList.contains('dark')) {
        themeToggle.textContent = '☀️ Theme';
    } else {
        themeToggle.textContent = '🌙 Theme';
    }
});

// Start conversation automatically
function startConversation() {
    chatWindow.innerHTML = '';
    userInput.disabled = false;
    restartBtn.style.display = 'none';
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: '' })
    })
    .then(res => res.json())
    .then(data => {
        appendMessage('assistant', data.reply);
    });
}
window.onload = startConversation;

restartBtn.addEventListener('click', startConversation);
