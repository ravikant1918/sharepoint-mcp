"""Unit tests for utils/parsers.py — pure functions, no mocks needed."""
from __future__ import annotations

import pytest

from mcp_sharepoint.utils.parsers import detect_file_type


class TestDetectFileType:
    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("report.pdf", "pdf"),
            ("data.xlsx", "excel"),
            ("data.xls", "excel"),
            ("letter.docx", "word"),
            ("notes.txt", "text"),
            ("config.json", "text"),
            ("page.html", "text"),
            ("script.py", "text"),
            ("image.png", "binary"),
            ("archive.zip", "binary"),
            ("REPORT.PDF", "pdf"),          # case-insensitive
            ("My File.DOCX", "word"),       # upper-case extension
        ],
    )
    def test_detect(self, filename: str, expected: str) -> None:
        assert detect_file_type(filename) == expected
