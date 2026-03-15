"""Tests for discover module (can mock requests)."""
import pytest
from unittest.mock import patch, MagicMock

from core.discover import content_hash_bytes, discover_all


def test_content_hash_bytes():
    h = content_hash_bytes(b"hello")
    assert len(h) == 64
    assert h == content_hash_bytes(b"hello")
    assert h != content_hash_bytes(b"world")


def test_discover_all_mock():
    """With no network, discover_all may fail or return []; we just check it returns a list."""
    with patch("core.discover._soup") as mock_soup:
        mock_soup.return_value = MagicMock()
        mock_soup.return_value.find_all.return_value = []
        from core.discover import discover_oilgasdata
        out = discover_oilgasdata("https://example.com/OilGasData")
        assert isinstance(out, list)
