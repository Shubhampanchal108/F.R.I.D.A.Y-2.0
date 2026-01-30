(function () {
  // 1. Icons (SVGs)
  const icons = {
    chat: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="24" height="24"><path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.159 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" /></svg>`,
    close: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" width="20" height="20"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>`,
    send: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" width="18" height="18"><path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" /></svg>`,
    settings: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="20" height="20"><path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.212 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>`
  };

  // 2. Setup Host & Shadow
  // Prevent double-injection when script is loaded multiple times
  let host = document.getElementById("friday-agent-host");
  let shadow;
  if (!host) {
    host = document.createElement("div");
    host.id = "friday-agent-host";
    document.body.appendChild(host);
    shadow = host.attachShadow({ mode: "open" });
  } else {
    // reuse existing host's shadow root if possible
    shadow = host.shadowRoot || host.attachShadow({ mode: "open" });
  }

  // 3. State Management
  const STATE = {
    theme: localStorage.getItem("friday_theme") || "light",
    kb_id: localStorage.getItem("friday_kb_id") || "default",
    api_key: localStorage.getItem("friday_api_key") || "", // New API Key state
    site_id: document.currentScript?.getAttribute("data-site-id") || "default",
  };

  // 4. Styles
  const style = document.createElement("style");
  style.textContent = `
    :host {
      --primary: #4f46e5;
      --primary-hover: #4338ca;
      --bg-color: #ffffff;
      --text-color: #1f2937;
      --bot-bg: #f3f4f6;
      --input-bg: #ffffff;
      --border-color: #e5e7eb;
      --shadow: rgba(0,0,0,0.15);
    }
    
    .dark-mode {
      --bg-color: #111827;
      --text-color: #f3f4f6;
      --bot-bg: #374151;
      --input-bg: #1f2937;
      --border-color: #374151;
      --shadow: rgba(0,0,0,0.5);
    }

    * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }

    #friday-launcher {
      position: fixed; bottom: 24px; right: 24px; width: 60px; height: 60px;
      background: var(--primary); color: white; border-radius: 50%;
      cursor: pointer; box-shadow: 0 4px 14px var(--shadow);
      display: flex; align-items: center; justify-content: center;
      transition: transform 0.2s; z-index: 999998;
    }
    #friday-launcher:hover { transform: scale(1.05); }

    #friday-window {
      position: fixed; bottom: 100px; right: 24px; width: 380px; height: 535px;
      background: var(--bg-color); color: var(--text-color);
      border-radius: 16px; box-shadow: 0 12px 24px var(--shadow);
      display: none; flex-direction: column; overflow: hidden;
      z-index: 999999; border: 1px solid var(--border-color);
      transition: opacity 0.3s;
    }
    #friday-window.open { display: flex; }

    .header {
      background: var(--primary); color: white; padding: 16px;
      display: flex; justify-content: space-between; align-items: center; font-weight: 600;
    }
    .header-controls { display: flex; gap: 12px; }
    .icon-btn { cursor: pointer; opacity: 0.8; transition: opacity 0.2s; }
    .icon-btn:hover { opacity: 1; }

    .messages {
      flex: 1; padding: 16px; overflow-y: auto; background: var(--bg-color);
      display: flex; flex-direction: column; gap: 12px;
    }
    .message {
      max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.4;
      word-wrap: break-word; animation: fadeIn 0.3s ease;
    }
    .message.user { align-self: flex-end; background: var(--primary); color: white; border-bottom-right-radius: 2px; }
    .message.bot { align-self: flex-start; background: var(--bot-bg); color: var(--text-color); border-bottom-left-radius: 2px; }

    /* Settings Overlay */
    #settings-panel {
      position: absolute; top: 56px; left: 0; width: 100%; bottom: 0;
      background: var(--bg-color); padding: 20px;
      transform: translateX(100%); transition: transform 0.3s ease;
      z-index: 10; display: flex; flex-direction: column; gap: 20px;
    }
    #settings-panel.active { transform: translateX(0); }
    
    .setting-item { display: flex; flex-direction: column; gap: 8px; }
    .setting-label { font-size: 14px; font-weight: 600; color: var(--text-color); }
    .setting-input {
      padding: 10px; border-radius: 8px; border: 1px solid var(--border-color);
      background: var(--input-bg); color: var(--text-color); outline: none;
    }
    .setting-hint { font-size: 11px; color: #888; margin-top: -4px; }
    
    .save-btn {
      margin-top: auto; padding: 12px; background: var(--primary); color: white;
      border: none; border-radius: 8px; font-weight: 600; cursor: pointer;
    }

    /* Switch */
    .switch { position: relative; display: inline-block; width: 44px; height: 24px; }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
      background-color: #ccc; transition: .4s; border-radius: 24px;
    }
    .slider:before {
      position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px;
      background-color: white; transition: .4s; border-radius: 50%;
    }
    input:checked + .slider { background-color: var(--primary); }
    input:checked + .slider:before { transform: translateX(20px); }

    .input-area { padding: 12px; border-top: 1px solid var(--border-color); display: flex; gap: 8px; background: var(--bg-color); }
    input {
      flex: 1; padding: 10px 14px; border: 1px solid var(--border-color);
      background: var(--input-bg); color: var(--text-color);
      border-radius: 20px; outline: none;
    }
    input:focus { border-color: var(--primary); }
    #send-btn {
      background: var(--primary); color: white; border: none; width: 40px; height: 40px;
      border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;
    }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
  `;
  shadow.appendChild(style);

  // 5. HTML Structure
  const container = document.createElement("div");
  container.className = STATE.theme === "dark" ? "dark-mode" : ""; 
  container.innerHTML = `
    <div id="friday-launcher">${icons.chat}</div>
    <div id="friday-window">
      <div class="header">
        <span>FRIDAY 2.0</span>
        <div class="header-controls">
          <div class="icon-btn" id="settings-btn" title="Settings">${icons.settings}</div>
          <div class="icon-btn" id="close-btn" title="Close">${icons.close}</div>
        </div>
      </div>

      <div class="messages" id="messages-list">
        <div class="message bot">Hello! I'm Friday. Connect your API Key in settings to start.</div>
      </div>

      <div id="settings-panel">
        <div class="setting-item">
          <span class="setting-label">Dark Mode</span>
          <label class="switch">
            <input type="checkbox" id="theme-toggle" ${STATE.theme === 'dark' ? 'checked' : ''}>
            <span class="slider"></span>
          </label>
        </div>
        
        <div class="setting-item">
          <span class="setting-label">Knowledge Base ID</span>
          <input class="setting-input" id="kb-input" type="text" value="${STATE.kb_id}" placeholder="e.g. documentation-v2">
        </div>

        <div class="setting-item">
          <span class="setting-label">API Key</span>
          <input class="setting-input" id="api-key-input" type="password" value="${STATE.api_key}" placeholder="sk-...">
          <span class="setting-hint">Your key is stored locally on this device.</span>
        </div>

        <button class="save-btn" id="save-settings">Save & Close</button>
      </div>

      <div class="input-area">
        <input id="chat-input" type="text" placeholder="Ask Friday..." autocomplete="off" />
        <button id="send-btn">${icons.send}</button>
      </div>
    </div>
  `;
  shadow.appendChild(container);

  // 6. Logic
  const win = shadow.getElementById("friday-window");
  const launcher = shadow.getElementById("friday-launcher");
  const closeBtn = shadow.getElementById("close-btn");
  const settingsBtn = shadow.getElementById("settings-btn");
  const settingsPanel = shadow.getElementById("settings-panel");
  const saveSettingsBtn = shadow.getElementById("save-settings");
  
  const themeToggle = shadow.getElementById("theme-toggle");
  const kbInput = shadow.getElementById("kb-input");
  const apiKeyInput = shadow.getElementById("api-key-input"); // New Input
  
  const input = shadow.getElementById("chat-input");
  const sendBtn = shadow.getElementById("send-btn");
  const messagesList = shadow.getElementById("messages-list");

  // Load saved messages (last 15) from localStorage
  const loadSavedMessages = () => {
    try {
      const raw = localStorage.getItem("friday_messages");
      const arr = raw ? JSON.parse(raw) : [];
      if (Array.isArray(arr) && arr.length > 0) {
        // clear default messages and render saved
        messagesList.innerHTML = "";
        arr.forEach(m => {
          const div = document.createElement("div");
          div.className = `message ${m.type}`;
          div.textContent = m.text;
          messagesList.appendChild(div);
        });
        messagesList.scrollTop = messagesList.scrollHeight;
      }
    } catch (e) {
      console.warn("Failed to load saved messages", e);
    }
  };

  const saveMessages = (msgArray) => {
    try {
      localStorage.setItem("friday_messages", JSON.stringify(msgArray.slice(-15)));
    } catch (e) {
      console.warn("Failed to save messages", e);
    }
  };

  // Initialize messages from storage
  loadSavedMessages();

  // Toggle Window
  launcher.onclick = () => {
    win.style.display = 'flex';
    setTimeout(() => win.classList.add("open"), 10);
    input.focus();
  };
  closeBtn.onclick = () => {
    win.classList.remove("open");
    setTimeout(() => win.style.display = 'none', 300);
  };

  // Toggle Settings
  settingsBtn.onclick = () => settingsPanel.classList.toggle("active");

  // Save Settings
  saveSettingsBtn.onclick = () => {
    STATE.kb_id = kbInput.value.trim() || "default";
    STATE.api_key = apiKeyInput.value.trim(); // Get API Key
    
    // Persist to LocalStorage
    localStorage.setItem("friday_kb_id", STATE.kb_id);
    localStorage.setItem("friday_api_key", STATE.api_key);
    localStorage.setItem("friday_theme", STATE.theme);
    
    settingsPanel.classList.remove("active");
    
    // Notification
    const note = document.createElement("div");
    note.className = "message bot";
    note.textContent = "Settings updated securely.";
    messagesList.appendChild(note);
    messagesList.scrollTop = messagesList.scrollHeight;
  };

  // Theme Toggle
  themeToggle.onchange = (e) => {
    if(e.target.checked) {
      STATE.theme = "dark";
      container.classList.add("dark-mode");
    } else {
      STATE.theme = "light";
      container.classList.remove("dark-mode");
    }
  };

  // Chat Logic
  const addMessage = (text, type) => {
    const div = document.createElement("div");
    div.className = `message ${type}`;
    div.textContent = text;
    messagesList.appendChild(div);
    messagesList.scrollTop = messagesList.scrollHeight;
    // Ensure the window remains visible when a new message arrives
    if (win) {
      win.style.display = 'flex';
      win.classList.add("open");
    }
    // Persist message to localStorage (keep last 15)
    try {
      const raw = localStorage.getItem("friday_messages");
      const arr = raw ? JSON.parse(raw) : [];
      arr.push({ text, type, ts: new Date().toISOString() });
      saveMessages(arr);
    } catch (e) {
      console.warn("Unable to persist message", e);
    }
  };

  const handleSend = async () => {
    const text = input.value.trim();
    if (!text) return;

    // Optional: Validation
    if (!STATE.api_key) {
      addMessage("Please set your API Key in settings first!", "bot");
      settingsPanel.classList.add("active"); // Auto-open settings
      return;
    }

    addMessage(text, "user");
    input.value = "";
    sendBtn.disabled = true;

    try {
      const response = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${STATE.api_key}` // Sending Key in Header
        },
        body: JSON.stringify({
          site_id: STATE.site_id,
          knowledge_base_id: STATE.kb_id,
          message: text,
          timestamp: new Date().toISOString()
        })
      });
      
      const data = await response.json();
      sendBtn.disabled = false;
      addMessage(data.reply || "No response.", "bot");
    } catch (error) {
      sendBtn.disabled = false;
      addMessage("Connection failed. Check your API Key.", "bot");
    }
  };

  sendBtn.onclick = handleSend;
  // Use keydown for reliable Enter handling and prevent default form submits
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  });

})();