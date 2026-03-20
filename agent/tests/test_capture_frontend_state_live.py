"""
Standalone smoke-test for the Playwright screenshot pipeline.

Runs outside ADK — no ToolContext, no artifact service.
Saves the screenshot directly to /tmp/snapshot_test.png so you can open it.

Usage (from the agent/ directory):
    uv run python tests/test_capture_frontend_state_live.py

Flags (edit at the top of the file):
    HEADLESS = False  →  browser window opens on screen so you can watch it
    RENDER_WAIT = 3   →  seconds to wait after page load before screenshot

What it tests:
  [1] Chromium binary is installed and can launch
  [2] The Graphivac view URL is reachable (wait_until="load")
  [3] Canvas has time to render (explicit sleep)
  [4] A non-empty PNG is produced
  [5] Timing breakdown for each step
"""

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ── Config ────────────────────────────────────────────────────────────────────
HEADLESS = True       # Set False to open a visible browser window for debugging
RENDER_WAIT = 3       # Seconds to wait after load before screenshot
SNAPSHOTS_DIR = Path(__file__).parent.parent.parent / "mapper" / "uploads" / "snapshots"
# ─────────────────────────────────────────────────────────────────────────────


def _build_url() -> str:
    base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id = os.getenv("GRAPHIVAC_GRID_ID", "")
    site_url = base_url.replace("/api/v1", "")
    return f"{site_url}/o/{org_id}/p/{project_id}/g/{grid_id}?iframe=t&init-zoom=t"


def _fmt(seconds: float) -> str:
    return f"{seconds:.2f}s"


async def run():
    from playwright.async_api import async_playwright

    url = _build_url()
    mode = "headless" if HEADLESS else "VISIBLE (browser will open on screen)"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = SNAPSHOTS_DIR / f"snapshot_{timestamp}.png"

    print(f"\n  URL    : {url}")
    print(f"  Mode   : {mode}")
    print(f"  Sleep  : {RENDER_WAIT}s after load")
    print(f"  Output : {output_path}\n")

    total_start = time.perf_counter()

    # ── Step 1: launch browser ────────────────────────────────────────────────
    print(f"[1/4] Launching Chromium ({mode})...")
    t0 = time.perf_counter()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        t1 = time.perf_counter()
        print(f"      ✓ Browser launched  ({_fmt(t1 - t0)})")

        # ── Step 2: navigate ──────────────────────────────────────────────────
        print(f"[2/4] Navigating to URL (wait_until=load)...")
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        t2 = time.perf_counter()
        try:
            await page.goto(url, wait_until="load", timeout=30_000)
        except Exception as e:
            print(f"      ✗ Navigation failed: {e}")
            await browser.close()
            return
        t3 = time.perf_counter()
        print(f"      ✓ Page loaded       ({_fmt(t3 - t2)})")

        # ── Step 3: wait for canvas render ────────────────────────────────────
        print(f"[3/4] Waiting {RENDER_WAIT}s for canvas to render...")
        await asyncio.sleep(RENDER_WAIT)
        print(f"      ✓ Done waiting")

        # ── Step 4: screenshot ────────────────────────────────────────────────
        print("[4/4] Taking screenshot...")
        t4 = time.perf_counter()
        png_bytes = await page.screenshot(full_page=True)
        await browser.close()
        t5 = time.perf_counter()
        print(f"      ✓ Screenshot taken  ({_fmt(t5 - t4)})")

    total = time.perf_counter() - total_start

    # ── Results ───────────────────────────────────────────────────────────────
    size_kb = len(png_bytes) / 1024
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Timestamped copy — full history for human review
    output_path.write_bytes(png_bytes)

    # Fixed-name copy — mirrors what the agent artifact "verification/latest_snapshot.png" contains
    latest_fixed = SNAPSHOTS_DIR / "latest_snapshot.png"
    latest_fixed.write_bytes(png_bytes)

    all_snapshots = sorted(SNAPSHOTS_DIR.glob("snapshot_*.png"))

    print(f"""
┌──────────────────────────────────────────────────────────┐
│  RESULTS                                                 │
├──────────────────────────────────────────────────────────┤
│  PNG size      : {size_kb:>8.1f} KB                           │
│  Total time    : {_fmt(total):>8}                           │
│  Timestamped   : {output_path.name:<38} │
│  Agent mirror  : latest_snapshot.png (always overwritten) │
│  Total snaps   : {len(all_snapshots):<38} │
└──────────────────────────────────────────────────────────┘
""")

    if len(png_bytes) < 5_000:
        print("  ⚠ WARNING: PNG is very small — canvas may not have rendered (blank/error page).")
    else:
        print(f"  ✓ Screenshot looks valid.")
        print(f"  → Human review : mapper/uploads/snapshots/{output_path.name}")
        print(f"  → Agent sees   : mapper/uploads/snapshots/latest_snapshot.png")


if __name__ == "__main__":
    asyncio.run(run())
