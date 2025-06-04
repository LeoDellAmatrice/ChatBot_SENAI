async function sendQuestion() {
    const userInput = document.getElementById('user-input').value;
    const courseSelect = document.getElementById('course-select').value;
    const chatBox = document.getElementById('chat-box');
    const debugData = document.getElementById('debug-data');

    if (!userInput.trim()) return;

    chatBox.innerHTML += `<div class="user-message"><strong>Você:</strong> ${userInput}</div>`;
    document.getElementById('user-input').value = '';

    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: userInput,
                course: courseSelect
            })
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        chatBox.innerHTML += `<div class="bot-message"><strong>Bot:</strong> ${data.response}</div>`;
        debugData.textContent = JSON.stringify(data.debug, null, 2);
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {
        chatBox.innerHTML += `<div class="error-message"><strong>Erro:</strong> ${error.message}</div>`;
    }
}