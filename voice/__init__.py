"""
F.R.I.D.A.Y Voice & Audio Engine Package
========================================
TTS speech playback, microphone recording, wake-word detection, and natural speech fillers.
"""

from voice.speak import (
    speak,
    speak_alert,
    interrupt_speech,
    set_voice_enabled,
    is_voice_enabled,
    set_authenticated,
    is_authenticated,
    register_speech_callback,
)
stop_speak = interrupt_speech

from voice.voice_input import SpeechRecognition
speech_recognition = SpeechRecognition

from voice.wake_word import WakeWordListener, extract_command
Wake_word_detector = WakeWordListener

from voice.instant_filler import (
    trigger_instant_filler,
    stop_instant_filler,
    is_filler_busy,
    select_filler_key,
)
play_instant_filler = trigger_instant_filler
is_filler_playing = is_filler_busy

__all__ = [
    "speak",
    "speak_alert",
    "interrupt_speech",
    "stop_speak",
    "set_voice_enabled",
    "is_voice_enabled",
    "set_authenticated",
    "is_authenticated",
    "register_speech_callback",
    "SpeechRecognition",
    "speech_recognition",
    "WakeWordListener",
    "Wake_word_detector",
    "extract_command",
    "trigger_instant_filler",
    "play_instant_filler",
    "stop_instant_filler",
    "is_filler_busy",
    "is_filler_playing",
    "select_filler_key",
]
