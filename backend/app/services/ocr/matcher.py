import difflib
from typing import Dict, Any, Tuple, Optional
from app.services.ocr.normalization import (
    normalize_text,
    normalize_name,
    normalize_pincode,
    normalize_address_components,
)


def compute_string_similarity(str1: str, str2: str) -> float:
    """Computes normalized Levenshtein-like similarity ratio (0.0 to 1.0)."""
    if not str1 and not str2:
        return 1.0
    if not str1 or not str2:
        return 0.0
    return difflib.SequenceMatcher(None, str1, str2).ratio()


def compare_name(app_name: str, doc_name: str) -> Dict[str, Any]:
    """
    Compares application citizen name with OCR extracted name.
    """
    n_app = normalize_name(app_name)
    n_doc = normalize_name(doc_name)

    if not n_doc or n_doc == "n a" or n_doc == "not extracted":
        return {
            "result": "NOT_EXTRACTED",
            "score": 0.0,
            "application_value": app_name,
            "document_value": doc_name or "N/A",
        }

    # Direct substring or exact match
    if n_app == n_doc:
        return {
            "result": "MATCH",
            "score": 1.0,
            "application_value": app_name,
            "document_value": doc_name,
        }

    # Token overlap check (handles order variations like "Patil Rajesh S" vs "Rajesh Shantaram Patil")
    tokens_app = set(n_app.split())
    tokens_doc = set(n_doc.split())
    overlap = tokens_app.intersection(tokens_doc)

    ratio = compute_string_similarity(n_app, n_doc)
    overlap_ratio = len(overlap) / max(len(tokens_app), 1)

    if overlap_ratio >= 0.65 or ratio >= 0.85:
        match_res = "MATCH"
        final_score = max(ratio, overlap_ratio)
    elif overlap_ratio >= 0.33 or ratio >= 0.60:
        match_res = "PARTIAL_MATCH"
        final_score = max(ratio, overlap_ratio)
    else:
        match_res = "MISMATCH"
        final_score = ratio

    return {
        "result": match_res,
        "score": round(final_score, 2),
        "application_value": app_name,
        "document_value": doc_name,
    }


def compare_address_components(
    requested_addr: Dict[str, Any],
    extracted_fields: Dict[str, Any],
    raw_ocr_text: str = "",
) -> Dict[str, Dict[str, Any]]:
    """
    Compares 6-part departmental address components against extracted fields / raw OCR text:
    house_no, street, village, taluka, district, pincode.
    """
    norm_req = normalize_address_components(requested_addr)
    norm_raw = normalize_text(raw_ocr_text)

    components = ["house_no", "street", "village", "taluka", "district", "pincode"]
    results: Dict[str, Dict[str, Any]] = {}

    for comp in components:
        req_val = norm_req.get(comp, "")
        raw_comp_val = extracted_fields.get(comp, "")
        doc_val = normalize_text(str(raw_comp_val)) if raw_comp_val else ""

        # If individual component wasn't extracted, check raw OCR text
        if not doc_val and req_val:
            if req_val in norm_raw:
                doc_val = req_val

        if not req_val:
            results[comp] = {
                "result": "MATCH",
                "score": 1.0,
                "requested": requested_addr.get(comp, "N/A"),
                "extracted": raw_comp_val or "Implicit / Not specified",
            }
            continue

        if not doc_val or doc_val in ("n a", "not extracted"):
            results[comp] = {
                "result": "NOT_EXTRACTED",
                "score": 0.0,
                "requested": requested_addr.get(comp, "N/A"),
                "extracted": "Not Extracted",
            }
            continue

        # Exact match or substring containment in text
        if req_val == doc_val or req_val in doc_val or doc_val in req_val or req_val in norm_raw:
            sim = 1.0
            match_status = "MATCH"
        else:
            sim = compute_string_similarity(req_val, doc_val)
            if sim >= 0.80:
                match_status = "MATCH"
            elif sim >= 0.50:
                match_status = "PARTIAL_MATCH"
            else:
                match_status = "MISMATCH"

        results[comp] = {
            "result": match_status,
            "score": round(sim, 2),
            "requested": requested_addr.get(comp, ""),
            "extracted": raw_comp_val or doc_val,
        }

    return results


def compute_assistive_score(
    name_eval: Dict[str, Any],
    address_comp_eval: Dict[str, Dict[str, Any]],
) -> Tuple[float, int, int]:
    """
    Computes weighted assist score and matched component counts.
    Total items = 7 (1 name + 6 address components).
    """
    total_items = 1 + len(address_comp_eval)
    matched_count = 0
    score_sum = 0.0

    # Name weight = 1.0
    if name_eval.get("result") == "MATCH":
        matched_count += 1
        score_sum += 1.0
    elif name_eval.get("result") == "PARTIAL_MATCH":
        matched_count += 0.5
        score_sum += 0.6
    else:
        score_sum += 0.0

    # Component weights
    for comp, comp_res in address_comp_eval.items():
        res = comp_res.get("result")
        if res == "MATCH":
            matched_count += 1
            score_sum += 1.0
        elif res == "PARTIAL_MATCH":
            matched_count += 0.5
            score_sum += 0.6
        else:
            score_sum += 0.0

    overall_score = round(score_sum / max(total_items, 1), 2)
    return overall_score, int(matched_count), total_items


def generate_verification_explanation(
    name_eval: Dict[str, Any],
    comp_eval: Dict[str, Dict[str, Any]],
    overall_status: str,
    custom_details: Optional[str] = None,
) -> str:
    """
    Generates explainable rationale detailing exactly which fields match or mismatch.
    """
    if custom_details and len(custom_details.strip()) > 0:
        return custom_details

    mismatches = []
    partial_matches = []
    matches = []

    if name_eval.get("result") == "MISMATCH":
        mismatches.append(f"Citizen Name (Document: '{name_eval.get('document_value')}', Requested: '{name_eval.get('application_value')}')")
    elif name_eval.get("result") == "MATCH":
        matches.append("Citizen Name")

    for comp, info in comp_eval.items():
        c_name = comp.replace("_", " ").title()
        if info.get("result") == "MISMATCH":
            mismatches.append(f"{c_name} (Document: '{info.get('extracted')}', Requested: '{info.get('requested')}')")
        elif info.get("result") == "PARTIAL_MATCH":
            partial_matches.append(f"{c_name}")
        elif info.get("result") == "MATCH":
            matches.append(c_name)

    if overall_status == "MISSING":
        return "No supporting proof documents attached to application. Officer action required to request document from citizen."

    if overall_status == "INVALID":
        return "Supporting document is corrupt, unreadable, or in an unsupported format."

    if mismatches:
        mismatch_str = "; ".join(mismatches)
        return f"Discrepancy detected in supporting document: {mismatch_str}. Officer scrutiny required."

    if partial_matches:
        partial_str = ", ".join(partial_matches)
        return f"Partial match observed in: {partial_str}. Document addresses appear consistent with minor formatting differences."

    return "Simulated AI/OCR verification passed: Citizen name, Taluka jurisdiction, and address components match municipal proof document."
