"""Download PDFs and store with content hash; skip unchanged."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

import requests

from core.discover import content_hash_bytes


def download_pdf(
    url: str,
    dest_dir: Path,
    timeout: int = 60,
) -> Tuple[Optional[Path], Optional[str], Optional[bytes]]:
    """
    Download PDF from url into dest_dir. Filename from URL.
    Returns (file_path, content_hash, raw_bytes) or (None, None, None) on failure.
    """
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        data = r.content
    except Exception:
        return None, None, None

    content_hash = content_hash_bytes(data)
    # Filename: use last part of URL or hash
    name = url.rstrip("/").split("/")[-1].split("?")[0] or f"{content_hash[:12]}.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    dest_dir.mkdir(parents=True, exist_ok=True)
    file_path = dest_dir / name
    file_path.write_bytes(data)
    return file_path, content_hash, data


def get_dest_dir(base: Path, source_name: str) -> Path:
    """Return data/source_name for storing PDFs."""
    return base / "pdfs" / source_name
