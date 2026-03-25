"""
citizen_report.py — PRAMAAN v5
Citizen field report: photo upload → structural check → GPS check →
Groq Vision AI classification → Neo4j dispute flag.
"""
import os
import io
import base64
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse
from PIL import Image
import numpy as np
from groq import Groq

from app.neo4j_client import get_session

log = logging.getLogger("pramaan.citizen_report")
router = APIRouter(prefix="/citizen", tags=["citizen_report"])

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

SCHEME_ASSETS = {
    "SCH_AMRUT": {
        "name": "AMRUT 2.0 — Storm Water Drainage",
        "assets": [
            {"id": "ASSET_DRAIN_W45_GALI7",  "label": "Ward 45 · Gali 7 Storm Drain",  "ward": "Ward 45", "status": "completed"},
            {"id": "ASSET_DRAIN_W45_GALI12", "label": "Ward 45 · Gali 12 Storm Drain", "ward": "Ward 45", "status": "completed"},
            {"id": "ASSET_DRAIN_W46",        "label": "Ward 46 · Storm Drain",         "ward": "Ward 46", "status": "in_progress"},
        ],
    },
    "SCH_PMAY": {
        "name": "PMAY-U — Housing for All",
        "assets": [
            {"id": "ASSET_PMAY_W45_BLOCK_A", "label": "Ward 45 · PMAY Block A (17,067 units)", "ward": "Ward 45", "status": "completed"},
        ],
    },
    "SCH_SBM": {
        "name": "SBM Urban 2.0 — Sanitation",
        "assets": [
            {"id": "ASSET_TOILET_W45", "label": "Ward 45 · Community Toilet Complex", "ward": "Ward 45", "status": "completed"},
        ],
    },
}


# ── Layer 1: Structural checks ────────────────────────────────────────────────
def _basic_image_checks(file_bytes: bytes) -> tuple[bool, str]:
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
    except Exception:
        return False, "File is corrupted or not a valid image (JPEG/PNG/WebP only)."

    img = Image.open(io.BytesIO(file_bytes))
    w, h = img.size

    if w < 300 or h < 300:
        return False, f"Image too small ({w}×{h}px). Minimum 300×300px — please upload a real field photo."

    if h > 0 and (h / w) > 2.2:
        return False, "Image looks like a selfie (very tall/narrow). Please upload a photo showing the infrastructure or damage."

    arr = np.array(img.convert("L"))
    if arr.std() < 7.0:
        return False, "Image appears blank or solid colour. Please upload a photo with visible content."

    return True, "ok"


# ── Layer 2: GPS sanity ───────────────────────────────────────────────────────
def _validate_gps(lat: float, lon: float) -> tuple[bool, str]:
    if lat == 0.0 and lon == 0.0:
        return True, "GPS not provided — skipped."
    if not (6.0 <= lat <= 38.0 and 68.0 <= lon <= 98.0):
        return False, (
            f"GPS ({lat:.4f}, {lon:.4f}) is outside India. "
            "Please enable location access or enter correct coordinates."
        )
    return True, "ok"


# ── Layer 3: Groq Vision AI ───────────────────────────────────────────────────
def _classify_with_groq(file_bytes: bytes, scheme_name: str, ward: str) -> tuple[bool, str, str]:
    if not GROQ_API_KEY:
        return True, "SKIPPED_NO_KEY", "AI classification skipped (no Groq key)."

    client = Groq(api_key=GROQ_API_KEY)
    b64 = base64.b64encode(file_bytes).decode()
    prompt = (
        f"This photo is a citizen field report for government scheme '{scheme_name}' in '{ward}', India.\n\n"
        "Classify as EXACTLY ONE:\n"
        "  VALID_INFRASTRUCTURE  — road, drain, toilet, building, streetlight, construction site\n"
        "  VALID_DAMAGE          — flood, landslide, waterlogging, collapsed structure, visible damage\n"
        "  INVALID_SELFIE        — person's face is the main subject\n"
        "  INVALID_IRRELEVANT    — meme, screenshot, cartoon, food, indoor scene unrelated to infrastructure\n"
        "  INVALID_BLANK         — dark, blurry, blank, no meaningful content\n\n"
        "Reply ONLY with:\nDECISION: <category>\nREASON: <one sentence>"
    )
    try:
        resp = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": prompt},
            ]}],
            max_tokens=80,
            temperature=0,
        )
        text = resp.choices[0].message.content or ""
        decision, reason = "INVALID_IRRELEVANT", "AI could not classify the image."
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("DECISION:"):
                decision = line.split(":", 1)[1].strip()
            elif line.startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()
        return decision.startswith("VALID_"), decision, reason
    except Exception as exc:
        log.warning("[citizen_report] Groq Vision error: %s", exc)
        return True, "GROQ_ERROR", f"AI check skipped: {exc}"


# ── Neo4j: create Evidence node + flag Asset as disputed ─────────────────────
def _flag_dispute_in_neo4j(
    report_id: str, asset_id: str, event_id: str, scheme_id: str,
    ward: str, lat: float, lon: float, description: str, ai_decision: str,
) -> bool:
    cypher = """
    MERGE (ev:Evidence {id: $report_id})
    SET ev.type        = 'citizen_photo',
        ev.source      = 'citizen_upload',
        ev.title       = $title,
        ev.description = $description,
        ev.ward        = $ward,
        ev.latitude    = $lat,
        ev.longitude   = $lon,
        ev.ai_decision = $ai_decision,
        ev.status      = 'needs_review',
        ev.confidence  = 'pending',
        ev.uploaded_at = $uploaded_at
    WITH ev
    OPTIONAL MATCH (ast:Asset {id: $asset_id})
    FOREACH (_ IN CASE WHEN ast IS NOT NULL THEN [1] ELSE [] END |
        MERGE (ast)-[:HAS_DISPUTE]->(ev)
        SET ast.has_dispute    = true,
            ast.dispute_status = 'citizen_raised'
    )
    WITH ev
    OPTIONAL MATCH (e:Event {id: $event_id})
    FOREACH (_ IN CASE WHEN e IS NOT NULL THEN [1] ELSE [] END |
        MERGE (e)-[:HAS_EVIDENCE]->(ev)
    )
    WITH ev
    OPTIONAL MATCH (s:Scheme {id: $scheme_id})
    FOREACH (_ IN CASE WHEN s IS NOT NULL THEN [1] ELSE [] END |
        MERGE (s)-[:HAS_CITIZEN_REPORT]->(ev)
    )
    RETURN ev.id AS created
    """
    try:
        with get_session() as session:
            result = session.run(cypher, {
                "report_id":   report_id,
                "asset_id":    asset_id,
                "event_id":    event_id,
                "scheme_id":   scheme_id,
                "title":       f"Citizen Dispute — {ward}",
                "description": description or "No description provided.",
                "ward":        ward,
                "lat":         lat,
                "lon":         lon,
                "ai_decision": ai_decision,
                "uploaded_at": datetime.utcnow().isoformat(),
            })
            return result.single() is not None
    except Exception as exc:
        log.error("[citizen_report] Neo4j flag error: %s", exc)
        return False


# ── GET /citizen/schemes ──────────────────────────────────────────────────────
@router.get("/schemes")
def get_schemes():
    return SCHEME_ASSETS


# ── POST /citizen/report ──────────────────────────────────────────────────────
@router.post("/report")
async def submit_citizen_report(
    photo:       UploadFile = File(...),
    asset_id:    str        = Form(default=""),
    event_id:    str        = Form(default="EVT_DELHI_FLOODS_2023"),
    scheme_id:   str        = Form(default="SCH_AMRUT"),
    ward:        str        = Form(default="Unknown Ward"),
    description: str        = Form(default=""),
    latitude:    float      = Form(default=0.0),
    longitude:   float      = Form(default=0.0),
):
    # File type check
    if photo.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        return JSONResponse(status_code=400, content={
            "accepted": False, "stage": "file_type",
            "reason": f"Unsupported type '{photo.content_type}'. Upload JPEG, PNG, or WebP.",
        })

    file_bytes = await photo.read()

    if len(file_bytes) > 15 * 1024 * 1024:
        return JSONResponse(status_code=400, content={
            "accepted": False, "stage": "file_size",
            "reason": "File too large (max 15 MB). Please compress and retry.",
        })

    # Layer 1
    ok, reason = _basic_image_checks(file_bytes)
    if not ok:
        return JSONResponse(content={"accepted": False, "stage": "structural", "reason": reason})

    # Layer 2
    ok, reason = _validate_gps(latitude, longitude)
    if not ok:
        return JSONResponse(content={"accepted": False, "stage": "gps", "reason": reason})

    # Layer 3
    scheme_name = SCHEME_ASSETS.get(scheme_id, {}).get("name", scheme_id)
    ai_valid, ai_decision, ai_reason = _classify_with_groq(file_bytes, scheme_name, ward)
    if not ai_valid:
        return JSONResponse(content={
            "accepted": False, "stage": "ai_vision",
            "decision": ai_decision,
            "reason": f"Image rejected: {ai_reason}. Please upload a photo showing infrastructure or damage at the location.",
        })

    # All passed → flag in Neo4j
    report_id = f"EVD_CITIZEN_{uuid.uuid4().hex[:10].upper()}"
    flagged = _flag_dispute_in_neo4j(
        report_id=report_id, asset_id=asset_id, event_id=event_id,
        scheme_id=scheme_id, ward=ward, lat=latitude, lon=longitude,
        description=description, ai_decision=ai_decision,
    )

    return JSONResponse(content={
        "accepted":         True,
        "report_id":        report_id,
        "ai_decision":      ai_decision,
        "ai_reason":        ai_reason,
        "flagged_in_neo4j": flagged,
        "status":           "needs_review",
        "message":          f"Report {report_id} submitted. Asset flagged for audit. Thank you.",
    })
