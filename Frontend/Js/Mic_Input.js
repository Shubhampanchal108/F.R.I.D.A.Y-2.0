const listenBtn = document.getElementById("listen-btn");
const listenText = document.getElementById("listen-text");
const muteBtn = document.getElementById("mute-btn");

let isListening = false;

// Update UI based on state
function updateListeningUI() {
  if (isListening) {
    listenBtn.classList.add("listening");
    listenBtn.classList.remove("stopped");
    listenText.textContent = "Listening...";
  } else {
    listenBtn.classList.remove("listening");
    listenBtn.classList.add("stopped");
    listenText.textContent = "Start Listening";
  }
}

// Start listening
function startListening() {
  isListening = true;
  updateListeningUI();
  // eel.MicStatus(true); // Uncomment this when using eel
}

// Stop listening
function stopListening() {
  isListening = false;
  updateListeningUI();
  eel.MicStatus(false);
}

// Toggle listening state
function toggleListening() {
  isListening = !isListening;
  updateListeningUI();
  eel.MicStatus(isListening);
}

// Event listeners
listenBtn.addEventListener("click", toggleListening);

muteBtn.addEventListener("click", () => {
  stopListening();
});

// Initial UI setup
document.addEventListener("DOMContentLoaded", () => {
  updateListeningUI();
});

eel.MicStatus(isListening)
