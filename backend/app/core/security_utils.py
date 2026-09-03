"""
security_utils.py — Phase 09 Step 04: SEC-04, SEC-05 hardening utilities.

Provides:
- sanitize_svg_text: Escapes XML/SVG special characters and strips control characters.
- validate_file_magic_bytes: Verifies binary magic signatures (PDF, PNG, JPEG).
- validate_filename_safety: Guards against path traversal, null bytes, control chars, excess length.
"""
import re
import unicodedata
from typing import Tuple

# ---------------------------------------------------------------------------
# Magic-byte signatures for supported document types (SEC-04)
# ---------------------------------------------------------------------------
_MAGIC_SIGNATURES = {
    "application/pdf": b"%PDF-",
    "image/jpeg": b"\xFF\xD8\xFF",
    "image/jpg": b"\xFF\xD8\xFF",
    "image/png": b"\x89PNG\r\n\x1a\n",
}

# Control character regex (exclude printable + standard whitespace)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Path traversal patterns
_PATH_TRAVERSAL_RE = re.compile(r"(\.\.[/\\]|[/\\]\.\.)")


def sanitize_svg_text(value: object) -> str:
    """
    Escape a value for safe embedding in SVG text nodes and attributes.

    Performs:
    - str() coercion
    - XML entity escaping: & < > " '
    - Control character removal (preserves legitimate Unicode, tabs, newlines stripped)
    """
    s = str(value) if value is not None else ""
    # Remove control characters that are invalid in XML/SVG
    s = _CONTROL_CHAR_RE.sub("", s)
    # Standard XML entity escaping (order matters: & must be first)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    s = s.replace("'", "&#39;")
    return s


def validate_file_magic_bytes(content: bytes, declared_mime: str, filename: str) -> Tuple[bool, str]:
    """
    Verify that file binary content matches declared MIME type magic bytes.

    Returns (True, "") on success.
    Returns (False, reason) if content does not match the declared MIME type.

    Supported MIME types: application/pdf, image/jpeg, image/jpg, image/png.
    For unknown/unsupported MIME types, validation passes (enforcement done at MIME allow-list layer).
    """
    if not content:
        return False, f"File '{filename}' is empty."

    expected_magic = _MAGIC_SIGNATURES.get(declared_mime.lower())
    if expected_magic is None:
        # Not a type we validate with magic bytes — pass through
        return True, ""

    if content[: len(expected_magic)] == expected_magic:
        return True, ""

    # Detailed rejection reason (safe — no binary data exposed)
    return (
        False,
        f"File '{filename}' claims to be '{declared_mime}' but binary signature does not match. "
        f"Possible MIME type spoofing — upload rejected.",
    )


def validate_filename_safety(filename: str) -> str:
    r"""
    Validate and sanitize an uploaded filename.

    Raises ValueError with a descriptive reason on rejection.
    Returns the original filename string if validation passes.

    Rules enforced:
    - Not blank
    - Length ≤ 255 characters
    - No null bytes (\x00)
    - No control characters
    - No path traversal sequences (.. / \\ variants)
    - No absolute path separators (leading / or \)
    """
    if not filename or not filename.strip():
        raise ValueError("Filename must not be empty.")

    if len(filename) > 255:
        raise ValueError(
            f"Filename exceeds maximum length of 255 characters (got {len(filename)})."
        )

    if "\x00" in filename:
        raise ValueError("Filename contains null bytes — rejected.")

    if _CONTROL_CHAR_RE.search(filename):
        raise ValueError("Filename contains control characters — rejected.")

    if _PATH_TRAVERSAL_RE.search(filename):
        raise ValueError(
            f"Filename '{filename}' contains path traversal sequences — rejected."
        )

    if filename.startswith("/") or filename.startswith("\\"):
        raise ValueError(
            f"Filename '{filename}' starts with an absolute path separator — rejected."
        )

    return filename
