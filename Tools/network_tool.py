"""
F.R.I.D.A.Y // Network & Internet Health Diagnostic Tool
Checks ping latency, internet connectivity, download bandwidth (Mbps), and connection health.
"""

import time
import subprocess
import requests
import re


def check_network_health() -> dict:
    """
    Performs a fast network health test:
    - Measures ping latency to DNS root (8.8.8.8 / 1.1.1.1)
    - Measures real download bandwidth (Mbps)
    - Evaluates connection stability and speed grade
    """
    # 1. Ping Latency Check
    ping_ms = None
    is_online = False
    try:
        res = subprocess.run(["ping", "-n", "2", "8.8.8.8"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            is_online = True
            # Extract average latency: "Average = 24ms"
            m = re.search(r'Average\s*=\s*(\d+)\s*ms', res.stdout, re.IGNORECASE)
            if m:
                ping_ms = int(m.group(1))
            else:
                m_alt = re.findall(r'time[=<](\d+)ms', res.stdout, re.IGNORECASE)
                if m_alt:
                    ping_ms = int(sum(int(x) for x in m_alt) / len(m_alt))
    except Exception:
        pass

    if not is_online:
        return {
            "status": "offline",
            "online": False,
            "message": "Device appears to be offline or has no DNS reachability.",
            "latency_ms": None,
            "download_mbps": 0.0,
            "quality": "Disconnected"
        }

    # 2. Fast Download Bandwidth Test via Cloudflare Speed CDN (1 MB payload)
    download_mbps = None
    try:
        t0 = time.time()
        resp = requests.get("https://speed.cloudflare.com/__down?bytes=1000000", timeout=6)
        elapsed = time.time() - t0
        if resp.status_code == 200 and elapsed > 0:
            bytes_received = len(resp.content)
            # (bytes * 8) / (seconds * 1,000,000) = Mbps
            download_mbps = round((bytes_received * 8) / (elapsed * 1024 * 1024), 2)
    except Exception:
        pass

    # 3. Connection Quality Grade
    quality = "Optimal"
    if download_mbps is not None:
        if download_mbps >= 25:
            quality = "Superfast (Fiber grade)"
        elif download_mbps >= 10:
            quality = "Good (Streaming & browsing ready)"
        elif download_mbps >= 2:
            quality = "Moderate"
        else:
            quality = "Slow / Congested"
    elif ping_ms and ping_ms < 50:
        quality = "Good Latency"
    else:
        quality = "Connected"

    summary = (
        f"Internet is connected. Latency: {ping_ms} ms. "
        f"Download Speed: {download_mbps} Mbps ({quality})."
        if download_mbps is not None
        else f"Internet is connected with {ping_ms} ms latency."
    )

    return {
        "status": "online",
        "online": True,
        "message": summary,
        "latency_ms": ping_ms,
        "download_mbps": download_mbps,
        "quality": quality
    }
