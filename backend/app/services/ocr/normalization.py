import re
import unicodedata
from typing import Dict, Any, Optional

DEVANAGARI_DIGITS = "०१२३४५६७८९"
ASCII_DIGITS = "0123456789"
DEV_TO_ASCII_NUMS = str.maketrans(DEVANAGARI_DIGITS, ASCII_DIGITS)

# Common Marathi / Devanagari & English honorific prefixes in Indian government records
HONORIFICS_EN = r"\b(shri|smt|mr|mrs|ms|dr|late|kumari|advocate|adv)\b"
HONORIFICS_MAR = (
    r"(?:^|\s+)(?:श्रीमती|श्री|कैलासवासी|कै\.|कै|डॉक्टर|डॉ\.|डॉ|माननीय|मा\.|मा|कुमारी|कु\.|सौ\.|सौ)(?:\.|\s+|$)"
)

# Common Indian address marker equivalences for normalization
ADDRESS_MARKERS_MAP = [
    (r"(?:^|\s+)(?:gat\s*no\.?|gat\s*number|गट\s*क्र\.?|गट\s*क्रमांक|गट\s*नं\.?)(?:\.|\s+|$)", " gat no "),
    (r"(?:^|\s+)(?:survey\s*no\.?|survey\s*number|s\.?\s*no\.?|सर्व्हे\s*नं\.?|सर्व्हे\s*क्र\.?)(?:\.|\s+|$)", " survey no "),
    (r"(?:^|\s+)(?:plot\s*no\.?|plot\s*number|प्लॉट\s*नं\.?|प्लॉट\s*क्र\.?)(?:\.|\s+|$)", " plot no "),
    (r"(?:^|\s+)(?:flat\s*no\.?|flat\s*number|फ्लॅट\s*नं\.?)(?:\.|\s+|$)", " flat no "),
    (r"(?:^|\s+)(?:house\s*no\.?|house\s*number|घर\s*क्र\.?|घर\s*नं\.?)(?:\.|\s+|$)", " house no "),
    (r"(?:^|\s+)(?:road|rd\.?)(?:\.|\s+|$)", " road "),
    (r"(?:^|\s+)(?:street|st\.?)(?:\.|\s+|$)", " street "),
    (r"(?:^|\s+)(?:chawl|चाळ)(?:\.|\s+|$)", " chawl "),
    (r"(?:^|\s+)(?:wadi|वाडी)(?:\.|\s+|$)", " wadi "),
]


def is_devanagari_text(text: Optional[str]) -> bool:
    """Checks if text contains any Devanagari characters (Unicode range U+0900 to U+097F)."""
    if not text:
        return False
    return bool(re.search(r"[\u0900-\u097F]", text))


def convert_devanagari_digits(text: Optional[str]) -> str:
    """
    Translates Devanagari digits (०१२३४५६७८९) to standard ASCII digits (0123456789).
    Leaves non-digit characters unchanged.
    Used for NUMERIC COMPARISON ONLY.
    """
    if not text:
        return ""
    return str(text).translate(DEV_TO_ASCII_NUMS)


def normalize_unicode(text: Optional[str]) -> str:
    """Applies Unicode NFC normalization and strips zero-width spaces."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFC", str(text))
    # Strip zero-width space (\u200B) and byte-order mark (\uFEFF)
    return norm.replace("\u200b", "").replace("\ufeff", "")


def normalize_whitespace(text: Optional[str]) -> str:
    """Collapses newlines, tabs, non-breaking spaces (\u00A0), and multiple spaces into a single space."""
    if not text:
        return ""
    return re.sub(r"[\s\u00a0]+", " ", str(text)).strip()


def normalize_punctuation(text: Optional[str]) -> str:
    """
    Removes excessive punctuation (including ASCII punctuation and Devanagari dandas । U+0964, ॥ U+0965)
    while retaining all letters, digits, and single spaces.
    """
    if not text:
        return ""
    cleaned = re.sub(r"[,\.:\-_/\(\)\[\]\{\}\\\|\u0964\u0965'\"]+", " ", str(text))
    return normalize_whitespace(cleaned)


def normalize_case(text: Optional[str]) -> str:
    """Converts Latin characters to lowercase while leaving Devanagari characters intact."""
    if not text:
        return ""
    return str(text).lower()


def normalize_text(text: Optional[str]) -> str:
    """
    Standardize general text:
    - Unicode NFC normalization
    - Case normalization (lowercase for Latin)
    - Punctuation removal (retaining letters, digits, spaces)
    - Whitespace collapsing
    """
    if not text:
        return ""
    step1 = normalize_unicode(text)
    step2 = normalize_case(step1)
    step3 = normalize_punctuation(step2)
    return normalize_whitespace(step3)


def normalize_name(name: Optional[str]) -> str:
    """
    Normalizes names by removing common Indian government honorifics
    in English (Shri, Smt, Mr, Mrs, Late, Kumari, Adv) and Marathi/Devanagari
    (श्री, श्रीमती, सौ, कु, कै, डॉ, माननीय) and standardizing whitespace.
    """
    if not name:
        return ""

    raw_norm = normalize_unicode(name)

    # Remove Marathi honorifics first (before punctuation removal)
    raw_norm = re.sub(HONORIFICS_MAR, " ", raw_norm)

    cleaned = normalize_text(raw_norm)

    # Remove English honorifics
    cleaned = re.sub(HONORIFICS_EN, "", cleaned)

    return normalize_whitespace(cleaned)


def normalize_pincode(pincode: Optional[str]) -> str:
    """
    Extracts standard 6-digit Indian Postal PIN code.
    Supports both ASCII (0-9) and Devanagari (०-९) digits.
    Converts Devanagari numerals to ASCII for strict comparison.
    """
    if not pincode:
        return ""

    raw_str = normalize_unicode(pincode)
    ascii_str = convert_devanagari_digits(raw_str)

    match = re.search(r"\b[1-9]\d{5}\b", ascii_str)
    if match:
        return match.group(0)

    # Fallback to any 6 digits
    any_six = re.search(r"\b\d{6}\b", ascii_str)
    if any_six:
        return any_six.group(0)

    # Final fallback: strip non-digits
    digits = re.sub(r"\D", "", ascii_str)
    return digits[:6] if len(digits) >= 6 else digits


def normalize_address_text(address: Optional[str]) -> str:
    """
    Normalizes address text including common Indian address markers
    (Gat No, Survey No, S.No, Plot No, Rd/Road, St/Street, Chawl, Wadi).
    Converts Devanagari digits to ASCII digits for comparison.
    """
    if not address:
        return ""

    norm = normalize_unicode(address)
    norm = convert_devanagari_digits(norm)
    norm = normalize_case(norm)

    # Apply address marker equivalences before punctuation stripping
    for pattern, replacement in ADDRESS_MARKERS_MAP:
        norm = re.sub(pattern, replacement, norm, flags=re.IGNORECASE)

    norm = normalize_punctuation(norm)
    return normalize_whitespace(norm)


def normalize_address_components(addr: Dict[str, Any]) -> Dict[str, str]:
    """
    Normalizes 6-part address model components:
    house_no, street, village, taluka, district, pincode.
    Handles both Latin and Devanagari values.
    """
    return {
        "house_no": normalize_address_text(addr.get("house_no", "")),
        "street": normalize_address_text(addr.get("street", "")),
        "village": normalize_text(addr.get("village", "")),
        "taluka": normalize_text(addr.get("taluka", "")),
        "district": normalize_text(addr.get("district", "")),
        "pincode": normalize_pincode(addr.get("pincode", "")),
    }
