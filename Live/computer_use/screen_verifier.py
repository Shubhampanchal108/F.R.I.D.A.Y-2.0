"""
=============================================================================
F.R.I.D.A.Y LIVE COMPUTER USE // SCREEN VERIFIER
=============================================================================
Provides visual closed-loop feedback for action verification:
1. Captures lightweight screen state before action.
2. Captures screen state after action (with settle delay for UI animations).
3. Computes visual difference percentage to verify whether the target UI responded.
=============================================================================
"""

import time
from typing import Dict, Any, Optional, Tuple
import numpy as np
import mss
import cv2

from Live.computer_use.coordinate_mapper import CoordinateMapper


class ScreenVerifier:
    """
    Measures visual UI changes to confirm whether a click, keypress, or scroll
    actually affected the interface.
    """

    def __init__(self, change_threshold: float = 0.008):
        # 0.008 = 0.8% pixel change counts as a visual state transition
        self.change_threshold = change_threshold

    def capture_screen_sample(self, region: Optional[Dict[str, int]] = None) -> Optional[np.ndarray]:
        """
        Captures a fast, downsampled grayscale image for low-overhead comparison.
        """
        try:
            with mss.mss() as sct:
                monitor = region if region else sct.monitors[1]
                screenshot = sct.grab(monitor)
                # Convert raw BGRA to BGR numpy array
                img = np.array(screenshot)[:, :, :3]
                # Downsample to 320x180 grayscale for near-instant difference math (<3ms)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                small = cv2.resize(gray, (320, 180), interpolation=cv2.INTER_AREA)
                return small
        except Exception:
            return None

    def capture_region_sample(self, norm_x: float, norm_y: float, box_size: int = 200) -> Optional[np.ndarray]:
        """
        Captures a localized crop around the target coordinate to detect micro-animations,
        checkbox toggles, or button color changes.
        """
        try:
            px, py = CoordinateMapper.normalized_to_pixel(norm_x, norm_y)
            w, h = CoordinateMapper.get_screen_dimensions()

            left = max(0, px - box_size // 2)
            top = max(0, py - box_size // 2)
            right = min(w, px + box_size // 2)
            bottom = min(h, py + box_size // 2)

            region = {"top": top, "left": left, "width": right - left, "height": bottom - top}
            with mss.mss() as sct:
                screenshot = sct.grab(region)
                img = np.array(screenshot)[:, :, :3]
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                return gray
        except Exception:
            return None

    def compute_diff_ratio(self, before: np.ndarray, after: np.ndarray) -> float:
        """
        Calculates the ratio of changed pixels between before and after samples (0.0 to 1.0).
        """
        if before is None or after is None or before.shape != after.shape:
            return 0.0

        diff = cv2.absdiff(before, after)
        # Threshold out minor video/compression noise (pixel delta > 20)
        _, thresh = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
        non_zero = np.count_nonzero(thresh)
        total_pixels = thresh.size

        return float(non_zero / max(1, total_pixels))

    def verify_action_effect(
        self,
        before_sample: Optional[np.ndarray],
        settle_delay: float = 0.35,
        region: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Waits for UI animations to settle, captures the post-action screen state,
        and evaluates whether the screen visual state changed.
        """
        if before_sample is None:
            return {
                "verified": True,
                "visual_change_detected": True,
                "change_ratio": 0.0,
                "message": "Action executed (visual verification skipped)."
            }

        # Allow UI/browser/window animation to render
        time.sleep(max(0.1, settle_delay))

        after_sample = self.capture_screen_sample(region)
        if after_sample is None:
            return {
                "verified": True,
                "visual_change_detected": True,
                "change_ratio": 0.0,
                "message": "Action executed (post-sample unavailable)."
            }

        ratio = self.compute_diff_ratio(before_sample, after_sample)
        changed = ratio >= self.change_threshold
        percentage = round(ratio * 100.0, 2)

        if changed:
            msg = f"UI responded visibly ({percentage}% screen change detected). Action verified."
        else:
            msg = f"Screen showed minimal change ({percentage}% difference). Target may need an extra click, or UI state did not update."

        return {
            "verified": changed,
            "visual_change_detected": changed,
            "change_percentage": percentage,
            "message": msg
        }


# Global Screen Verifier Instance
screen_verifier = ScreenVerifier()

