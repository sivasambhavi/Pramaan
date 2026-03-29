"""
Quick Gemini API health check — run with:
  python test_gemini.py
"""
import os, sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
if not key:
    print("❌  No GEMINI_API_KEY / GOOGLE_API_KEY found in .env")
    sys.exit(1)

print(f"🔑  Key loaded: {key[:12]}…")

# ── Test 1: SDK init ───────────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("✅  SDK initialised (gemini-1.5-flash)")
except Exception as e:
    print(f"❌  SDK init failed: {e}")
    sys.exit(1)

# ── Test 2: Live call ─────────────────────────────────────────────────────────
try:
    resp = model.generate_content("Reply with exactly: PRAMAAN OK")
    text = resp.text.strip()
    print(f"✅  API call succeeded → '{text}'")
except Exception as e:
    err = str(e)
    if "API_KEY_INVALID" in err or "invalid" in err.lower():
        print(f"❌  API key is INVALID or revoked: {e}")
    elif "429" in err or "quota" in err.lower():
        print(f"⚠️   API key valid but QUOTA EXCEEDED (rate limited): {e}")
    elif "403" in err:
        print(f"❌  API key FORBIDDEN (key may lack Gemini API permission): {e}")
    else:
        print(f"❌  API call failed: {e}")
    sys.exit(1)

# ── Test 3: JSON mode ─────────────────────────────────────────────────────────
try:
    resp2 = model.generate_content(
        'Return JSON: {"status": "ok"}',
        generation_config=genai.GenerationConfig(
            temperature=0.0,
            response_mime_type="application/json",
        ),
    )
    print(f"✅  JSON mode works → {resp2.text.strip()[:60]}")
except Exception as e:
    print(f"⚠️   JSON mode failed (non-critical): {e}")

print("\n✅  Gemini API is HEALTHY — all checks passed.")
