"""
PRAMAAN Top Navigation Bar
Hides the Streamlit sidebar and renders a fixed 52px dark navbar.
Call render_topnav(active_page) as the first thing in every page's main().
"""
import os, base64
import streamlit as st

PAGES = [
    ("Live Ingestion",        "/Live_Ingestion"),
    ("Global Intelligence", "/Global_Intelligence"),
    ("Ontology Graph",        "/Decision_Engine"),
    ("Crisis Tracker",         "/Crisis_Monitor"),
    ("Scheme Delivery",        "/Delivery_Monitor"),
    ("Proof & Evidence",      "/Proof_and_Evidence"),
    ("Intelligence Verdict",  "/Intelligence_Verdict"),
]

_HIDE_SIDEBAR = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Outfit:wght@700;800&display=swap" rel="stylesheet">
<style>
  [data-testid="stSidebar"]        { display: none !important; }
  [data-testid="collapsedControl"] { display: none !important; }
  #MainMenu                          { visibility: hidden; }
  footer                             { visibility: hidden; }
  header[data-testid="stHeader"]    { height: 0 !important; min-height: 0 !important; }
  [data-testid="stToolbar"]         { display: none !important; }
  [data-testid="stDecoration"]      { display: none !important; }
  [data-testid="stStatusWidget"]    { display: none !important; }
  .block-container {
      padding-top: 0 !important;
      padding-bottom: 1rem !important;
      padding-left: 1.5rem !important;
      padding-right: 1.5rem !important;
      max-width: 100% !important;
  }
  .appview-container .main .block-container { padding-top: 0 !important; }
</style>
"""


_TRYMINDS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Tryminds_logo.jpeg")
)

# Read once at module load — avoids file I/O on every render
def _load_img_tag(path: str, mime: str = "image/jpeg", alt: str = "", style: str = "") -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'<img src="data:{mime};base64,{b64}" alt="{alt}" style="{style}">'

_TRYMINDS_IMG_TAG: str = _load_img_tag(
    _TRYMINDS_PATH,
    alt="Tryminds",
    style="height:32px;width:auto;object-fit:contain;border-radius:6px;opacity:0.9;",
)


def render_topnav(active_page: str | None = None, show_sidebar: bool = False) -> None:
    """Inject fixed top navbar, hide sidebar, push content below bar."""
    st.markdown(_HIDE_SIDEBAR, unsafe_allow_html=True)
    if show_sidebar:
        # Re-show sidebar for pages that need it (overrides _HIDE_SIDEBAR)
        st.markdown("""
        <style>
          [data-testid="stSidebar"]        { display: flex !important; }
          [data-testid="collapsedControl"] { display: flex !important; }
        </style>
        """, unsafe_allow_html=True)

    links_html = ""
    for name, url in PAGES:
        active = name == active_page
        color  = "#FF6B35" if active else "#94a3b8"
        weight = "600"     if active else "500"
        border = "3px solid #FF6B35" if active else "3px solid transparent"
        links_html += (
            f'<a href="{url}" target="_self" style="'
            f'color:{color};text-decoration:none;font-size:13.5px;font-weight:{weight};'
            f'padding:0 18px;height:52px;display:inline-flex;align-items:center;'
            f'border-bottom:{border};transition:color 0.15s ease,border-color 0.15s ease;"'
            f' onmouseover="if(this.style.borderBottomColor===\'transparent\')this.style.color=\'#ffffff\'"'
            f' onmouseout="if(this.style.borderBottomColor===\'transparent\')this.style.color=\'#94a3b8\'"'
            f'>{name}</a>'
        )

    st.markdown(f"""
    <style>
      @keyframes navShine {{
        0%   {{ background-position: 200% center; }}
        100% {{ background-position: -50% center; }}
      }}
      .pramaan-nav {{
        position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
        height: 52px; background: #0D1117;
        border-bottom: 1px solid #1e293b;
        display: flex; align-items: center; padding: 0 28px;
        font-family: 'Inter', sans-serif; gap: 0;
      }}
      .pramaan-nav-brand {{
        font-family: 'Cinzel', serif;
        font-size: 17px; font-weight: 900;
        letter-spacing: 0.16em; margin-right: 32px; flex-shrink: 0;
        text-decoration: none !important;
        background: linear-gradient(105deg, #f97316 0%, #fb923c 28%, #fff4e6 46%, #ffe9b0 52%, #fb923c 68%, #38bdf8 100%);
        background-size: 250% auto;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: navShine 3.5s linear infinite;
      }}
      .pramaan-nav-links {{ display: flex; align-items: stretch; height: 52px; }}
      .pramaan-nav-right {{ margin-left: auto; display: flex; align-items: center; }}
    </style>
    <div class="pramaan-nav">
      <a href="/" target="_self" class="pramaan-nav-brand">PRAMAAN</a>
      <div class="pramaan-nav-links">{links_html}</div>
      <div class="pramaan-nav-right">{_TRYMINDS_IMG_TAG}</div>
    </div>
    """, unsafe_allow_html=True)

    # Spacer pushes Streamlit content below the fixed bar
    st.markdown("<div style='height:54px'></div>", unsafe_allow_html=True)
