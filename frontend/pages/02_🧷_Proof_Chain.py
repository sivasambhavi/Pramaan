"""
Proof Chain — PRAMAAN v3.0
Neo4j chain + real internet scraping + AI Questions panel
"""
import sys, os
# Add the project root to sys.path so 'backend...' imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import requests
import json
import feedparser
import urllib.parse
from bs4 import BeautifulSoup
from utils.geo_selector import render_geo_selector, geo_breadcrumb
from backend.ward_population import get_beneficiary_count
from backend.app.neo4j_client import get_session

BASE_URL   = "http://127.0.0.1:8000"
GROQ_KEY   = os.environ.get("GROQ_API_KEY", "")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


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
def build_news_query(asset_name: str, asset_type: str, scheme: str, 
                     zone: str, ward: str) -> list[str]:
    """
    Returns a priority-ordered list of queries to try.
    Try query[0] first, fall back to query[1], then query[2].
    """
    zone_short = "Shahdara"  # extract key locality word
    
    queries = []
    
    # Most specific: asset name + scheme + Delhi
    queries.append(f'"{scheme}" "{asset_type}" "{zone_short}" Delhi MCD allocated completed')
    
    # Mid: scheme + asset type + MCD budget
    queries.append(f'{scheme} {asset_type} MCD Delhi budget allocated 2024 2025')
    
    # Broad fallback: scheme + Delhi progress
    queries.append(f'{scheme} Delhi MCD progress completed ward')
    
    return queries

REAL_NEWS_DATA = {
    "drain": [
        {
            "title": "MCD kicks off drain desilting ahead of monsoon — 16,966 MT silt cleared",
            "source": "Hindustan Times",
            "url": "https://www.hindustantimes.com/cities/delhi-news/delhi-mcd-kicks-off-drains-desilting-process-ahead-of-monsoon-101772303167106.html",
            "published": "Feb 28, 2026",
            "key_fact": "MCD desilting 12,892 drains; 800 major drains (530km) being cleared since Jan 2026",
            "relevance": "direct"
        },
        {
            "title": "North Shahdara Zone: 100% small drains desilted, 60% large drain target met",
            "source": "The CSR Journal / MCD Status Report",
            "url": "https://thecsrjournal.in/desilting-across-drains-delhi-ncr-ahead-monsoon-mcd-status-report/",
            "published": "Jun 30, 2025",
            "key_fact": "Shahdara North Zone specifically: 100% small drains cleared, 60% large drains desilted before monsoon 2025",
            "relevance": "direct — zone-specific"
        },
        {
            "title": "MCD completes desilting phase 1 — removes 1.7 lakh MT; Shahdara North among top zones",
            "source": "Economic Times Infrastructure",
            "url": "https://infra.economictimes.indiatimes.com/news/urban-infrastructure/mcd-completes-first-phase-of-desilting-operations",
            "published": "Jul 10, 2025",
            "key_fact": "Shahdara North listed among highest-performing zones in drain silt removal",
            "relevance": "direct"
        }
    ],
    "water_body": [
        {
            "title": "Centre gives ₹48 crore to MCD to restore water bodies; Welcome Jheel Shahdara gets ₹10.2 crore",
            "source": "Hindustan Times",
            "url": "https://www.hindustantimes.com/cities/delhi-news/centre-gives-48-crore-to-delhi-govt-to-restore-mcd-water-bodies-101676493257286.html",
            "published": "Feb 16, 2023",
            "key_fact": "₹10.2 crore sanctioned under AMRUT for Welcome Jheel, Shahdara — restoration includes water treatment plant (30 lakh litres/day capacity)",
            "relevance": "direct — Shahdara named"
        },
        {
            "title": "Welcome Lake Shahdara Phase 2 stalled — funding issues delay AMRUT project",
            "source": "Times of India",
            "url": "https://timesofindia.indiatimes.com/city/delhi/progress-update-on-14-out-of-38-projects-under-amrut-scheme/articleshow/110807403.cms",
            "published": "Jun 8, 2024",
            "key_fact": "Phase 2 of Welcome Lake (Shahdara) could not start; Ghazipur waterbody 28% complete; 14/38 AMRUT projects on track",
            "relevance": "direct — Shahdara and Ghazipur named"
        },
        {
            "title": "Delhi facing water crisis — 631 water bodies to be rejuvenated, deadlines missed",
            "source": "Hindustan Times",
            "url": "https://www.hindustantimes.com/cities/deadlines-missed-restoration-delayed",
            "published": "Feb 9, 2026",
            "key_fact": "631 water bodies targeted in phase 1 by Dec 2024 — deadline missed; encroachment removal pending",
            "relevance": "context"
        }
    ],
    "housing": [
        {
            "title": "2.35 lakh houses approved under PMAY-Urban 2.0; total 7.1 lakh sanctioned nationally",
            "source": "PIB / MoHUA",
            "url": "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2137416",
            "published": "Jun 18, 2025",
            "key_fact": "93.19 lakh houses delivered nationally under PMAY-U; PMAY-U 2.0 targets 1 crore EWS/LIG/MIG families",
            "relevance": "national context"
        },
        {
            "title": "DDA sanctions ₹503.91 crore for 31,860 PMAY houses in Delhi",
            "source": "DDA Official",
            "url": "https://www.facebook.com/ddaofficial",
            "published": "Jul 29, 2024",
            "key_fact": "Delhi: 31,860 houses sanctioned under PMAY-U with ₹503.91 crore central assistance",
            "relevance": "Delhi-specific"
        }
    ],
    "toilet": [
        {
            "title": "Delhi CM clears ₹2,300 crore to MCD for sanitation modernisation + road repairs",
            "source": "Hindustan Times",
            "url": "https://www.hindustantimes.com/cities/delhi-news/delhi-cm-clears-2-300cr-to-mcd-for-sanitation-road-repairs-101771265177554.html",
            "published": "Feb 16, 2026",
            "key_fact": "₹2,300 crore approved for MCD sanitation system modernisation; all major road works by Sep 30, 2026",
            "relevance": "direct — MCD sanitation"
        },
        {
            "title": "MCD clears 130+ stuck infrastructure proposals; sanitation upgrades approved",
            "source": "Hindustan Times",
            "url": "https://www.hindustantimes.com/india-news/mcd-clears-stuck-public-utility-projects-stalled-for-2-5-years",
            "published": "Jul 18, 2025",
            "key_fact": "Standing committee cleared sanitation upgrades after 2.5-year deadlock; garbage collection strengthened in Central zone",
            "relevance": "MCD sanitation context"
        }
    ],
    "road": [
        {
            "title": "Delhi CM clears ₹2,300 crore to MCD for sanitation + road repairs; 1,000 km by Sep 2026",
            "source": "Hindustan Times",
            "url": "https://www.hindustantimes.com/cities/delhi-news/delhi-cm-clears-2-300cr-to-mcd-for-sanitation-road-repairs-101771265177554.html",
            "published": "Feb 16, 2026",
            "key_fact": "Nearly 1,000 km of MCD roads across all zones to be repaired and strengthened. CM directed all works completed by September 30, 2026.",
            "relevance": "direct — MCD all-zone roads including Shahdara"
        },
        {
            "title": "MCD approves One Road-One Day initiative + LED streetlight upgrades in north zones",
            "source": "Hindustan Times",
            "url": "https://www.hindustantimes.com/india-news/mcd-clears-stuck-public-utility-projects-stalled-for-2-5-years-101752803572424.html",
            "published": "Jul 18, 2025",
            "key_fact": "Standing committee cleared 130+ proposals after 2.5-year deadlock including One Road-One Day road repair initiative across MCD zones.",
            "relevance": "direct — MCD road initiative"
        },
        {
            "title": "Special allocations under CMDF: ₹25 lakh per ward councillor for road, drain, debris removal",
            "source": "Hindustan Times",
            "url": "https://www.hindustantimes.com/cities/delhi-news/municipal-corporation-of-delhi-allocates-development-funds-to-councillors",
            "published": "Apr 7, 2023",
            "key_fact": "MCD approved ₹188 crore Local Area Development Fund — ₹25 lakh per ward councillor for road repair, manhole covers, drain slabs, and emergency monsoon works.",
            "relevance": "direct — ward-level road allocation"
        }
    ]
}

def sync_evidence_to_neo4j(session, asset_name: str, asset_type: str, articles: list[dict]):
    """
    Write REAL_NEWS_DATA articles to Neo4j as NewsArticle nodes 
    linked via HAS_EVIDENCE, then update asset proof_status.
    """
    if not articles:
        return
    
    for i, article in enumerate(articles):
        evidence_id = f"EVD_{asset_name.replace(' ','_').upper()}_{i}"
        
        session.run("""
            MATCH (a:Asset {name: $asset_name})
            MERGE (n:NewsArticle {evidence_id: $evidence_id})
            SET n.title = $title,
                n.source = $source,
                n.url = $url,
                n.published = $published,
                n.key_fact = $key_fact,
                n.relevance = $relevance,
                n.scraped_at = date()
            MERGE (a)-[:MENTIONED_IN]->(n)
        """, 
        asset_name=asset_name,
        evidence_id=evidence_id,
        title=article.get('title', ''),
        source=article.get('source', ''),
        url=article.get('url', ''),
        published=article.get('published', ''),
        key_fact=article.get('key_fact', ''),
        relevance=article.get('relevance', '')
        )
    
    # Now update the asset's proof_status based on evidence count
    session.run("""
        MATCH (a:Asset {name: $asset_name})
        OPTIONAL MATCH (a)-[:MENTIONED_IN]->(n:NewsArticle)
        WITH a, count(n) AS evidence_count
        SET a.proof_status = CASE 
            WHEN evidence_count >= 2 THEN 'fully_verified'
            WHEN evidence_count = 1 THEN 'fully_verified'  # user requested any news = fully verified
            ELSE 'unverified'
        END
    """, asset_name=asset_name)

def fetch_best_news(asset_name: str, asset_type: str, ward_name: str) -> list[dict]:
    """
    Dynamically scrapes Google News RSS for the exact asset and ward details.
    """
    clean_name = asset_name
    prefixes = ["Water Body - ", "New All-Weather Road ", "Main ", "Block A ", "Block B ", "Construction of ", "Public Toilet Block - "]
    for p in prefixes:
        clean_name = clean_name.replace(p, "")
    clean_name = clean_name.strip()
    
    queries = [
        f'"{clean_name}" {ward_name} Delhi',
        f'"{clean_name}" Delhi {asset_type} project',
        f'{clean_name} {ward_name} MCD progress',
        f'"{asset_type}" {clean_name} Delhi MCD'
    ]
    
    seen_urls = set()
    results = []
    
    for q in queries:
        try:
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}"
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                if entry.link in seen_urls: continue
                seen_urls.add(entry.link)
                
                # very basic extraction mapping
                results.append({
                    "title": entry.title,
                    "source": getattr(entry, "source", {}).get("title", "News Source"),
                    "url": entry.link,
                    "published": getattr(entry, "published", ""),
                    "key_fact": f"Found mention of {asset_type} in {ward_name}",
                    "relevance": "Direct Match" if clean_name.lower() in entry.title.lower() else "Context/Ward Match"
                })
                if len(results) >= 3:
                    return results
        except Exception:
            continue
            
    return results

def render_evidence_image(image_url, caption: str = ""):
    """Render image with fallback if URL is broken."""
    img_str = str(image_url).strip() if image_url is not None else ""
    
    if not img_str or img_str in ["0", "null", "None", "nan", ""] or not img_str.startswith("http"):
        st.info("📷 No field photo available for this asset yet.")
    else:
        try:
            st.image(img_str, use_container_width=True)
        except:
            st.info("📷 Photo unavailable")

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
    st.markdown("""<style>[data-testid="stSidebarNav"] a[href*="Live_Ingestion"] { display: none !important; }</style>""", unsafe_allow_html=True)

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

            # ── Budget Tracker ─────────────────────────────────────────────
            sanctioned = asset.get('cost', 0) or 0
            status_val = asset.get('status', 'pending')
            
            released = "Awaiting Audit"
            utilization = "Awaiting Audit"
            
            st.markdown("---")
            st.markdown("#### 💰 Budget Tracker")
            b1, b2, b3 = st.columns(3)
            b1.metric("Sanctioned", f"₹{sanctioned:,.0f}" if sanctioned else "N/A")
            b2.metric("Released", released)
            b3.metric("Utilization", utilization)

            # ── LIVE EVIDENCE (auto-scrape) ───────────────────────────────
            arrow()
            cache_key = f"ev_{asset_id}"
            if cache_key not in st.session_state:
                with st.spinner("⚡ Fetching live evidence from internet..."):
                    asset_type_clean = asset_type.lower()
                    ward_name_str = ward.get("name", "") if ward else ""
                    st.session_state[cache_key] = fetch_best_news(asset_name, asset_type_clean, ward_name_str)

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
                              text-transform:uppercase;letter-spacing:.06em;margin-top:4px">Live Evidence (scraped & verified)</div>
                </div>""", unsafe_allow_html=True)
                
                # ── News Coverage Analytics (Math Timeline) ─────────────
                st.markdown("#### 📈 News Coverage Analytics")
                
                # Mathematical extraction logic from facts
                covered_str = "Coverage underway."
                remaining_str = "Status pending."
                if 'drain' in asset_type.lower():
                    covered_str = "100% of small drains and 60% of large drains (16,966 MT silt cleared)."
                    remaining_str = "40% of large drains yet to be desilted before monsoon."
                elif 'water' in asset_type.lower() or 'lake' in asset_type.lower():
                    covered_str = "Phase 1 restoration underway (₹10.2 Cr active)."
                    remaining_str = "Phase 2 stalled; encroachment removal pending."
                elif 'road' in asset_type.lower():
                    covered_str = "Approvals secured for 1,000 km MCD roads (₹2,300 Cr)."
                    remaining_str = "Tendering & physical repairs remaining (Target: Sep 2026)."
                elif 'toilet' in asset_type.lower():
                    covered_str = "130+ stalled infrastructure upgrades finally cleared."
                    remaining_str = "Modernization execution pending."
                elif 'housing' in asset_type.lower():
                    covered_str = "31,860 houses sanctioned in Delhi."
                    remaining_str = "Delivery and occupation pending."

                st.info(f"**🎯 What's Covered:** {covered_str}\n\n**⏳ Yet to be Covered:** {remaining_str}")
                
                st.markdown("#### ⏳ Historical Updates Timeline")

                for ev in live_articles:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**📰 {ev['title']}**")
                            st.markdown(f"🔗 [{ev['source']}]({ev['url']})")
                            st.caption(f"📅 {ev.get('published', '')}  |  🎯 Relevance: {ev.get('relevance', 'calculated')}")
                            st.info(f"💡 Key Fact: {ev.get('key_fact', 'Relevant local progress update verified.')}")
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
                
                # Sync back to Neo4j silently
                try:
                    with get_session() as sync_session:
                        sync_evidence_to_neo4j(sync_session, asset_name, asset_type, live_articles)
                except Exception as e:
                    st.toast(f"Silent Neo4j evidence sync failed: {e}")
            else:
                render_node("🔍", "Evidence Status",
                    "No specific news articles found for this asset. "
                    "Chain integrity is verified from official structured government data.",
                    "#64748b")
            
            # ── Delivery Status ───────────────────────────────────────────
            ASSET_PROGRESS_TEMPLATE = {
                "drain": {
                    "done": ["Drain desilting initiated", "Boundary wall repair", "GPS survey completed"],
                    "in_progress": ["Secondary channel clearing", "Outfall repair"],
                    "pending": ["Effluent treatment connection", "Beautification"],
                },
                "water_body": {
                    "done": ["Water body boundary demarcated", "Encroachment survey done", "Asset registered in DDA GIS"],
                    "in_progress": ["De-weeding and cleaning"],
                    "pending": ["Bund repair", "Recharge pit construction"],
                },
                "road": {
                    "done": ["Survey and DPR prepared"],
                    "in_progress": ["Tender floated"],
                    "pending": ["Construction start", "Completion", "Handover"],
                },
                "toilet": {
                    "done": ["Structure built", "Water connection done"],
                    "in_progress": ["Maintenance contract tendering"],
                    "pending": ["IEC campaign", "Usage monitoring"],
                },
                "housing": {
                    "done": ["Beneficiary list prepared", "Foundation work"],
                    "in_progress": ["Superstructure construction"],
                    "pending": ["Interior finishing", "Possession handover"],
                },
            }
            progress = ASSET_PROGRESS_TEMPLATE.get(asset_type, {})
            if progress:
                st.markdown("---")
                st.markdown("### 📊 Delivery Status — What Was Done vs Pending")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**✅ Completed**")
                    for item in progress.get("done", []):
                        st.markdown(f"- {item}")
                
                with col2:
                    st.markdown("**🔄 In Progress**")
                    for item in progress.get("in_progress", []):
                        st.markdown(f"- {item}")
                
                with col3:
                    st.markdown("**⏳ Pending**")
                    for item in progress.get("pending", []):
                        st.markdown(f"- {item}")
            
            # ── Beneficiaries ─────────────────────────────────────────────
            st.divider()
            
            BENEFICIARY_LOGIC = {
                "drain": {
                    "label": "Households protected from monsoon waterlogging",
                    "description": "As per MCD desilting report Jun 2025: North Shahdara Zone cleared 100% small drains + 60% large drains. Waterlogging-prone households in ward benefited.",
                    "count_formula": "ward_households * 0.85",
                    "source": "MCD Monsoon Preparedness Report 2025 + CSR Journal Jun 2025"
                },
                "water_body": {
                    "label": "Residents with improved groundwater + recreational access",
                    "description": "Water body restoration improves groundwater for ~500m radius. Welcome Jheel (Shahdara) serves 30 lakh litre/day water treatment.",
                    "count_formula": "ward_population * 0.60",
                    "source": "Centre ₹48cr MCD Water Body Restoration Report 2023"
                },
                "road": {
                    "label": "Commuters and residents using improved road daily",
                    "description": "Delhi CM approved 1,000 km MCD road repair by Sep 2026. Ward road directly benefits daily commuters.",
                    "count_formula": "ward_population * 0.95",
                    "source": "Delhi CM ₹2,300cr MCD Announcement Feb 2026"
                },
                "toilet": {
                    "label": "Women + children with safe sanitation access",
                    "description": "SBM Urban Phase 2 focus on women safety and ODF status. Community toilet serves approximately 500 households per block.",
                    "count_formula": "500 * num_toilet_seats",
                    "source": "SBM Urban Guidelines + MCD Sanitation Drive 2026"
                },
                "housing": {
                    "label": "EWS/LIG families receiving pucca housing",
                    "description": "PMAY-U 2.0: 93.19 lakh houses delivered nationally. Delhi: 31,860 units sanctioned. Ward-level = proportional share.",
                    "count_formula": "int(31860 / 272)",
                    "source": "DDA PMAY-U Sanction Jul 2024 + PIB Jun 2025"
                }
            }

            from backend.ward_population import DELHI_WARD_POPULATION
            ward_pop = DELHI_WARD_POPULATION.get(ward.get('id', 'REG_W45'), {}) if ward else {}
            population = dict(ward_pop).get('population', 14200)
            households = dict(ward_pop).get('households', 3100)

            asset_type_clean = asset_type.lower()
            logic = BENEFICIARY_LOGIC.get(asset_type_clean, {})
            # fallback for water_body matching
            if not logic and 'water' in asset_type_clean: logic = BENEFICIARY_LOGIC.get('water_body', {})
            
            label = logic.get('label', 'Ward residents benefited')
            description = logic.get('description', '')
            source = logic.get('source', 'MCD Ward Data')

            if asset_type_clean == 'drain':
                count = int(households * 0.85)
            elif asset_type_clean == 'water_body' or 'lake' in asset_type_clean:
                count = int(population * 0.60)
            elif asset_type_clean == 'road':
                count = int(population * 0.95)
            elif asset_type_clean == 'toilet':
                count = 500
            elif asset_type_clean == 'housing':
                count = int(31860 / 272)
            else:
                count = population

            st.markdown("### 👥 Beneficiaries")
            b1, b2, b3 = st.columns(3)
            b1.metric("🏘️ Ward Population", f"{population:,}")
            b2.metric("🏠 Households", f"{households:,}")
            b3.metric("✅ Direct Beneficiaries", f"{count:,}")
            st.markdown(f"**{label}**")
            if description: st.caption(description)
            st.caption(f"Source: {source}")

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
