"""
PRAMAAN — Step 1c: Fetch / Extract Unstructured Data
Reads all files from data/resources/unstructured/ (PDFs, CSVs, docs),
extracts text, calls AI service to extract governance entities,
and saves raw extraction JSON to data/resources/unstructured/extracted/.

Run before: transform_to_7_table_schema.py
"""

import sys
import json
import re
import time
from pathlib import Path

_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[1]

UNSTRUCTURED_DIR = _PROJECT_ROOT / "data" / "resources" / "unstructured"
EXTRACTED_DIR    = UNSTRUCTURED_DIR / "extracted"
EXTRACTED_DIR.mkdir(exist_ok=True)

# ── PDF reader ────────────────────────────────────────────────────────────────
try:
    from pypdf import PdfReader
except ImportError:
    print("❌ pypdf not installed — run: pip install pypdf")
    sys.exit(1)

# ── AI service ────────────────────────────────────────────────────────────────
# fetch_unstructured.py runs standalone (not inside FastAPI), so call Groq directly.
try:
    from groq import Groq
    from dotenv import load_dotenv
    import os
    load_dotenv(_PROJECT_ROOT / ".env")
    _groq_key = os.getenv("GROQ_API_KEY", "")
    if not _groq_key:
        print("❌ GROQ_API_KEY not set in .env")
        sys.exit(1)
    _client = Groq(api_key=_groq_key)
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)

# ── Chunk size — Groq context limit is ~6k tokens safe for extraction ─────────
CHUNK_CHARS = 3000
DELAY_SECS  = 2   # avoid rate-limiting between chunks


print("=" * 60)
print("  PRAMAAN — Unstructured Data Extraction (Step 1c)")
print("=" * 60)


# ── Text extractors ───────────────────────────────────────────────────────────

def extract_text_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages  = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
    return "\n\n".join(pages)


def extract_text_csv(path: Path) -> str:
    """Read CSV as plain text — AI will parse the structure."""
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_text_md(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_pdf(path)
    elif suffix in (".csv", ".md", ".txt"):
        return extract_text_csv(path)
    return ""


# ── AI extraction ─────────────────────────────────────────────────────────────

def _call_ai(chunk: str, source_label: str) -> dict:
    prompt = f"""You are a governance data extraction assistant for India (Delhi focus).
Extract governance entities from the text below. Return ONLY valid JSON — no markdown, no explanation.

Text:
{chunk}

Return this exact structure:
{{
  "entities": [
    {{"id": "unique_id", "label": "Scheme|Region|Asset|Actor|Beneficiary|Event", "properties": {{
        "name": "...", "type": "...", "confidence": 0.8,
        "ministry": "...",  "category": "...",
        "status": "completed|in_progress|planned",
        "cost": 1200000
    }}}}
  ],
  "relations": [
    {{"from_id": "id1", "to_id": "id2", "type": "FUNDS|BUILT_BY|LOCATED_IN|BENEFITS|PROVES|REPRESENTS",
      "from_label": "Scheme", "to_label": "Asset"}}
  ]
}}

Rules:
- Only include entities clearly mentioned in the text
- confidence: 0.9 if explicitly stated, 0.7 if inferred
- Skip entities with no name
- Asset type must be one of: drain|road|toilet|housing|park|streetlight|water_body|other
- Region type must be one of: state|city|zone|ward|street
- Actor type must be one of: government|contractor|elected_rep
- Prefix IDs with source: {source_label}_
"""
    try:
        resp = _client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4096,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"    ⚠️  JSON parse error: {e}")
        return {"entities": [], "relations": []}
    except Exception as e:
        print(f"    ⚠️  AI call error: {e}")
        return {"entities": [], "relations": []}


def extract_from_text(full_text: str, source_label: str) -> dict:
    """Split text into chunks, call AI on each, merge results."""
    chunks = [full_text[i:i+CHUNK_CHARS] for i in range(0, len(full_text), CHUNK_CHARS)]
    all_entities, all_relations = [], []
    seen_ids = set()

    print(f"    Splitting into {len(chunks)} chunk(s) of ~{CHUNK_CHARS} chars")

    for i, chunk in enumerate(chunks, 1):
        if not chunk.strip():
            continue
        print(f"    Chunk {i}/{len(chunks)} ...", end=" ", flush=True)
        result = _call_ai(chunk, source_label)

        for ent in result.get("entities", []):
            eid = ent.get("id", "")
            if eid and eid not in seen_ids:
                seen_ids.add(eid)
                all_entities.append(ent)

        all_relations.extend(result.get("relations", []))
        print(f"{len(result.get('entities', []))} entities, {len(result.get('relations', []))} relations")

        if i < len(chunks):
            time.sleep(DELAY_SECS)

    return {"entities": all_entities, "relations": all_relations}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Collect all files from pdfs/ and docs/
    files = []
    for subdir in ["pdfs", "docs"]:
        d = UNSTRUCTURED_DIR / subdir
        if d.exists():
            files.extend(f for f in d.iterdir()
                         if f.is_file() and f.suffix.lower() in (".pdf", ".csv", ".md", ".txt"))

    if not files:
        print("⚠️  No files found in unstructured/pdfs/ or unstructured/docs/")
        sys.exit(0)

    print(f"\nFound {len(files)} unstructured file(s) to process\n")

    total_entities = total_relations = 0
    processed = skipped = 0

    for path in sorted(files):
        out_path = EXTRACTED_DIR / (path.stem + ".json")

        # Skip if already extracted (re-run safe)
        if out_path.exists():
            existing = json.loads(out_path.read_text())
            n_ent = len(existing.get("entities", []))
            n_rel = len(existing.get("relations", []))
            print(f"  ⏭  {path.name} — already extracted ({n_ent} entities, {n_rel} relations) — skipping")
            total_entities += n_ent
            total_relations += n_rel
            skipped += 1
            continue

        print(f"\n  📄 {path.name}")
        try:
            text = extract_text(path)
        except Exception as e:
            print(f"    ❌ Text extraction failed: {e}")
            continue

        if not text.strip():
            print("    ⚠️  No extractable text (possibly scanned/image PDF) — skipping")
            continue

        print(f"    Extracted {len(text):,} chars of text")

        source_label = re.sub(r"[^a-z0-9]", "_", path.stem.lower())[:20]
        result = extract_from_text(text, source_label)

        # Stamp metadata
        result["source_file"]  = path.name
        result["source_type"]  = "unstructured_llm"
        result["source_subdir"] = path.parent.name

        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        n_ent = len(result["entities"])
        n_rel = len(result["relations"])
        total_entities += n_ent
        total_relations += n_rel
        processed += 1
        print(f"    ✅ Saved → {out_path.name}  ({n_ent} entities, {n_rel} relations)")

    print(f"""
{'=' * 60}
  Extraction complete
  Processed : {processed} file(s)
  Skipped   : {skipped} (already extracted)
  Total     : {total_entities} entities, {total_relations} relations
  Output    : {EXTRACTED_DIR}
{'=' * 60}
✅ Next: run transform_to_7_table_schema.py
""")


if __name__ == "__main__":
    main()
