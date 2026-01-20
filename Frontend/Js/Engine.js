document.addEventListener("DOMContentLoaded", () => {
  // --- Element References ---
  const currentTimeEl = document.getElementById("current-time");
  const currentDateEl = document.getElementById("current-date");
  
  const muteBtn = document.getElementById("mute-btn");
  const muteText = document.getElementById("mute-text");
  const visualizer = document.getElementById("visualizer");
  const videoFeed = document.getElementById("video-feed");
  const cameraFeed = document.getElementById("camera-feed");
  const cameraPlaceholder = document.getElementById("camera-placeholder");
  const cameraBtn = document.getElementById("camera-btn");
  const cameraText = document.getElementById("camera-text");
  const logContainer = document.getElementById("log-container");

  // --- State Management ---
  
  let isMuted = false;
  let isCameraOn = false;
  let videoStream = null;
  let conversation = [
    {
      type: "F.R.I.D.A.Y",
      text: "hello",
      time: new Date(),
    },
    { type: "user", text: "Run a full system diagnostic.", time: new Date() },
  ];

  // --- Render System Status HTML structure once ---
async function setupSystemStatus() {
  let systemStatus = await eel.get_system_status()(); 

  const systemStatusContainer = document.getElementById("system-status-container");
  systemStatusContainer.innerHTML = "";
  
  Object.keys(systemStatus).forEach((key) => {
    const item = systemStatus[key]
    const itemHTML = `
      <div class="status-item" id="status-${key}">
        <div class="labels">
          <span class="name">${systemStatus[key].name}</span>
          <span class="value">${systemStatus[key].value}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${systemStatus[key].value}%;"></div>
        </div>
      </div>
    `;
    systemStatusContainer.innerHTML += itemHTML;
  });
}

setInterval(setupSystemStatus, 2000);
setupSystemStatus();



  // --- Simulation and Update Functions ---
  function updateTime() {
    const now = new Date();
    currentTimeEl.textContent = now.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    currentDateEl.textContent = now.toLocaleDateString("en-IN", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  function renderConversation() {
    logContainer.innerHTML = "";
    conversation.forEach((msg) => {
      const msgDiv = document.createElement("div");
      msgDiv.className = `log-message ${msg.type}`;
      msgDiv.innerHTML = `
                        <div class="sender">${
                          msg.type === "jarvis" ? "J.A.R.V.I.S" : "YOU"
                        }</div>
                        <div>${msg.text}</div>
                        <div class="time">${msg.time.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}</div>
                    `;
      logContainer.appendChild(msgDiv);
    });
    logContainer.scrollTop = logContainer.scrollHeight;
  }

  function updateMuteUI() {
    if (isMuted) {
      muteBtn.style.borderColor = "var(--yellow)";
      muteBtn.style.color = "var(--yellow)";
      muteText.textContent = "Unmute";
    } else {
      muteBtn.style.borderColor = "";
      muteBtn.style.color = "";
      muteText.textContent = "Mute";
    }
  }

  function updateCameraUI() {
    cameraFeed.classList.toggle("active", isCameraOn);
    videoFeed.style.display = isCameraOn ? "block" : "none";
    cameraPlaceholder.style.display = isCameraOn ? "none" : "block";
    if (isCameraOn) {
      cameraBtn.style.borderColor = "var(--red)";
      cameraBtn.style.color = "var(--red)";
      cameraText.textContent = "Stop Camera";
    } else {
      cameraBtn.style.borderColor = "";
      cameraBtn.style.color = "";
      cameraText.textContent = "Start Camera";
    }
  }

  async function toggleCamera() {
    if (isCameraOn) {
      videoStream.getTracks().forEach((track) => track.stop());
      videoStream = null;
      isCameraOn = false;
    } else {
      try {
        videoStream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
        videoFeed.srcObject = videoStream;
        isCameraOn = true;
      } catch (err) {
        console.error("Camera access denied:", err);
        cameraPlaceholder.textContent = "Camera Access Denied";
      }
    }
    updateCameraUI();
  }

  // --- Initial Setup and Intervals ---
  setupSystemStatus();
  renderConversation();
  updateTime();
  setInterval(updateTime, 1000);

  // --- Event Listeners ---
  muteBtn.addEventListener("click", () => {
    isMuted = !isMuted;
    updateMuteUI();
  });
  cameraBtn.addEventListener("click", toggleCamera);
});