/**
 * F.R.I.D.A.Y 2.0 // Neural Widget Master Controller
 * Full UI control bridging frontend holographic UI with Python backend
 * Handles multi-mode switching, wake-word listener, live vision streams, API keys, and tasks
 */

let orbInstance = null;
let isAudioActive = true;
let isProcessing = false;
let isRecording = false;
let isExpanded = false;
let isAgentSpeaking = false;
let sfxEnabled = true;
let currentOperatingMode = 'text';

async function interruptSpeech() {
  playSfx('click');
  isAgentSpeaking = false;
  setOrbState('idle', 'INTERRUPTED // STANDBY');
  const banner = document.getElementById('chat-interrupter-banner');
  if (banner) banner.classList.add('hidden');
  if (window.pywebview && window.pywebview.api) {
    try {
      await window.pywebview.api.interrupt_speech();
    } catch (e) {
      console.warn('interrupt_speech error:', e);
    }
  }
}
window.fridayInterruptSpeech = interruptSpeech;

// Web Audio API Context for synthesized holographic SFX
let audioCtx = null;

function playSfx(type = 'click') {
  if (!sfxEnabled) return;
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;

    if (type === 'click') {
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(1400, now + 0.05);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
      osc.start(now);
      osc.stop(now + 0.05);
    } else if (type === 'tab') {
      osc.frequency.setValueAtTime(520, now);
      osc.frequency.exponentialRampToValueAtTime(980, now + 0.08);
      gain.gain.setValueAtTime(0.07, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      osc.start(now);
      osc.stop(now + 0.08);
    } else if (type === 'expand') {
      osc.frequency.setValueAtTime(400, now);
      osc.frequency.exponentialRampToValueAtTime(1200, now + 0.12);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
      osc.start(now);
      osc.stop(now + 0.12);
    } else if (type === 'ping') {
      osc.frequency.setValueAtTime(1200, now);
      osc.frequency.exponentialRampToValueAtTime(1800, now + 0.1);
      gain.gain.setValueAtTime(0.09, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
      osc.start(now);
      osc.stop(now + 0.1);
    }
  } catch (e) {
    // Ignore audio autoplay restrictions
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Arc Reactor & Frequency Visualizer
  orbInstance = new FridayOrb('orb-canvas', 'freq-canvas');

  // 2. Setup Navigation & Views
  setupNavigationTabs();

  // 3. Setup Window Controls (Expand, Collapse, Minimize, Close)
  setupWindowControls();

  // 4. Setup Operating Mode Switcher (1-click mode shifting)
  setupOperatingModes();

  // 5. Setup Chat & Input Handlers
  setupChatHandlers();

  // 6. Setup Core HUD Quick Actions
  setupCoreHudHandlers();

  // 7. Setup Settings Page Handlers (Audio, API Keys, Persona)
  setupSettingsHandlers();

  // 8. Setup Profile & Reminders Handlers
  setupProfileHandlers();

  // 9. Connect to Python pywebview API
  if (window.pywebview) {
    onPywebviewReady();
  } else {
    window.addEventListener('pywebviewready', onPywebviewReady);
  }
});

function onPywebviewReady() {
  console.log('[FRIDAY] pywebview API connected.');
  fetchInitialTelemetry();
  loadAssistantSettings();
  loadUserProfile();
  loadApiKeysConfig();
  loadRemindersAndTasks();
  syncOperatingMode();
}

// ==========================================================================
// 1. NAVIGATION & TAB SWITCHING
// ==========================================================================
function setupNavigationTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  const views = document.querySelectorAll('.view-pane');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetView = tab.getAttribute('data-view');
      switchView(targetView);
    });
  });
}

function switchView(viewName) {
  playSfx('tab');
  const tabs = document.querySelectorAll('.nav-tab');
  const views = document.querySelectorAll('.view-pane');

  tabs.forEach(t => {
    if (t.getAttribute('data-view') === viewName) {
      t.classList.add('active');
    } else {
      t.classList.remove('active');
    }
  });

  views.forEach(v => {
    if (v.id === `view-${viewName}`) {
      v.classList.add('active');
    } else {
      v.classList.remove('active');
    }
  });

  // Manage Arc Reactor rendering based on active view
  if (viewName === 'core') {
    if (orbInstance) {
      orbInstance.resume();
      setTimeout(() => orbInstance.setupDPI(), 60);
    }
  } else {
    if (orbInstance) {
      orbInstance.pause();
    }
    if (viewName === 'chat') {
      scrollToBottom();
      setTimeout(() => {
        const input = document.getElementById('query-input');
        if (input) input.focus();
      }, 100);
    } else if (viewName === 'settings') {
      loadAssistantSettings();
      loadApiKeysConfig();
    } else if (viewName === 'profile') {
      loadUserProfile();
      loadRemindersAndTasks();
    }
  }
}

// ==========================================================================
// 2. WINDOW CONTROLS (EXPAND, COLLAPSE, MINIMIZE, CLOSE)
// ==========================================================================
function setupWindowControls() {
  const btnExpand = document.getElementById('btn-expand');
  const btnCollapse = document.getElementById('btn-collapse');
  const btnMinimize = document.getElementById('btn-minimize');
  const btnClose = document.getElementById('btn-close');
  const miniOrbContainer = document.getElementById('mini-orb-container');

  btnExpand.addEventListener('click', handleToggleExpand);

  btnCollapse.addEventListener('click', (e) => {
    e.stopPropagation();
    switchWindowMode('orb');
  });

  if (miniOrbContainer) {
    miniOrbContainer.addEventListener('click', (e) => {
      e.stopPropagation();
      switchWindowMode('full');
    });
  }

  // Fallback safety: clicking anywhere while in mini-orb mode expands back to full window
  document.addEventListener('click', () => {
    if (document.body.classList.contains('mode-orb')) {
      switchWindowMode('full');
    }
  });

  btnMinimize.addEventListener('click', handleHideWindow);
  btnClose.addEventListener('click', handleCloseApplication);
}

async function handleCloseApplication() {
  playSfx('click');
  if (window.pywebview && window.pywebview.api) {
    try {
      await window.pywebview.api.close_application();
    } catch (err) {
      console.warn('API close_application error:', err);
    }
  } else {
    window.close();
  }
}

async function handleToggleExpand() {
  playSfx('expand');
  const btnExpand = document.getElementById('btn-expand');
  const iconExpand = btnExpand.querySelector('.icon-expand');
  const iconShrink = btnExpand.querySelector('.icon-shrink');

  if (window.pywebview && window.pywebview.api) {
    try {
      const res = await window.pywebview.api.toggle_expand_window();
      isExpanded = res && res.expanded;
    } catch (err) {
      isExpanded = !isExpanded;
    }
  } else {
    isExpanded = !isExpanded;
  }

  if (isExpanded) {
    document.body.classList.add('mode-expanded');
    iconExpand.classList.add('hidden');
    iconShrink.classList.remove('hidden');
    btnExpand.title = "Restore Compact Size (Corner)";
  } else {
    document.body.classList.remove('mode-expanded');
    iconExpand.classList.remove('hidden');
    iconShrink.classList.add('hidden');
    btnExpand.title = "Expand UI (Enlarge Workspace)";
  }

  if (orbInstance) {
    setTimeout(() => orbInstance.setupDPI(), 100);
  }
}

async function switchWindowMode(mode) {
  playSfx('click');
  if (mode === 'orb') {
    if (orbInstance) orbInstance.pause();
    document.body.classList.remove('mode-full');
    document.body.classList.add('mode-orb');
    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.minimize_to_orb();
      } catch (err) {
        console.warn('API minimize_to_orb error:', err);
      }
    }
  } else {
    document.body.classList.remove('mode-orb');
    document.body.classList.add('mode-full');
    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.expand_to_full();
      } catch (err) {
        console.warn('API expand_to_full error:', err);
      }
    }
    const activeTab = document.querySelector('.nav-tab.active');
    if (activeTab && activeTab.getAttribute('data-view') === 'core' && orbInstance) {
      orbInstance.resume();
      setTimeout(() => orbInstance.setupDPI(), 150);
    }
  }
}

async function handleHideWindow() {
  playSfx('click');
  if (window.pywebview && window.pywebview.api) {
    try {
      await window.pywebview.api.hide_window();
    } catch (err) {
      console.warn('API hide_window error:', err);
    }
  }
}

// ==========================================================================
// 3. OPERATING PROTOCOLS & 1-CLICK MODE SHIFTING
// ==========================================================================
function setupOperatingModes() {
  const pills = document.querySelectorAll('.mode-pill-btn');
  const stopLiveBtn = document.getElementById('btn-stop-live');
  const btnStartScreen = document.getElementById('btn-start-screen-vision');
  const btnStartCamera = document.getElementById('btn-start-camera-vision');

  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      const mode = pill.getAttribute('data-mode');
      shiftOperatingMode(mode);
    });
  });

  if (stopLiveBtn) {
    stopLiveBtn.addEventListener('click', () => {
      shiftOperatingMode('stop_live');
    });
  }

  if (btnStartScreen) {
    btnStartScreen.addEventListener('click', () => shiftOperatingMode('live_screen'));
  }
  if (btnStartCamera) {
    btnStartCamera.addEventListener('click', () => shiftOperatingMode('live_camera'));
  }
}

async function shiftOperatingMode(mode) {
  playSfx('ping');
  currentOperatingMode = mode === 'stop_live' ? 'text' : mode;

  // Update UI pill active states
  const pills = document.querySelectorAll('.mode-pill-btn');
  pills.forEach(p => {
    if (p.getAttribute('data-mode') === currentOperatingMode) {
      p.classList.add('active');
    } else {
      p.classList.remove('active');
    }
  });

  const badge = document.getElementById('hud-active-mode-badge');
  const info = document.getElementById('mode-status-info');
  const liveBanner = document.getElementById('live-active-banner');
  const liveText = document.getElementById('live-feed-status-text');

  if (currentOperatingMode === 'text') {
    badge.textContent = 'TEXT';
    info.textContent = 'Keyboard input protocol active';
    if (liveBanner) liveBanner.classList.add('hidden');
    setOrbState('idle', 'F.R.I.D.A.Y STANDBY');
  } else if (currentOperatingMode === 'voice') {
    badge.textContent = 'VOICE';
    info.textContent = 'Direct speech conversation protocol';
    if (liveBanner) liveBanner.classList.add('hidden');
    handleToggleVoiceInput();
  } else if (currentOperatingMode === 'wakeword') {
    badge.textContent = 'WAKE-WORD';
    info.textContent = "Listening for 'Hey Friday'...";
    if (liveBanner) liveBanner.classList.add('hidden');
    setOrbState('idle', "STANDBY // SAY 'HEY FRIDAY'");
  } else if (currentOperatingMode === 'live_screen') {
    badge.textContent = 'SCREEN VISION';
    info.textContent = 'Streaming desktop screen to Gemini...';
    if (liveBanner) {
      liveBanner.classList.remove('hidden');
      liveText.textContent = 'LIVE SCREEN STREAM ACTIVE';
    }
    setOrbState('thinking', 'LIVE SCREEN MULTIMODAL ACTIVE');
  } else if (currentOperatingMode === 'live_camera') {
    badge.textContent = 'CAMERA VISION';
    info.textContent = 'Streaming camera video feed to Gemini...';
    if (liveBanner) {
      liveBanner.classList.remove('hidden');
      liveText.textContent = 'LIVE CAMERA STREAM ACTIVE';
    }
    setOrbState('thinking', 'LIVE CAMERA MULTIMODAL ACTIVE');
  }

  // Sync with Python backend
  if (window.pywebview && window.pywebview.api) {
    try {
      await window.pywebview.api.set_operating_mode(mode);
    } catch (e) {
      console.warn('set_operating_mode error:', e);
    }
  }
}

async function syncOperatingMode() {
  if (window.pywebview && window.pywebview.api) {
    try {
      const modeData = await window.pywebview.api.get_operating_mode();
      if (modeData && modeData.mode) {
        shiftOperatingMode(modeData.mode);
      }
    } catch (e) {
      console.warn('syncOperatingMode error:', e);
    }
  }
}

// Global wake-word triggered from Python backend
window.fridayOnWakeWord = function(phrase) {
  playSfx('ping');
  setOrbState('listening', `WAKE WORD DETECTED: "${phrase || 'Hey Friday'}"`);
  const activeTab = document.querySelector('.nav-tab.active');
  if (!activeTab || activeTab.getAttribute('data-view') !== 'chat') {
    switchView('chat');
  }
  setTimeout(() => {
    handleToggleVoiceInput();
  }, 400);
};

// ==========================================================================
// 4. CORE HUD VIEW ACTIONS
// ==========================================================================
function setupCoreHudHandlers() {
  const btnCoreVoice = document.getElementById('btn-core-voice');
  const coreQuickInput = document.getElementById('core-quick-input');
  const btnCoreSend = document.getElementById('btn-core-send');

  btnCoreVoice.addEventListener('click', () => {
    handleToggleVoiceInput();
  });

  btnCoreSend.addEventListener('click', () => {
    const prompt = coreQuickInput.value.trim();
    if (prompt) {
      coreQuickInput.value = '';
      switchView('chat');
      document.getElementById('query-input').value = prompt;
      handleSendPrompt();
    }
  });

  coreQuickInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const prompt = coreQuickInput.value.trim();
      if (prompt) {
        coreQuickInput.value = '';
        switchView('chat');
        document.getElementById('query-input').value = prompt;
        handleSendPrompt();
      }
    }
  });

  document.querySelectorAll('.action-tile').forEach(tile => {
    tile.addEventListener('click', () => {
      playSfx('click');
      const prompt = tile.getAttribute('data-prompt');
      const action = tile.getAttribute('data-action');
      if (action === 'briefing') {
        handleTriggerBriefing();
      } else if (prompt) {
        switchView('chat');
        document.getElementById('query-input').value = prompt;
        handleSendPrompt();
      } else if (action === 'open-chat') {
        switchView('chat');
      }
    });
  });
}

// Proactive Executive Morning Briefing
async function handleTriggerBriefing() {
  playSfx('ping');
  switchView('chat');
  setOrbState('thinking', 'GENERATING PROACTIVE EXECUTIVE BRIEFING');
  appendAssistantMessage('🌅 Generating comprehensive executive briefing, Sir...');

  if (window.pywebview && window.pywebview.api) {
    try {
      const briefing = await window.pywebview.api.trigger_morning_briefing();
      if (briefing) {
        appendAssistantMessage(briefing);
      }
    } catch (e) {
      appendAssistantMessage(`⚠️ Executive briefing error: ${e}`);
    }
  } else {
    await new Promise(r => setTimeout(r, 1200));
    appendAssistantMessage('Good morning Sir. All systems nominal, battery at 92%. You have no overdue reminders today.');
  }
  setOrbState('idle', 'F.R.I.D.A.Y STANDBY');
}

// ==========================================================================
// 5. CHAT VIEWPORT & MESSAGES
// ==========================================================================
function setupChatHandlers() {
  const queryInput = document.getElementById('query-input');
  const btnSend = document.getElementById('btn-send');
  const btnMic = document.getElementById('btn-mic');
  const btnAudio = document.getElementById('btn-audio-toggle');
  const interrupter = document.getElementById('chat-interrupter-banner');

  if (interrupter) {
    interrupter.addEventListener('click', () => interruptSpeech());
  }

  queryInput.addEventListener('input', () => {
    queryInput.style.height = 'auto';
    queryInput.style.height = Math.min(queryInput.scrollHeight, 80) + 'px';
  });

  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendPrompt();
    }
  });

  btnSend.addEventListener('click', handleSendPrompt);
  btnMic.addEventListener('click', handleToggleVoiceInput);
  btnAudio.addEventListener('click', handleToggleAudioOutput);

  document.querySelectorAll('.chip-btn').forEach(chip => {
    chip.addEventListener('click', () => {
      playSfx('click');
      const prompt = chip.getAttribute('data-prompt');
      const action = chip.getAttribute('data-action');
      if (action === 'briefing') {
        handleTriggerBriefing();
      } else if (prompt) {
        queryInput.value = prompt;
        handleSendPrompt();
      } else if (action === 'clear-chat') {
        clearChatMessages();
      }
    });
  });
}

async function handleSendPrompt() {
  // If Friday is speaking, new prompt immediately interrupts ongoing speech
  if (isAgentSpeaking) {
    await interruptSpeech();
  }
  if (isProcessing) return;
  const input = document.getElementById('query-input');
  const prompt = input.value.trim();
  if (!prompt) return;

  playSfx('click');

  input.value = '';
  input.style.height = 'auto';

  appendUserMessage(prompt);

  isProcessing = true;
  setOrbState('thinking', 'ANALYZING & PROCESSING DIRECTIVE');

  try {
    let response = "Sir, I am unable to connect to the cognitive backend.";
    if (window.pywebview && window.pywebview.api) {
      response = await window.pywebview.api.send_query(prompt);
    } else {
      await new Promise(r => setTimeout(r, 1000));
      response = `Directive acknowledged, Sir. All local neural parameters are operational for: "${prompt}".`;
    }

    appendAssistantMessage(response);
    playSfx('ping');

    // If speech is not triggered or already completed, revert to standby
    if (!isAgentSpeaking) {
      setOrbState('idle', 'F.R.I.D.A.Y STANDBY');
    }

  } catch (err) {
    appendAssistantMessage(`⚠️ System Error: ${err.message || err}`);
    setOrbState('idle', 'F.R.I.D.A.Y STANDBY');
  } finally {
    isProcessing = false;
  }
}

// Voice input
async function handleToggleVoiceInput() {
  // If Friday is speaking, clicking mic immediately silences her
  if (isAgentSpeaking) {
    await interruptSpeech();
  }
  if (isProcessing) return;

  const btnMic = document.getElementById('btn-mic');
  if (isRecording) {
    isRecording = false;
    btnMic.classList.remove('recording');
    setOrbState('idle', 'F.R.I.D.A.Y STANDBY');
    return;
  }

  isRecording = true;
  btnMic.classList.add('recording');
  setOrbState('listening', 'LISTENING FOR VOCAL COMMAND...');
  playSfx('ping');

  try {
    let recognizedText = "";
    if (window.pywebview && window.pywebview.api) {
      recognizedText = await window.pywebview.api.start_voice_input();
    } else {
      await new Promise(r => setTimeout(r, 2000));
      recognizedText = "System diagnostic status";
    }

    btnMic.classList.remove('recording');
    isRecording = false;

    if (recognizedText && recognizedText.trim()) {
      switchView('chat');
      document.getElementById('query-input').value = recognizedText;
      handleSendPrompt();
    } else {
      setOrbState('idle', 'NO SPEECH DETECTED');
      setTimeout(() => setOrbState('idle', 'F.R.I.D.A.Y STANDBY'), 1500);
    }
  } catch (err) {
    btnMic.classList.remove('recording');
    isRecording = false;
    setOrbState('idle', 'MIC ERROR');
    setTimeout(() => setOrbState('idle', 'F.R.I.D.A.Y STANDBY'), 1500);
  }
}

// Audio output TTS
async function handleToggleAudioOutput() {
  playSfx('click');
  isAudioActive = !isAudioActive;
  const btn = document.getElementById('btn-audio-toggle');
  const iconOn = btn.querySelector('.sound-on');
  const iconOff = btn.querySelector('.sound-off');

  if (isAudioActive) {
    btn.classList.add('active');
    btn.title = "Toggle Voice Output (Speaking ON)";
    iconOn.classList.remove('hidden');
    iconOff.classList.add('hidden');
  } else {
    btn.classList.remove('active');
    btn.title = "Toggle Voice Output (Speaking MUTED)";
    iconOn.classList.add('hidden');
    iconOff.classList.remove('hidden');
  }

  const voiceToggleSetting = document.getElementById('setting-voice-enabled');
  if (voiceToggleSetting) voiceToggleSetting.checked = isAudioActive;

  if (window.pywebview && window.pywebview.api) {
    try {
      await window.pywebview.api.toggle_audio(isAudioActive);
    } catch (err) {
      console.warn('API toggle_audio error:', err);
    }
  }
}

// ==========================================================================
// 6. SETTINGS & FULL API CONFIGURATION
// ==========================================================================
function setupSettingsHandlers() {
  const sliderRate = document.getElementById('setting-speech-rate');
  const valRate = document.getElementById('val-speech-rate');
  const sliderPitch = document.getElementById('setting-speech-pitch');
  const valPitch = document.getElementById('val-speech-pitch');
  const sfxToggle = document.getElementById('setting-sfx-enabled');
  const btnSave = document.getElementById('btn-save-settings');
  const btnReset = document.getElementById('btn-reset-settings');
  const btnSaveApi = document.getElementById('btn-save-api-config');
  const btnBriefingNow = document.getElementById('btn-trigger-briefing-now');
  const wakeWordCheckbox = document.getElementById('setting-wakeword-enabled');

  sliderRate.addEventListener('input', () => {
    valRate.textContent = sliderRate.value;
  });

  sliderPitch.addEventListener('input', () => {
    valPitch.textContent = sliderPitch.value;
  });

  sfxToggle.addEventListener('change', () => {
    sfxEnabled = sfxToggle.checked;
  });

  if (wakeWordCheckbox) {
    wakeWordCheckbox.addEventListener('change', () => {
      shiftOperatingMode(wakeWordCheckbox.checked ? 'wakeword' : 'text');
    });
  }

  if (btnBriefingNow) {
    btnBriefingNow.addEventListener('click', handleTriggerBriefing);
  }

  // Theme Pickers
  document.querySelectorAll('.theme-option').forEach(opt => {
    opt.addEventListener('click', () => {
      playSfx('click');
      document.querySelectorAll('.theme-option').forEach(o => o.classList.remove('active'));
      opt.classList.add('active');
      const theme = opt.getAttribute('data-theme');
      applyTheme(theme);
    });
  });

  // Password eye toggles
  document.querySelectorAll('.eye-toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        input.type = input.type === 'password' ? 'text' : 'password';
      }
    });
  });

  // Save Assistant Settings
  btnSave.addEventListener('click', async () => {
    playSfx('ping');
    const settings = {
      voice_enabled: document.getElementById('setting-voice-enabled').checked,
      voice_speed: parseInt(sliderRate.value, 10),
      voice_pitch: parseInt(sliderPitch.value, 10),
      sound_effects: sfxToggle.checked,
      wake_word_active: document.getElementById('setting-wakeword-enabled').checked,
      glow_theme: getActiveTheme()
    };

    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.save_assistant_settings(settings);
      } catch (e) {
        console.warn('Save settings API error:', e);
      }
    }

    const toast = document.getElementById('settings-toast');
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 2500);
  });

  // Save Full API Configuration (CLI replacement)
  if (btnSaveApi) {
    btnSaveApi.addEventListener('click', async () => {
      playSfx('ping');
      const apiConfig = {
        keys: {
          LLM_KEY: document.getElementById('cfg-llm-key').value.trim(),
          GEMINI_KEY: document.getElementById('cfg-gemini-key').value.trim(),
          WEATHER_KEY: document.getElementById('cfg-weather-key').value.trim(),
          TAVILY_API_KEY: document.getElementById('cfg-tavily-key').value.trim(),
          NEWS_API_KEY: document.getElementById('cfg-news-key').value.trim(),
          AGENT_PASSWORD: document.getElementById('cfg-agent-pass').value.trim()
        },
        llm: {
          LLM_SERVICE_PROVIDER_URL: document.getElementById('cfg-llm-url').value.trim(),
          MODEL: document.getElementById('cfg-llm-model').value.trim()
        }
      };

      if (window.pywebview && window.pywebview.api) {
        try {
          await window.pywebview.api.save_api_keys_config(apiConfig);
        } catch (e) {
          console.warn('Save API keys error:', e);
        }
      }

      const toast = document.getElementById('api-config-toast');
      if (toast) {
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 2500);
      }
    });
  }

  // Reset Settings
  btnReset.addEventListener('click', () => {
    playSfx('click');
    document.getElementById('setting-voice-enabled').checked = true;
    sliderRate.value = 185;
    valRate.textContent = '185';
    sliderPitch.value = 50;
    valPitch.textContent = '50';
    sfxToggle.checked = true;
    sfxEnabled = true;
    document.getElementById('setting-wakeword-enabled').checked = false;
    applyTheme('cyan');
  });
}

function applyTheme(themeName) {
  document.body.classList.remove('theme-cyan', 'theme-gold', 'theme-purple', 'theme-green');
  document.body.classList.add(`theme-${themeName}`);

  document.querySelectorAll('.theme-option').forEach(o => {
    if (o.getAttribute('data-theme') === themeName) {
      o.classList.add('active');
    } else {
      o.classList.remove('active');
    }
  });

  if (orbInstance) {
    orbInstance.setTheme(themeName);
  }
}

function getActiveTheme() {
  const activeOpt = document.querySelector('.theme-option.active');
  return activeOpt ? activeOpt.getAttribute('data-theme') : 'cyan';
}

async function loadAssistantSettings() {
  if (window.pywebview && window.pywebview.api) {
    try {
      const settings = await window.pywebview.api.get_assistant_settings();
      if (settings) {
        if ('voice_enabled' in settings) {
          isAudioActive = settings.voice_enabled;
          document.getElementById('setting-voice-enabled').checked = isAudioActive;
        }
        if ('voice_speed' in settings) {
          document.getElementById('setting-speech-rate').value = settings.voice_speed;
          document.getElementById('val-speech-rate').textContent = settings.voice_speed;
        }
        if ('voice_pitch' in settings) {
          document.getElementById('setting-speech-pitch').value = settings.voice_pitch;
          document.getElementById('val-speech-pitch').textContent = settings.voice_pitch;
        }
        if ('sound_effects' in settings) {
          sfxEnabled = settings.sound_effects;
          document.getElementById('setting-sfx-enabled').checked = sfxEnabled;
        }
        if ('wake_word_active' in settings) {
          document.getElementById('setting-wakeword-enabled').checked = settings.wake_word_active;
        }
        if ('glow_theme' in settings) {
          applyTheme(settings.glow_theme);
        }
      }
    } catch (e) {
      console.warn('Failed to load settings:', e);
    }
  }
}

async function loadApiKeysConfig() {
  if (window.pywebview && window.pywebview.api) {
    try {
      const cfg = await window.pywebview.api.get_api_keys_config();
      if (cfg) {
        const keys = cfg.keys || {};
        const llm = cfg.llm || {};
        if (keys.LLM_KEY) document.getElementById('cfg-llm-key').value = keys.LLM_KEY;
        if (keys.GEMINI_KEY) document.getElementById('cfg-gemini-key').value = keys.GEMINI_KEY;
        if (keys.WEATHER_KEY) document.getElementById('cfg-weather-key').value = keys.WEATHER_KEY;
        if (keys.TAVILY_API_KEY) document.getElementById('cfg-tavily-key').value = keys.TAVILY_API_KEY;
        if (keys.NEWS_API_KEY) document.getElementById('cfg-news-key').value = keys.NEWS_API_KEY;
        if (keys.AGENT_PASSWORD) document.getElementById('cfg-agent-pass').value = keys.AGENT_PASSWORD;

        if (llm.LLM_SERVICE_PROVIDER_URL) document.getElementById('cfg-llm-url').value = llm.LLM_SERVICE_PROVIDER_URL;
        if (llm.MODEL) document.getElementById('cfg-llm-model').value = llm.MODEL;
      }
    } catch (e) {
      console.warn('loadApiKeysConfig error:', e);
    }
  }
}

// ==========================================================================
// 7. USER PROFILE, REMINDERS & TASKS
// ==========================================================================
function setupProfileHandlers() {
  const btnSaveProfile = document.getElementById('btn-save-profile');
  const btnAddMemory = document.getElementById('btn-add-memory');
  const btnRefreshTasks = document.getElementById('btn-refresh-tasks');
  const btnSubmitTask = document.getElementById('btn-submit-task');

  btnSaveProfile.addEventListener('click', async () => {
    playSfx('ping');
    const name = document.getElementById('prof-input-name').value.trim();
    const email = document.getElementById('prof-input-email').value.trim();
    const phone = document.getElementById('prof-input-phone').value.trim();

    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.save_user_profile_data({ name, email, phone });
      } catch (e) {
        console.warn('Save profile API error:', e);
      }
    }

    if (name) {
      document.getElementById('profile-display-name').textContent = name;
    }

    const toast = document.getElementById('profile-toast');
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 2500);
  });

  btnAddMemory.addEventListener('click', async () => {
    playSfx('click');
    const textInput = document.getElementById('add-mem-text');
    const typeSelect = document.getElementById('add-mem-type');
    const text = textInput.value.trim();
    const memType = typeSelect.value;
    if (!text) return;

    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.add_user_memory(text, memType);
      } catch (e) {
        console.warn('Add memory API error:', e);
      }
    }

    textInput.value = '';
    loadUserProfile();
  });

  if (btnRefreshTasks) {
    btnRefreshTasks.addEventListener('click', () => {
      playSfx('click');
      loadRemindersAndTasks();
    });
  }

  if (btnSubmitTask) {
    btnSubmitTask.addEventListener('click', async () => {
      const taskInput = document.getElementById('add-task-text');
      const text = taskInput.value.trim();
      if (!text) return;
      playSfx('click');

      if (window.pywebview && window.pywebview.api) {
        try {
          await window.pywebview.api.add_task(text);
        } catch (e) {
          console.warn('add_task error:', e);
        }
      }
      taskInput.value = '';
      loadRemindersAndTasks();
    });
  }
}

async function loadUserProfile() {
  if (window.pywebview && window.pywebview.api) {
    try {
      const data = await window.pywebview.api.get_user_profile_data();
      if (data) {
        if (data.name) {
          document.getElementById('profile-display-name').textContent = data.name;
          document.getElementById('prof-input-name').value = data.name;
        }
        if (data.email) {
          document.getElementById('prof-input-email').value = data.email;
        }
        if (data.phone) {
          document.getElementById('prof-input-phone').value = data.phone;
        }
        if (data.device) {
          document.getElementById('profile-system-host').textContent = data.device;
        }

        renderMemoriesList(data.memories || {});
      }
    } catch (e) {
      console.warn('Failed to load user profile:', e);
    }
  }
}

async function loadRemindersAndTasks() {
  const container = document.getElementById('reminders-tasks-container');
  if (!container) return;

  if (window.pywebview && window.pywebview.api) {
    try {
      const res = await window.pywebview.api.get_reminders_and_tasks();
      container.innerHTML = '';
      const reminders = (res && res.reminders) || [];
      const tasks = (res && res.tasks) || [];

      if (reminders.length === 0 && tasks.length === 0) {
        container.innerHTML = `<div class="memory-empty-state">No reminders or tasks due. You can add one below!</div>`;
        return;
      }

      reminders.forEach(r => {
        const card = document.createElement('div');
        card.className = 'task-item-card';
        card.innerHTML = `
          <div class="task-item-left">
            <span>⏰</span>
            <span class="task-desc">${escapeHTML(r.reminder || r.text || '')}</span>
          </div>
          <span class="task-time-pill">${escapeHTML(r.remind_at || r.time || 'Scheduled')}</span>
        `;
        container.appendChild(card);
      });

      tasks.forEach(t => {
        const card = document.createElement('div');
        card.className = 'task-item-card';
        const taskText = typeof t === 'string' ? t : (t.task || t.name || '');
        card.innerHTML = `
          <div class="task-item-left">
            <span>✓</span>
            <span class="task-desc">${escapeHTML(taskText)}</span>
          </div>
          <span class="task-time-pill">Todo</span>
        `;
        container.appendChild(card);
      });
    } catch (e) {
      console.warn('loadRemindersAndTasks error:', e);
    }
  }
}

function renderMemoriesList(memories) {
  const container = document.getElementById('memory-items-list');
  const countBadge = document.getElementById('memory-count-badge');
  container.innerHTML = '';

  const items = [];
  if (memories.preferences) {
    Object.values(memories.preferences).forEach(v => items.push({ text: v, tag: 'preference' }));
  }
  if (memories.facts) {
    Object.values(memories.facts).forEach(v => items.push({ text: v, tag: 'fact' }));
  }
  if (memories.habits) {
    Object.values(memories.habits).forEach(v => items.push({ text: v, tag: 'habit' }));
  }
  if (memories.goals) {
    memories.goals.forEach(v => items.push({ text: typeof v === 'string' ? v : v.goal, tag: 'goal' }));
  }

  countBadge.textContent = `${items.length} Learned`;

  if (items.length === 0) {
    container.innerHTML = `<div class="memory-empty-state">No custom facts recorded yet. Teach Friday below!</div>`;
    return;
  }

  items.slice(-10).reverse().forEach(item => {
    const card = document.createElement('div');
    card.className = 'memory-item-card';
    card.innerHTML = `
      <span class="memory-item-text">${escapeHTML(item.text)}</span>
      <span class="memory-item-tag">${escapeHTML(item.tag)}</span>
    `;
    container.appendChild(card);
  });
}

// ==========================================================================
// 8. REALTIME SPEECH, TOOL CALLS & TELEMETRY
// ==========================================================================
window.fridayOnSpeechStart = function(previewText) {
  isAgentSpeaking = true;
  setOrbState('speaking', '⏹️ SPEAKING // CLICK TO STOP (Esc)');
  const preview = document.getElementById('speaking-preview-text');
  if (preview) {
    preview.textContent = '🔊 ' + (previewText || 'F.R.I.D.A.Y IS SPEAKING...');
  }
  const banner = document.getElementById('chat-interrupter-banner');
  if (banner) {
    banner.classList.remove('hidden');
  }
};

window.fridayOnSpeechEnd = function(interrupted) {
  isAgentSpeaking = false;
  const banner = document.getElementById('chat-interrupter-banner');
  if (banner) banner.classList.add('hidden');
  if (!isProcessing) {
    setOrbState('idle', interrupted ? 'INTERRUPTED // STANDBY' : 'F.R.I.D.A.Y STANDBY');
  }
};

window.fridayOnToolStart = function(toolName, args) {
  const banner = document.getElementById('tool-activity-banner');
  const toolNameText = document.getElementById('tool-name-text');
  if (toolNameText && banner) {
    toolNameText.textContent = `${toolName}(${JSON.stringify(args || {})})`;
    banner.classList.remove('hidden');
  }
  setOrbState('thinking', `RUNNING DIRECTIVE: ${toolName}`);
  if (orbInstance) {
    orbInstance.setState('thinking', toolName);
  }
};

window.fridayOnToolEnd = function(toolName, result) {
  const banner = document.getElementById('tool-activity-banner');
  setTimeout(() => {
    if (banner) banner.classList.add('hidden');
  }, 1000);
  if (!isAgentSpeaking && !isProcessing) {
    setOrbState('idle', 'F.R.I.D.A.Y STANDBY');
  }
};

async function fetchInitialTelemetry() {
  if (window.pywebview && window.pywebview.api) {
    try {
      const data = await window.pywebview.api.get_system_info();
      if (data) {
        if (data.battery) {
          document.getElementById('tel-battery').textContent = `BATTERY: ${data.battery}`;
        }
        if (data.status) {
          document.getElementById('tel-status').textContent = data.status;
        }
      }
    } catch (e) {
      console.warn('Failed to fetch telemetry:', e);
    }
  }
}

function setOrbState(state, label) {
  if (orbInstance) {
    orbInstance.setState(state, label);
  }

  // Toggle overdrive animation classes on Arc Reactor hero stage
  const stage = document.getElementById('arc-reactor-stage');
  if (stage) {
    stage.classList.remove('state-speaking', 'state-thinking', 'state-listening');
    if (state === 'speaking') {
      stage.classList.add('state-speaking');
    } else if (state === 'thinking') {
      stage.classList.add('state-thinking');
    } else if (state === 'listening') {
      stage.classList.add('state-listening');
    }
  }

  const badge = document.getElementById('orb-state-badge');
  const text = document.getElementById('orb-state-text');
  if (badge) {
    badge.className = 'arc-state-badge ' + state;
    if (state === 'speaking') {
      badge.title = 'Click to Stop / Interrupt Speech (or press Esc)';
    } else {
      badge.title = '';
    }
  }
  if (text) text.textContent = label;
}

// Global Interruption Hotkey (Esc, Ctrl+D) & Badge Click
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' || (e.ctrlKey && (e.key === 'd' || e.key === 'D'))) {
    if (isAgentSpeaking || isRecording) {
      e.preventDefault();
      interruptSpeech();
    }
  }
});

// Setup click on state badge to interrupt when speaking
setTimeout(() => {
  const badge = document.getElementById('orb-state-badge');
  if (badge) {
    badge.addEventListener('click', () => {
      if (isAgentSpeaking) {
        interruptSpeech();
      }
    });
  }
}, 500);

// ==========================================================================
// 9. CHAT HELPERS & RENDERING
// ==========================================================================
function appendUserMessage(text) {
  const container = document.getElementById('chat-messages');
  const row = document.createElement('div');
  row.className = 'message-row user-row';

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  row.innerHTML = `
    <div class="avatar-cell">
      <div class="user-avatar">U</div>
    </div>
    <div class="message-content">
      <div class="message-sender">YOU <span class="msg-time">${now}</span></div>
      <div class="message-bubble user-bubble">
        <p>${escapeHTML(text)}</p>
      </div>
    </div>
  `;

  container.appendChild(row);
  scrollToBottom();
}

function appendAssistantMessage(text) {
  const container = document.getElementById('chat-messages');
  const row = document.createElement('div');
  row.className = 'message-row assistant-row';

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const formattedHtml = formatMarkdown(text);

  row.innerHTML = `
    <div class="avatar-cell">
      <div class="assistant-avatar">
        <span class="avatar-glow"></span>
        <span class="avatar-letter">F</span>
      </div>
    </div>
    <div class="message-content">
      <div class="message-sender">F.R.I.D.A.Y <span class="msg-time">${now}</span></div>
      <div class="message-bubble assistant-bubble">
        ${formattedHtml}
      </div>
    </div>
  `;

  container.appendChild(row);
  scrollToBottom();
}

function clearChatMessages() {
  const container = document.getElementById('chat-messages');
  container.innerHTML = `
    <div class="message-row assistant-row">
      <div class="avatar-cell">
        <div class="assistant-avatar">
          <span class="avatar-glow"></span>
          <span class="avatar-letter">F</span>
        </div>
      </div>
      <div class="message-content">
        <div class="message-sender">F.R.I.D.A.Y <span class="msg-time">Just now</span></div>
        <div class="message-bubble assistant-bubble">
          <p>Chat buffer cleared, Sir. Standing by for instructions.</p>
        </div>
      </div>
    </div>
  `;
}

function scrollToBottom() {
  const viewport = document.getElementById('chat-viewport');
  if (!viewport) return;
  setTimeout(() => {
    viewport.scrollTop = viewport.scrollHeight;
  }, 50);
}

function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatMarkdown(text) {
  if (!text) return '';
  let str = escapeHTML(text);

  str = str.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  str = str.replace(/`(.*?)`/g, '<code class="inline-code">$1</code>');
  str = str.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

  const paragraphs = str.split(/\n\s*\n/);
  return paragraphs.map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
}
