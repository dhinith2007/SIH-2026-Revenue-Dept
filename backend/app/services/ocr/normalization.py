import re
from typing import Dict, Any, Optional


def normalize_text(text: Optional[str]) -> str:
    """
    Standardize text: lower-casing, collapse whitespace, strip edge spaces.
    """
    if not text:
        return ""
    # Collapse multiple whitespaces and newlines
    cleaned = re.sub(r"\s+", " ", text.strip().lower())
    # Remove excessive punctuation while retaining letters and numbers
    cleaned = re.sub(r"[,\.:\-_/]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_name(name: Optional[str]) -> str:
    """
    Normalizes names by removing common Indian government honorifics
    (Shri, Smt, Mr, Mrs, Late) and standardizing token order.
    """
    if not name:
        return ""
    cleaned = normalize_text(name)
    # Remove common honorific prefixes
    cleaned = re.sub(r"\b(shri|smt|mr|mrs|ms|dr|late|kumari)\b", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_pincode(pincode: Optional[str]) -> str:
    """
    Extracts standard 6-digit Indian Postal PIN code.
    """
    if not pincode:
        return ""
    match = re.search(r"\b\d{6}\b", str(pincode))
    if match:
        return match.group(0)
    # Fallback to stripped digits
    digits = re.sub(r"\D", "", str(pincode))
    return digits[:6] if len(digits) >= 6 else digits


def normalize_address_components(addr: Dict[str, Any]) -> Dict[str, str]:
    """
    Normalizes 6-part address model components:
    house_no, street, village, taluka, district, pincode.
    """
    return {
        "house_no": normalize_text(addr.get("house_no", "")),
        "street": normalize_text(addr.get("street", "")),
        "village": normalize_text(addr.get("village", "")),
        "taluka": normalize_text(addr.get("taluka", "")),
        "district": normalize_text(addr.get("district", "")),
        "pincode": normalize_pincode(addr.get("pincode", "")),
    }
