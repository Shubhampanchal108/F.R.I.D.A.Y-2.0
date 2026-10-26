"""
=============================================================================
F.R.I.D.A.Y 2.0 // LIVE MULTIMODAL STREAMING MODE
=============================================================================
Facade module that delegates to the modular Live package.
Maintains 100% backward compatibility with CLI, scripts, and widget UI.
=============================================================================
"""

import sys
import argparse
import warnings

# Suppress noisy warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*non-text parts.*")

from Live import run_live_mode, LiveSession, LIVE_TOOLS, get_live_tools

DEFAULT_MODE = "screen"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FRIDAY Live Multimodal Vision Mode")
    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        help="Pixels to stream from: screen, camera, none",
        choices=["camera", "screen", "none"],
    )
    args = parser.parse_args()
    run_live_mode(video_mode=args.mode)
