import difflib
import re
from typing import Dict, Any, Tuple, Optional, List
from pydantic import BaseModel, Field
from app.services.ocr.normalization import (
    normalize_text,
    normalize_name,
    normalize_pincode,
    normalize_address_text,
    normalize_address_components,
    convert_devanagari_digits,
    is_devanagari_text,
)


class FieldComparisonResult(BaseModel):
    field: str
    source_value: str  # Application value
    target_value: str  # Extracted OCR value
    normalized_source: str
    normalized_target: str
    status: str  # MATCH, PARTIAL_MATCH, MISMATCH, UNAVAILABLE, NOT_EXTRACTED
    score: float = 0.0  # 0.0 to 1.0
    method: str = "exact"  # exact, token_overlap, fuzzy_similarity, initials_match, script_difference, strict_pincode
    explanation: str = ""


class DocumentComparisonResult(BaseModel):
    overall_status: str  # VALIDATED, PARTIAL_MATCH, MISMATCH, INVALID, MISSING, LOW_CONFIDENCE
    overall_score: float = 0.0
    field_results: Dict[str, FieldComparisonResult] = Field(default_factory=dict)
    matched_fields: List[str] = Field(default_factory=list)
    partial_fields: List[str] = Field(default_factory=list)
    mismatched_fields: List[str] = Field(default_factory=list)
    unavailable_fields: List[str] = Field(default_factory=list)
    explanation: str = ""
    normalization_notes: List[str] = Field(default_factory=list)


def compute_string_similarity(str1: str, str2: str) -> float:
    """Computes normalized Levenshtein-like similarity ratio (0.0 to 1.0)."""
    if not str1 and not str2:
        return 1.0
    if not str1 or not str2:
        return 0.0
    return difflib.SequenceMatcher(None, str1, str2).ratio()


def check_initials_compatibility(norm_a: str, norm_b: str) -> bool:
    """
    Checks if one name is an initialed version of the other.
    e.g. "R S Patil" vs "Rajesh Shantaram Patil" or "Dhinith P" vs "Dhinith Pragalyan"
    """
    tokens_a = norm_a.split()
    tokens_b = norm_b.split()

    if len(tokens_a) != len(tokens_b) or len(tokens_a) < 2:
        return False

    matched_tokens = 0
    for ta, tb in zip(tokens_a, tokens_b):
        if ta == tb:
            matched_tokens += 1
        elif len(ta) == 1 and tb.startswith(ta):
            matched_tokens += 1
        elif len(tb) == 1 and ta.startswith(tb):
            matched_tokens += 1
        else:
            return False

    return matched_tokens == len(tokens_a)


def compare_name(app_name: str, doc_name: str) -> Dict[str, Any]:
    """
    Compares application citizen name with OCR extracted name.
    Supports Unicode NFC, Marathi honorifics, Devanagari text, initials, token overlap,
    and bilingual script difference handling.
    """
    raw_app = (app_name or "").strip()
    raw_doc = (doc_name or "").strip()

    n_app = normalize_name(raw_app)
    n_doc = normalize_name(raw_doc)

    if not n_doc or n_doc in ("n a", "not extracted", "n/a"):
        explanation = "Citizen name was not extracted from document OCR."
        return {
            "result": "NOT_EXTRACTED",
            "status": "NOT_EXTRACTED",
            "score": 0.0,
            "application_value": raw_app,
            "document_value": raw_doc or "N/A",
            "normalized_source": n_app,
            "normalized_target": n_doc,
            "method": "not_extracted",
            "explanation": explanation,
        }

    if not n_app:
        explanation = "Application citizen name is empty or not specified."
        return {
            "result": "UNAVAILABLE",
            "status": "UNAVAILABLE",
            "score": 0.0,
            "application_value": raw_app,
            "document_value": raw_doc,
            "normalized_source": n_app,
            "normalized_target": n_doc,
            "method": "unavailable",
            "explanation": explanation,
        }

    # 1. Exact normalized match
    if n_app == n_doc:
        explanation = "Name matched exactly after honorific and whitespace normalization."
        return {
            "result": "MATCH",
            "status": "MATCH",
            "score": 1.0,
            "application_value": raw_app,
            "document_value": raw_doc,
            "normalized_source": n_app,
            "normalized_target": n_doc,
            "method": "exact_normalized",
            "explanation": explanation,
        }

    # 2. Bilingual Script Difference Handling
    app_is_dev = is_devanagari_text(raw_app) or is_devanagari_text(n_app)
    doc_is_dev = is_devanagari_text(raw_doc) or is_devanagari_text(n_doc)

    if app_is_dev != doc_is_dev:
        explanation = (
            f"Script difference detected: Application name is in {'Devanagari' if app_is_dev else 'English'} "
            f"while document name is in {'Devanagari' if doc_is_dev else 'English'}. "
            "Automatic transliteration skipped for statutory safety; officer verification required."
        )
        return {
            "result": "PARTIAL_MATCH",
            "status": "PARTIAL_MATCH",
            "score": 0.50,
            "application_value": raw_app,
            "document_value": raw_doc,
            "normalized_source": n_app,
            "normalized_target": n_doc,
            "method": "script_difference",
            "explanation": explanation,
        }

    # 3. Initials Compatibility Check
    if check_initials_compatibility(n_app, n_doc):
        explanation = f"Name partially matched via initials compatibility ('{n_app}' vs '{n_doc}')."
        return {
            "result": "PARTIAL_MATCH",
            "status": "PARTIAL_MATCH",
            "score": 0.88,
            "application_value": raw_app,
            "document_value": raw_doc,
            "normalized_source": n_app,
            "normalized_target": n_doc,
            "method": "initials_compatibility",
            "explanation": explanation,
        }

    # 4. Token Overlap & Fuzzy Similarity
    tokens_app = set(n_app.split())
    tokens_doc = set(n_doc.split())
    overlap = tokens_app.intersection(tokens_doc)

    ratio = compute_string_similarity(n_app, n_doc)
    overlap_ratio = len(overlap) / max(len(tokens_app), 1)

    if overlap_ratio >= 0.65 or ratio >= 0.85:
        match_res = "MATCH"
        final_score = max(ratio, overlap_ratio)
        explanation = f"Name matched with high token overlap ({len(overlap)} tokens matched)."
        method = "token_overlap"
    elif overlap_ratio >= 0.33 or ratio >= 0.60:
        match_res = "PARTIAL_MATCH"
        final_score = max(ratio, overlap_ratio)
        explanation = f"Name partially matched ({len(overlap)} of {len(tokens_app)} tokens matched)."
        method = "partial_token_overlap"
    else:
        match_res = "MISMATCH"
        final_score = ratio
        explanation = f"Name discrepancy detected: Application citizen name ('{raw_app}') differs from document name ('{raw_doc}')."
        method = "fuzzy_mismatch"

    return {
        "result": match_res,
        "status": match_res,
        "score": round(final_score, 2),
        "application_value": raw_app,
        "document_value": raw_doc,
        "normalized_source": n_app,
        "normalized_target": n_doc,
        "method": method,
        "explanation": explanation,
    }


def compare_pincode(app_pincode: str, doc_pincode: str) -> Dict[str, Any]:
    """
    Compares application postal PIN code against document PIN code strictly.
    Supports both ASCII and Devanagari numerals.
    """
    raw_app = (app_pincode or "").strip()
    raw_doc = (doc_pincode or "").strip()

    n_app = normalize_pincode(raw_app)
    n_doc = normalize_pincode(raw_doc)

    if not n_doc:
        return {
            "result": "NOT_EXTRACTED",
            "status": "NOT_EXTRACTED",
            "score": 0.0,
            "requested": raw_app,
            "extracted": raw_doc or "Not Extracted",
            "normalized_source": n_app,
            "normalized_target": n_doc,
            "method": "not_extracted",
            "explanation": "PIN code was not extracted from document OCR.",
        }

    if not n_app:
        return {
            "result": "MATCH",
            "status": "MATCH",
            "score": 1.0,
            "requested": raw_app or "N/A",
            "extracted": raw_doc,
            "normalized_source": n_app,
            "normalized_target": n_doc,
            "method": "implicit_match",
            "explanation": "PIN code not specified in application; document PIN accepted.",
        }

    # Compare numeric 6-digit PIN codes
    if n_app == n_doc:
        doc_had_dev = is_devanagari_text(raw_doc)
        method = "devanagari_numeral_equivalence" if doc_had_dev else "strict_exact"
        explanation = (
            "PIN code matched exactly after Devanagari numeral conversion."
            if doc_had_dev
            else "PIN code matched exactly."
        )
        return {
            "result": "MATCH",
            "status": "MATCH",
            "score": 1.0,
            "requested": raw_app,
            "extracted": raw_doc,
            "normalized_source": n_app,
            "normalized_target": n_doc,
            "method": method,
            "explanation": explanation,
        }
    else:
        explanation = f"PIN code mismatch: Application PIN '{n_app}' differs from document PIN '{n_doc}'."
        return {
            "result": "MISMATCH",
            "status": "MISMATCH",
            "score": 0.0,
            "requested": raw_app,
            "extracted": raw_doc,
            "normalized_source": n_app,
            "normalized_target": n_doc,
            "method": "strict_pincode_mismatch",
            "explanation": explanation,
        }


def compare_address_components(
    requested_addr: Dict[str, Any],
    extracted_fields: Dict[str, Any],
    raw_ocr_text: str = "",
) -> Dict[str, Dict[str, Any]]:
    """
    Compares 6-part departmental address components against extracted fields / raw OCR text:
    house_no, street, village, taluka, district, pincode.
    Handles Devanagari numerals, address markers (Gat No, Survey No, Rd, St), and bilingual scripts.
    """
    norm_req = normalize_address_components(requested_addr)
    norm_raw = normalize_address_text(raw_ocr_text)

    components = ["house_no", "street", "village", "taluka", "district", "pincode"]
    results: Dict[str, Dict[str, Any]] = {}

    for comp in components:
        req_val = requested_addr.get(comp, "") if requested_addr else ""
        n_req = norm_req.get(comp, "")
        raw_comp_val = extracted_fields.get(comp, "") if extracted_fields else ""

        # Special handling for pincode
        if comp == "pincode":
            results["pincode"] = compare_pincode(str(req_val), str(raw_comp_val or ""))
            continue

        doc_val = normalize_address_text(str(raw_comp_val)) if raw_comp_val else ""

        # If individual component wasn't extracted, check raw OCR text
        if not doc_val and n_req:
            if n_req in norm_raw:
                doc_val = n_req

        if not n_req:
            results[comp] = {
                "result": "MATCH",
                "status": "MATCH",
                "score": 1.0,
                "requested": req_val or "N/A",
                "extracted": raw_comp_val or "Implicit / Not specified",
                "normalized_source": n_req,
                "normalized_target": doc_val,
                "method": "implicit_match",
                "explanation": f"{comp.replace('_', ' ').title()} not specified in application; document component accepted.",
            }
            continue

        if not doc_val or doc_val in ("n a", "not extracted", "n/a"):
            results[comp] = {
                "result": "NOT_EXTRACTED",
                "status": "NOT_EXTRACTED",
                "score": 0.0,
                "requested": req_val or "N/A",
                "extracted": "Not Extracted",
                "normalized_source": n_req,
                "normalized_target": doc_val,
                "method": "not_extracted",
                "explanation": f"{comp.replace('_', ' ').title()} was not extracted from document OCR.",
            }
            continue

        # Check script difference for village/taluka/district
        req_is_dev = is_devanagari_text(str(req_val))
        doc_is_dev = is_devanagari_text(str(raw_comp_val)) or is_devanagari_text(doc_val)

        # Number discrepancy check: if both fields contain numbers (e.g. Gat No 123 vs Gat No 132), numbers must match!
        req_digits = re.findall(r"\d+", n_req)
        doc_digits = re.findall(r"\d+", doc_val)
        number_discrepancy = bool(req_digits and doc_digits and req_digits != doc_digits)

        # 1. Exact normalized match or marker equivalence match
        if not number_discrepancy and (n_req == doc_val or n_req in doc_val or doc_val in n_req or (norm_raw and n_req in norm_raw)):
            sim = 1.0
            match_status = "MATCH"
            method = "exact_address_marker_match"
            explanation = f"{comp.replace('_', ' ').title()} matched exactly ('{req_val}')."
        elif number_discrepancy:
            sim = 0.0
            match_status = "MISMATCH"
            method = "number_discrepancy_mismatch"
            explanation = f"{comp.replace('_', ' ').title()} number discrepancy: Application '{req_val}' differs from document '{raw_comp_val}'."
        elif req_is_dev != doc_is_dev and not (n_req in doc_val or doc_val in n_req):
            sim = 0.50
            match_status = "PARTIAL_MATCH"
            method = "bilingual_script_difference"
            explanation = (
                f"{comp.replace('_', ' ').title()} script difference: "
                f"Application is in {'Devanagari' if req_is_dev else 'English'} ('{req_val}') "
                f"while document is in {'Devanagari' if doc_is_dev else 'English'} ('{raw_comp_val}')."
            )
        else:
            sim = compute_string_similarity(n_req, doc_val)
            if sim >= 0.80:
                match_status = "MATCH"
                method = "fuzzy_similarity"
                explanation = f"{comp.replace('_', ' ').title()} matched with high similarity ({round(sim*100)}%)."
            elif sim >= 0.50:
                match_status = "PARTIAL_MATCH"
                method = "partial_similarity"
                explanation = f"{comp.replace('_', ' ').title()} partially matched ({round(sim*100)}%)."
            else:
                match_status = "MISMATCH"
                method = "address_mismatch"
                explanation = f"{comp.replace('_', ' ').title()} mismatch: Application '{req_val}' differs from document '{raw_comp_val}'."

        results[comp] = {
            "result": match_status,
            "status": match_status,
            "score": round(sim, 2),
            "requested": req_val,
            "extracted": raw_comp_val or doc_val,
            "normalized_source": n_req,
            "normalized_target": doc_val,
            "method": method,
            "explanation": explanation,
        }

    return results


def compute_assistive_score(
    name_eval: Dict[str, Any],
    address_comp_eval: Dict[str, Dict[str, Any]],
) -> Tuple[float, int, int]:
    """
    Computes weighted assist score and matched component counts.
    Total items = 7 (1 name + 6 address components).
    Preserves exact backward compatibility with existing callers.
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
    elif name_eval.get("result") == "PARTIAL_MATCH":
        if name_eval.get("method") == "script_difference":
            partial_matches.append("Citizen Name (Script Difference)")
        else:
            partial_matches.append("Citizen Name")
    elif name_eval.get("result") == "MATCH":
        matches.append("Citizen Name")

    for comp, info in comp_eval.items():
        c_name = comp.replace("_", " ").title()
        if info.get("result") == "MISMATCH":
            mismatches.append(f"{c_name} (Document: '{info.get('extracted')}', Requested: '{info.get('requested')}')")
        elif info.get("result") == "PARTIAL_MATCH":
            partial_matches.append(c_name)
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

    return "Bilingual AI/OCR verification passed: Citizen name, Taluka jurisdiction, and address components match municipal proof document."
