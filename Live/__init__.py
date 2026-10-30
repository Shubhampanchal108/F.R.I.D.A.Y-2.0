"""
=============================================================================
F.R.I.D.A.Y LIVE MULTIMODAL VISION & AUDIO PACKAGE
=============================================================================
Package providing real-time streaming, tools schemas, audio/vision I/O,
and synchronization with Core Friday.
=============================================================================
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()
DEFAULT_MODE = "screen"


def run_live_mode(video_mode="screen"):
    """
    Launch F.R.I.D.A.Y's Real-Time Live Multimodal Vision & Audio Protocol.
    video_mode: 'screen' (desktop screen reading) | 'camera' (webcam vision) | 'none' (audio-only)
    """
    from Live.live_session import LiveSession, LIVE_MODELS

    mode_name = "🖥️ REAL-TIME SCREEN STREAM" if video_mode == "screen" else "📷 REAL-LIFE WEBCAM STREAM" if video_mode == "camera" else "🎙️ REAL-TIME AUDIO"

    live_panel = Panel(
        f"[bold bright_cyan]⚡ F.R.I.D.A.Y LIVE MULTIMODAL VISION SYSTEM ACTIVATED ⚡[/bold bright_cyan]\n\n"
        f"[bold white]Visual Mode:[/bold white] [bold bright_green]{mode_name}[/bold bright_green]\n"
        f"[bold white]Audio Stream:[/bold white] [bold bright_green]Bidirectional Real-Time Audio (Zephyr Neural Voice)[/bold bright_green]\n"
        f"[bold white]Core Sync:[/bold white] [bold bright_green]Active ⚡ (Connected with Core Memory, Tasks, Reminders & Sentinel Alerts)[/bold bright_green]\n"
        f"[bold white]Live Tools:[/bold white] [bold bright_green]Active ⚡ (Full Tools Suite + Visual Computer Use Agent)[/bold bright_green]\n"
        f"[bold white]Gemini Model:[/bold white] [dim]{LIVE_MODELS[0]}[/dim]\n\n"
        f"[bold yellow]Instructions:[/bold yellow]\n"
        f" • Speak directly into your microphone or type in the input bar below to talk to FRIDAY.\n"
        f" • Friday can see your {'screen in real time' if video_mode == 'screen' else 'webcam in real time'}.\n"
        f" • Friday can execute actions (open apps, screenshots, volume, files, computer use click/type) in real time.\n"
        f" • Sentinel alerts from Core Friday (battery, reminders, emails) will be announced proactively.\n"
        f" • Type [bold red]'stop'[/bold red] or [bold red]'exit'[/bold red] or press [bold red]Ctrl+C[/bold red] to return to FRIDAY HUD.",
        title="[bold magenta]👁️ F.R.I.D.A.Y VISION HUB 👁️[/bold magenta]",
        box=box.DOUBLE,
        border_style="bright_magenta"
    )
    console.print(live_panel)

    session = LiveSession(video_mode=video_mode)
    try:
        asyncio.run(session.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Live session stopped by user (Ctrl+C).[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Live Mode session error: {e}[/red]")


def __getattr__(name: str):
    """Lazy export loader to avoid heavy PyTorch/ChromaDB initialization during subpackage imports."""
    if name in ["LiveSession", "LIVE_MODELS"]:
        from Live.live_session import LiveSession, LIVE_MODELS
        return LiveSession if name == "LiveSession" else LIVE_MODELS
    elif name in ["LIVE_TOOLS", "get_live_tools"]:
        from Live.tools_schema import LIVE_TOOLS, get_live_tools
        return LIVE_TOOLS if name == "LIVE_TOOLS" else get_live_tools
    elif name == "FridayBridge":
        from Live.bridge import FridayBridge
        return FridayBridge
    elif name == "VisionStreamer":
        from Live.vision_stream import VisionStreamer
        return VisionStreamer
    elif name == "AudioStreamer":
        from Live.audio_stream import AudioStreamer
        return AudioStreamer
    raise AttributeError(f"module 'Live' has no attribute '{name}'")


__all__ = [
    "run_live_mode",
    "LiveSession",
    "FridayBridge",
    "VisionStreamer",
    "AudioStreamer",
    "get_live_tools",
    "LIVE_TOOLS"
]
