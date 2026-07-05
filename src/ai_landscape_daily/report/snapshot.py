from __future__ import annotations

import asyncio
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def create_snapshot(overview_path: Path, output_path: Path) -> Path | None:
    try:
        import playwright.async_api  # noqa: F401
    except ImportError:
        output_path.write_bytes(_placeholder_png())
        return output_path

    try:
        return asyncio.run(_capture(overview_path, output_path))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Snapshot generation failed: %s", exc)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(_placeholder_png())
        return output_path


async def _capture(overview_path: Path, output_path: Path) -> Path:
    from playwright.async_api import async_playwright

    output_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 1200}, device_scale_factor=1)
        await page.goto(overview_path.resolve().as_uri(), wait_until="networkidle")
        await page.screenshot(path=str(output_path), full_page=True)
        await browser.close()
    return output_path


def _placeholder_png() -> bytes:
    # 1x1 transparent PNG used when Playwright is not installed.
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000a49444154789c6360000002000100ffff03000006000557bfab0d000000"
        "0049454e44ae426082"
    )
