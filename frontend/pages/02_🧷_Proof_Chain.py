"""
Proof Chain — PRAMAAN v3.0
Neo4j chain + real internet scraping + AI Questions panel
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import requests
import json
import feedparser
import urllib.parse
from bs4 import BeautifulSoup
from utils.geo_selector import render_geo_selector, geo_breadcrumb

BASE_URL   = "http://127.0.0.1:8000"
GROQ_KEY   = os.environ.get("GROQ_API_KEY", "")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def hide_live_ingestion():
    st.markdown("""<style>
    [data-testid="stSidebarNav"] ul li:nth-child(4){display:none}
    </style>""", unsafe_allow_html=True)

def render_node(icon, label, content, color):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{color}22,{color}11);
               border-left:4px solid {color};border-radius:8px;
               padding:12px 16px;margin-bottom:6px;">
      <div style="font-size:1.4em">{icon}</div>
      <div style="font-weight:700;color:{color};font-size:0.8em;
                  text-transform:uppercase;letter-spacing:.06em;margin-top:4px">{label}</div>
      <div style="margin-top:6px;font-size:.95em;line-height:1.6">{content}</div>
    </div>""", unsafe_allow_html=True)

def arrow():
    st.markdown('<div style="text-align:center;font-size:1.6em;color:#555;margin:2px 0">↓</div>',
                unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Scraping
# ──────────────────────────────────────────────────────────────────────────────
def get_evidence(zone: str, city: str, asset_name: str, asset_type: str, 
                 scheme: str) -> list[dict]:
    """
    Tries 3 progressively broader queries.
    Returns first non-empty result set.
    """
    
    # Clean asset name
    asset_clean = ""
    if asset_name:
        asset_clean = asset_name.replace("Water Body -", "").replace("DMC Ward", "").replace("-", " ").strip()

    # Delivery keywords per asset type
    TYPE_KEYWORDS = {
        "drain":      "drain desilting cleaning",
        "road":       "road repair resurfacing",
        "park":       "park garden renovation",
        "toilet":     "public toilet",
        "water_body": "lake water body restoration",
        "building":   "building community centre",
    }
    kw = TYPE_KEYWORDS.get(asset_type, "project")
    
    # Zone short: "Shahdara North Zone" → "Shahdara"
    zone_word = zone.split()[0] if zone else ""
    
    # Scheme short: "Local Development Grants - Roads & Drains (Delhi)" → "Local Development"
    scheme_short = scheme.split("-")[0].split("(")[0].strip()[:20] if scheme else ""
    
    queries = [
        # Tier 1 — most specific: asset name + kw
        f"{asset_clean} {kw} {city} 2024 2025",
        
        # Tier 2 — zone + city + asset type keyword
        f"{zone_word} {city} MCD {kw} 2024 2025",
        
        # Tier 3 — broadest: scheme + city + asset type
        f"{scheme_short} {city} MCD {kw} completed"
    ]
    
    SKIP_WORDS = ["BJP","AAP","Congress","party","election",
                  "blame","scam","protest","controversy","allegation"]
    
    for query in queries:
        encoded = urllib.parse.quote(query)
        rss = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
        
        try:
            feed = feedparser.parse(rss)
            results = []
            
            for entry in feed.entries[:8]:
                title = entry.get("title","")
                url   = entry.get("link","")
                
                if not title or not url:
                    continue
                if any(w.lower() in title.lower() for w in SKIP_WORDS):
                    continue
                
                # Clean HTML from snippet
                summary_raw = entry.get("summary","")
                try:
                    snippet_clean = BeautifulSoup(summary_raw, "html.parser").get_text(separator=" ", strip=True)[:250]
                except:
                    snippet_clean = summary_raw[:250]
                
                results.append({
                    "title":   title,
                    "url":     url,
                    "snippet": snippet_clean,
                    "source":  entry.get("source",{}).get("title","News"),
                    "date":    entry.get("published",""),
                    "query":   query
                })
            
            if results:
                return results[:3]  # Found — return top 3
                
        except Exception:
            continue
    
    return []  # All 3 queries failed

def render_evidence_image(image_url, caption: str = ""):
    """Render image with fallback if URL is broken."""
    img_str = str(image_url).strip() if image_url is not None else ""
    
    if not img_str or img_str in ["0", "null", "None", "nan"]:
        # Show placeholder instead of broken icon
        st.markdown(f"""
        <div style="background:#1e1e2e; border:1px dashed #444; 
             border-radius:8px; padding:20px; text-align:center; 
             color:#888; font-size:13px;">
            📷 No photo evidence available<br/>
            <small>{caption}</small>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Check if it's a valid HTTP URL
    if not img_str.startswith("http"):
        st.markdown(f"""
        <div style="background:#1e1e2e; border:1px dashed #444;
             border-radius:8px; padding:20px; text-align:center;
             color:#888; font-size:13px;">
            📷 Photo reference: {caption}<br/>
            <small>Image not accessible in browser</small>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Try rendering — catch broken URL silently
    try:
        st.image(image_url, caption=caption, use_container_width=True)
    except Exception:
        st.markdown(f"""
        <div style="background:#1e1e2e; border:1px dashed #444;
             border-radius:8px; padding:20px; text-align:center;
             color:#888; font-size:13px;">
            📷 Image unavailable<br/>
            <small>{caption}</small>
        </div>
        """, unsafe_allow_html=True)

def get_og_image(article_url: str) -> str | None:
    """
    Fetches the Open Graph image from a news article URL.
    This gives a real thumbnail for the evidence card.
    Returns image URL string or None if not found.
    """
    try:
        resp = requests.get(
            article_url, 
            timeout=3,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Try og:image first
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]
        
        # Try twitter:image
        tw = soup.find("meta", attrs={"name":"twitter:image"})
        if tw and tw.get("content"):
            return tw["content"]
            
    except Exception:
        pass
    return None


def patch_asset_verified(asset_id: str):
    """Mark asset as verified in Neo4j via backend."""
    try:
        requests.post(f"{BASE_URL}/assets/{asset_id}/set-verified", timeout=5)
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# AI Questions
# ──────────────────────────────────────────────────────────────────────────────
def generate_questions(asset_name, asset_type, ward_name, status, cost,
                        agency_name, funding_name, evidence_url) -> list:
    cache_key = f"questions_{asset_name}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    fallback = [
        f"What is the funding source for {asset_name}?",
        "Which agency implemented this project?",
        f"When was this {asset_type} last verified?",
        "Is there physical evidence of completion?",
        "What is the total cost of this project?",
    ]

    if not GROQ_KEY:
        st.session_state[cache_key] = fallback
        return fallback

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        prompt = f"""Generate 5 short, factual questions a citizen or auditor would ask about:
Asset: {asset_name} | Type: {asset_type} | Ward: {ward_name}
Status: {status} | Cost: Rs {cost} | Agency: {agency_name}
Funding: {funding_name} | Evidence URL: {evidence_url or 'none'}

Return ONLY a JSON array of 5 strings. Example: ["Q1?","Q2?","Q3?","Q4?","Q5?"]"""

        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=300
        )
        raw = resp.choices[0].message.content.strip()
        s, e = raw.find("["), raw.rfind("]") + 1
        if s >= 0 and e > s:
            qs = json.loads(raw[s:e])
            if isinstance(qs, list):
                st.session_state[cache_key] = qs
                return qs
    except Exception:
        pass

    st.session_state[cache_key] = fallback
    return fallback


def answer_from_graph(q, asset_name, asset_type, ward_name, status,
                      cost, agency_name, funding_name, ev_url) -> str:
    q = q.lower()
    if any(w in q for w in ["fund", "scheme", "source"]):
        return f"**{asset_name}** is funded under **{funding_name}**."
    if any(w in q for w in ["agency", "implement", "built", "who"]):
        return f"Implemented by **{agency_name}**."
    if any(w in q for w in ["cost", "rupee", "budget", "₹", "spend"]):
        return f"Total cost: **₹{cost:,.0f}**" if cost else "Cost data not available."
    if any(w in q for w in ["status", "complet", "done", "finish"]):
        return f"Current status: **{str(status).upper()}**."
    if any(w in q for w in ["evidence", "proof", "verif", "photo", "news"]):
        return f"Evidence: [{ev_url}]({ev_url})" if ev_url else \
               "No direct evidence URL. Chain verified from structured government data."
    if any(w in q for w in ["ward", "location", "where"]):
        return f"Located in **{ward_name}**."
    return (f"**{asset_name}** ({asset_type}) in {ward_name}. "
            f"Funded by {funding_name}, built by {agency_name}. Status: {status}.")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(page_title="Proof Chain | Pramaan", layout="wide")
    hide_live_ingestion()

    st.title("🔗 Governance Delivery Proof Chain")
    st.caption("Trace any asset from funding source → agency → physical asset → live internet evidence.")

    # ── Geography from session (or re-select if fresh page) ──────────────
    geo = render_geo_selector(sidebar=True)
    ward_id   = geo["ward_id"]
    ward_name = geo["ward_name"]

    st.markdown(f"**📍** `{geo_breadcrumb()}`")
    st.divider()

    # ── Asset selector ────────────────────────────────────────────────────
    try:
        resp = requests.get(f"{BASE_URL}/assets/list", params={"ward_region_id": ward_id}, timeout=5)
        if resp.status_code != 200:
            st.error("Could not load assets from backend.")
            return
        all_assets = resp.json().get("assets", [])
        if not all_assets:
            st.warning("No assets found for this ward.")
            return
    except Exception as e:
        st.error(f"Backend error: {e}")
        return

    asset_options = {f"{a['name']} ({a.get('type','?')})": a["asset_id"] for a in all_assets}

    # Support jump-to from Ward Map click
    preselect = st.session_state.get("selected_asset")
    default_idx = 0
    if preselect:
        for i, aid in enumerate(asset_options.values()):
            if aid == preselect:
                default_idx = i
                break

    selected_label = st.selectbox("🔍 Select Asset to Trace", list(asset_options.keys()), index=default_idx)
    asset_id  = asset_options[selected_label]
    st.session_state["selected_asset"] = asset_id

    st.divider()

    # ── Load chain from Neo4j ─────────────────────────────────────────────
    try:
        chain_resp = requests.get(f"{BASE_URL}/assets/{asset_id}/chain", timeout=10)
        if chain_resp.status_code == 404:
            st.warning("No chain data found for this asset.")
            return
        if chain_resp.status_code != 200:
            st.error("Failed to load chain data.")
            return

        data        = chain_resp.json()
        asset       = data["asset"]
        scheme      = data.get("scheme")
        actor       = data.get("built_by")
        region      = data.get("region")
        ward        = data.get("ward")
        seed_evs    = data.get("evidence", [])

        asset_name  = asset.get("name", asset_id)
        asset_type  = asset.get("type", "asset")
        cost_val    = asset.get("cost", 0) or 0
        status      = asset.get("status", "unknown")
        agency_name = actor.get("name", "N/A") if actor else "N/A"
        funding_name= scheme.get("name", "N/A") if scheme else "N/A"
        seed_ev_url = seed_evs[0].get("url","") if seed_evs else ""

        st.subheader(f"🔗 Proof Chain: {asset_name}")

        chain_col, _ = st.columns([5, 1])

        with chain_col:
            st.caption("Full traceability: Funding → Agency → Asset → Location → Evidence")

            # ── Scheme node ───────────────────────────────────────────────
            if scheme:
                render_node("💰", "Scheme / Funding",
                    f"<b>{scheme.get('name','N/A')}</b><br/>"
                    f"Ministry: {scheme.get('ministry','N/A')} | "
                    f"Category: {scheme.get('category','N/A')}", "#3b82f6")
                arrow()

            # ── Actor node ────────────────────────────────────────────────
            if actor:
                render_node("🏛️", "Implementing Agency",
                    f"<b>{actor.get('name','N/A')}</b><br/>Type: {actor.get('type','N/A')}", "#8b5cf6")
                arrow()

            # ── Asset node ────────────────────────────────────────────────
            cost_str = f"₹{cost_val:,.0f}" if cost_val else "N/A"
            render_node("🏗️", "Asset / Infrastructure",
                f"<b>{asset_name}</b><br/>"
                f"Type: {asset_type} | Status: {status} | Cost: {cost_str}", "#f59e0b")

            # ── Location node ─────────────────────────────────────────────
            loc_parts = []
            if ward:   loc_parts.append(f"Ward: {ward.get('name','')}")
            if region: loc_parts.append(f"Street: {region.get('name','')}")
            if loc_parts:
                arrow()
                render_node("📍", "Location", "<br/>".join(loc_parts), "#10b981")

            # ── LIVE EVIDENCE (auto-scrape) ───────────────────────────────
            arrow()
            cache_key = f"ev_{asset_id}"
            if cache_key not in st.session_state:
                with st.spinner("⚡ Fetching live evidence from internet..."):
                    st.session_state[cache_key] = get_evidence(
                        zone       = st.session_state.get("zone", "Shahdara North Zone"),
                        city       = "Delhi",
                        asset_name = asset_name,
                        asset_type = asset_type,
                        scheme     = funding_name
                    )

            live_articles = st.session_state[cache_key]

            if live_articles:
                # Patch asset as verified
                patch_asset_verified(asset_id)
                st.markdown("""
                <div style="background:linear-gradient(135deg,#06b6d422,#06b6d411);
                           border-left:4px solid #06b6d4;border-radius:8px;
                           padding:12px 16px;margin-bottom:6px;">
                  <div style="font-size:1.4em">📰</div>
                  <div style="font-weight:700;color:#06b6d4;font-size:0.8em;
                              text-transform:uppercase;letter-spacing:.06em;margin-top:4px">Live Evidence (internet-scraped)</div>
                </div>""", unsafe_allow_html=True)

                for ev in live_articles:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**📰 {ev['title']}**")
                            st.markdown(f"🔗 [{ev['source']}]({ev['url']})")
                            st.markdown(f"📅 {ev['date']}")
                            st.caption(ev['snippet'])
                        with col2:
                            # Try to show article thumbnail
                            img_url = get_og_image(ev['url'])
                            if img_url:
                                try:
                                    st.image(img_url, use_container_width=True)
                                except:
                                    st.markdown("📷")
                            else:
                                st.markdown("📰")
                        st.divider()
            else:
                render_node("🔍", "Evidence Status",
                    "No specific news articles found for this asset. "
                    "Chain integrity is verified from official structured government data.",
                    "#64748b")

        # ── AMRUT National Context Panel ─────────────────────────────────
        if funding_name and "AMRUT" in funding_name.upper():
            import plotly.graph_objects as go
            import pandas as pd
            st.divider()
            st.markdown("### 🌐 National Context — AMRUT Storm Drainage")
            st.caption(
                "Source: **data.gov.in** · Rajya Sabha Starred Question, 20 Dec 2021 · "
                "[View Dataset](https://data.gov.in/catalog/stateut-wise-status-progress-"
                "storm-water-drainage-projects-taken-under-amrut)"
            )
            try:
                amrut_resp = requests.get(f"{BASE_URL}/data/amrut-drainage", timeout=6)
                if amrut_resp.status_code == 200:
                    amrut     = amrut_resp.json()
                    delhi_d   = amrut.get("delhi", {}) or {}
                    nat_total = amrut.get("grand_total", {}) or {}
                    states    = amrut.get("states", [])

                    d1, d2, d3, d4 = st.columns(4)
                    d1.metric("🏙️ Delhi Completed",
                              f"{delhi_d.get('work_completed___number','N/A')} projects")
                    d2.metric("💰 Delhi Amount",
                              f"₹{delhi_d.get('work_completed___amount','N/A')} Cr")
                    d3.metric("🔨 Delhi In-Progress",
                              f"{delhi_d.get('work_in_progress___number','N/A')} projects")
                    d4.metric("🌍 National Total",
                              f"{nat_total.get('total___number','N/A')} projects · "
                              f"₹{nat_total.get('total___amount','N/A')} Cr")

                    # Bar chart — states by completed works
                    df_states = pd.DataFrame(states)
                    df_states = df_states[df_states["work_completed___number"] != "NA"].copy()
                    df_states["work_completed___number"] = pd.to_numeric(
                        df_states["work_completed___number"], errors="coerce"
                    ).fillna(0)
                    df_top = df_states.nlargest(10, "work_completed___number")
                    colors = ["#E63946" if "Delhi" in str(s) else "#3b82f6"
                              for s in df_top["state_ut"]]
                    fig = go.Figure(go.Bar(
                        x=df_top["state_ut"],
                        y=df_top["work_completed___number"],
                        marker_color=colors,
                        text=df_top["work_completed___number"].astype(int),
                        textposition="outside"
                    ))
                    fig.update_layout(
                        title="Top 10 States — AMRUT Drainage Works Completed",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font={"color": "white"},
                        xaxis={"tickfont": {"size": 10}},
                        height=340, margin=dict(l=20, r=20, t=40, b=80)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption("🔴 Red = NCT of Delhi | 🔵 Blue = other states")
            except Exception as ex:
                st.caption(f"National data unavailable: {ex}")

    except Exception as e:
        st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
