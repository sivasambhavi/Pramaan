"""
02_Scheme_Tracker.py — PRAMAAN v5
Scheme Tracker: interactive knowledge graph (streamlit-agraph), Type 1/2 scheme panels,
cross-domain connections, node detail panel.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
from utils.api import safe_get
from utils.events import EVENTS_BY_ID, render_event_dropdown
from components.topnav import render_topnav

NODE_CONFIG = {
    "Event":    {"color": "#f97316", "size": 26, "shape": "dot",     "desc": "High-impact incidents"},
    "Domain":   {"color": "#a78bfa", "size": 20, "shape": "diamond", "desc": "Policy areas"},
    "Region":   {"color": "#22c55e", "size": 16, "shape": "dot",     "desc": "Geographic locations"},
    "Actor":    {"color": "#38bdf8", "size": 16, "shape": "dot",     "desc": "Govt bodies & agencies"},
    "Scheme":   {"color": "#facc15", "size": 14, "shape": "dot",     "desc": "Funding programmes"},
    "Policy":   {"color": "#fb7185", "size": 14, "shape": "dot",     "desc": "Legislation & policy"},
    "Impact":   {"color": "#94a3b8", "size": 8,  "shape": "dot",     "desc": "Measured outcomes"},
    "Evidence": {"color": "#e2e8f0", "size": 7,  "shape": "dot",     "desc": "PIB · NDMA · ISRO sources"},
}

# Node types that show labels — Impact/Evidence hidden to reduce clutter
_LABELLED_TYPES = {"Event", "Domain", "Actor", "Region", "Scheme", "Policy"}

DOMAIN_COLORS = {
    "Climate":     "#22c55e",
    "Defense":     "#f97316",
    "Economics":   "#38bdf8",
    "Society":     "#fb7185",
    "Governance":  "#06b6d4",
    "Geopolitics": "#a78bfa",
    "Technology":  "#facc15",
}

EDGE_COLORS = {
    # Cross-domain — gold, dashed, thick
    "CONNECTED_TO": "#FFD700",
    # Causation / action — orange
    "TRIGGERED":    "#f97316",
    "CAUSED":       "#f97316",
    "CAUSED_BY":    "#f97316",
    # Impact / harm — red
    "IMPACTED":     "#ef4444",
    "IMPACTS":      "#ef4444",
    # Positive / activated — green
    "ACTIVATED":    "#22c55e",
    "PROVEN_BY":    "#22c55e",
    "OCCURRED_IN":  "#22c55e",
    # Policy / governance — purple
    "GOVERNED_BY":  "#a78bfa",
    "MANAGED_BY":   "#a78bfa",
    "BELONGS_TO":   "#a78bfa",
    "ALSO_IN":      "#a78bfa",
    # Funding — yellow
    "FUNDED_BY":    "#facc15",
    # Structural — muted
    "PART_OF":      "#475569",
    "LOCATED_IN":   "#475569",
}

# Per-relationship visual properties: (width, dashes, arrows)
EDGE_STYLE = {
    "CONNECTED_TO": (3,   True,  True),   # gold dashed thick
    "TRIGGERED":    (2,   False, True),
    "CAUSED":       (2,   False, True),
    "CAUSED_BY":    (2,   False, True),
    "IMPACTED":     (2,   False, True),
    "IMPACTS":      (2,   False, True),
    "ACTIVATED":    (2,   False, True),
    "PROVEN_BY":    (1.5, False, False),
    "GOVERNED_BY":  (1.5, False, False),
    "MANAGED_BY":   (1.5, False, False),
    "BELONGS_TO":   (1,   False, False),
    "ALSO_IN":      (1,   False, False),
    "FUNDED_BY":    (1.5, False, True),
    "OCCURRED_IN":  (1,   False, False),
    "PART_OF":      (1,   False, False),
    "LOCATED_IN":   (1,   False, False),
}

# Known source/agency suffixes to strip from labels
_SOURCE_TOKENS = {"pib", "ndma", "isro", "imd", "ndrf", "mha", "moe", "army",
                  "navy", "govt", "press", "rep", "rpt", "doc", "ord"}

# Type prefix → short readable suffix added to label
_TYPE_SUFFIX = {
    "EVD_":      "Evd",
    "Evidence_": "Evd",
    "IMP_":      "Impact",
    "Impact_":   "Impact",
    "ACT_":      "",
    "Actor_":    "",
    "EVT_":      "",
    "Event_":    "",
    "SCH_":      "Scheme",
    "Scheme_":   "Scheme",
    "REG_":      "",
    "Region_":   "",
    "POL_":      "Policy",
    "Policy_":   "Policy",
    "DOM_":      "",
    "Domain_":   "",
}


def _humanize(raw_id: str) -> str:
    """
    Clean readable label from a raw DB node ID.
    EVD_WAYANAD_PIB    → "Wayanad"
    IMP_DANA_NDRF_2024 → "Dana"
    EVT_CHAMOLI_2021   → "Chamoli 2021"
    ACT_NDMA           → "NDMA"
    DOM_CLIMATE        → "Climate"
    """
    # Strip type prefix
    for prefix in _TYPE_SUFFIX:
        if raw_id.startswith(prefix):
            raw_id = raw_id[len(prefix):]
            break

    # Keep tokens that are not source/agency names
    # Preserve known acronyms (all-caps ≤ 5 chars) as-is; title-case others
    parts = []
    for tok in raw_id.split("_"):
        tl = tok.lower()
        if tl in _SOURCE_TOKENS:
            continue
        # Keep short ALL-CAPS tokens as acronyms (e.g. NDMA, IMD, MHA)
        if tok.isupper() and len(tok) <= 5:
            parts.append(tok)
        else:
            parts.append(tok.capitalize())

    label = " ".join(parts).strip()
    return label[:18].strip() if label else raw_id[:18]


def _humanize_edge(edge_type: str) -> str:
    return edge_type.replace("_", " ").title()


def _get_ego_ids(event_id: str, graph_data: dict) -> set:
    """Return the event node + all directly connected node IDs."""
    ids = {event_id}
    for e in graph_data.get("edges", []):
        if e["from"] == event_id:
            ids.add(e["to"])
        elif e["to"] == event_id:
            ids.add(e["from"])
    return ids


def _build_graph(graph_data: dict, filter_type: set | None = None, focus_ids: set | None = None):
    nodes, edges, seen_ids = [], [], set()

    for n in graph_data.get("nodes", []):
        ntype = n.get("type", "Event")
        if filter_type and ntype not in filter_type:
            continue
        in_focus   = focus_ids is None or n["id"] in focus_ids
        cfg        = NODE_CONFIG.get(ntype, NODE_CONFIG["Event"])
        full_name  = n.get("label") or n["id"]          # full name for tooltip
        short_label = _humanize(full_name)               # short label for canvas

        # Only show canvas labels for important types — hide Impact/Evidence
        canvas_label = short_label if ntype in _LABELLED_TYPES else ""

        color      = cfg["color"] if in_focus else "#2d3f55"
        size       = cfg["size"]  if in_focus else max(cfg["size"] - 4, 5)
        font_color = "#e2e8f0"    if in_focus else "#475569"
        font_size  = 10           if in_focus else 8

        # Rich tooltip: full name + type + description if available
        props       = n.get("props", {})
        tooltip     = f"{ntype}: {full_name}"
        if props.get("description"):
            tooltip += f"\n{props['description'][:120]}"
        elif props.get("type"):
            tooltip += f"\nType: {props['type']}"

        nodes.append(Node(
            id=n["id"],
            label=canvas_label,
            size=size,
            color=color,
            title=tooltip,
            shape=cfg["shape"],
            font={"color": font_color, "size": font_size, "strokeWidth": 1, "strokeColor": "#020b14"},
        ))
        seen_ids.add(n["id"])

    for e in graph_data.get("edges", []):
        if e["from"] not in seen_ids or e["to"] not in seen_ids:
            continue
        etype    = e.get("type", "")
        in_focus = focus_ids is None or (e["from"] in focus_ids and e["to"] in focus_ids)
        if in_focus:
            color                = EDGE_COLORS.get(etype, "#475569")
            width, dashes, arrow = EDGE_STYLE.get(etype, (1.5, False, True))
        else:
            color, width, dashes, arrow = "#2d3f55", 0.5, False, False
        hover = _humanize_edge(etype)
        if e.get("reason"):
            hover += f": {e['reason']}"
        edges.append(Edge(
            source=e["from"], target=e["to"],
            color=color, width=width,
            dashes=dashes,
            arrows="to" if arrow else "",
            title=hover,
        ))

    return nodes, edges


def page():
    st.set_page_config(page_title="Scheme Tracker – PRAMAAN", layout="wide")
    render_topnav(active_page="Scheme Tracker")

    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; }
    section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
    div[data-testid="stVerticalBlock"] > div:first-child { margin-top: 0 !important; }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(167,139,250,0.7), 0 0 30px rgba(167,139,250,0.4), 0 0 50px rgba(167,139,250,0.2); }
        50%       { text-shadow: 0 0 25px rgba(167,139,250,1), 0 0 60px rgba(167,139,250,0.8), 0 0 100px rgba(167,139,250,0.5); }
    }
    iframe { background-color: #f8fafc !important; }
    /* Style tabs to match brand */
    button[data-baseweb="tab"] { font-size: 11px !important; padding: 6px 12px !important; }
    div[data-baseweb="select"] * { font-size: 12px !important; }
    div[data-testid="stToggle"] label p { font-size: 10px !important; }
    div[data-testid="stCheckbox"] label p { font-size: 11px !important; }
    </style>
    """, unsafe_allow_html=True)

    if "graph_clicked" not in st.session_state:
        st.session_state.graph_clicked = None
    if "ontology_sel" not in st.session_state:
        st.session_state.ontology_sel = None    # bare event_id or None = All Events
    if "active_types" not in st.session_state:
        st.session_state.active_types = set(NODE_CONFIG.keys())

    # Deep-link from Intelligence Map — auto-focus the passed event
    if "deep_link_event" in st.session_state:
        raw = st.session_state.pop("deep_link_event")
        # raw may be "Event_EVT_..." or bare "EVT_..." — normalise to bare id
        bare = raw[len("Event_"):] if raw.startswith("Event_") else raw
        st.session_state.ontology_sel = bare
        st.session_state.pop("focus_select", None)

    header_slot = st.empty()

    st.markdown(
        '<div style="font-size:12px;color:#475569;margin-bottom:4px;margin-top:2px;">'
        'Interactive knowledge graph — how events, actors, schemes and evidence connect '
        'across 7 domains. Click any node to explore. Scroll to zoom · Drag to pan.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Fetch ─────────────────────────────────────────────────────────────────
    with st.spinner("Loading ontology graph from Neo4j..."):
        graph_data = safe_get("/ontology/graph", timeout=20, silent=False)

    if not graph_data:
        st.error("Could not load graph. Is the backend running?")
        return

    stats       = graph_data.get("stats", {})
    total_nodes = stats.get("total_nodes", len(graph_data.get("nodes", [])))
    total_edges = stats.get("total_edges", len(graph_data.get("edges", [])))
    domains     = len(set(n.get("domain", "") for n in graph_data.get("nodes", []) if n.get("domain"))) or 7
    cross_count = sum(1 for e in graph_data.get("edges", []) if e.get("type") == "CONNECTED_TO")

    header_slot.markdown(f"""
    <div style="position:sticky;top:52px;z-index:100;background:#020b14;
                padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:6px;
                display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.9em;font-weight:800;color:#a78bfa;font-family:'Cinzel',serif;
                   letter-spacing:0.08em;white-space:nowrap;animation:glowPulse 2.5s ease-in-out infinite;">
        SCHEME TRACKER
      </span>
      <span style="font-size:0.75em;color:#64748b;white-space:nowrap;">
        {total_nodes} Entities &nbsp;·&nbsp; {total_edges} Relationships &nbsp;·&nbsp;
        {domains} Domains &nbsp;·&nbsp; {cross_count} Cross-Domain Links
        &nbsp;·&nbsp; <span style="color:#475569;">Neo4j · PIB · NDMA · ISRO</span>
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Top control row: event focus + toggles + reset ───────────────────────
    ecol, tcol1, tcol2, rcol = st.columns([3, 0.8, 0.9, 0.7], gap="small")
    with ecol:
        render_event_dropdown("ontology_sel", "focus_select", include_all=True)

    # Derive the Neo4j node ID used for ego-graph highlighting
    _oid = st.session_state.get("ontology_sel")
    focus_event = f"Event_{_oid}" if _oid else None

    with tcol1:
        physics    = st.checkbox("Physics",     value=True,  key="phy_cb")
    with tcol2:
        show_cross = st.checkbox("Cross-links", value=True,  key="cross_cb")
    with rcol:
        if focus_event:
            if st.button("Reset", use_container_width=True):
                st.session_state.ontology_sel = None
                st.session_state.pop("focus_select", None)
                st.rerun()

    active_filter = st.session_state.active_types or set(NODE_CONFIG.keys())
    focus_ids = _get_ego_ids(focus_event, graph_data) if focus_event else None

    # ── 3-column layout ───────────────────────────────────────────────────────
    col_left, col_graph, col_detail = st.columns([1, 2.8, 1], gap="medium")

    # ══ LEFT — tabbed panel ═══════════════════════════════════════════════════
    with col_left:
        tab1, tab2 = st.tabs(["Node Index", "Connections"])

        # ── Tab 1: Node Index (click to toggle type on/off) ──────────────────
        with tab1:
            # All-types counts
            all_type_counts = {}
            for n in graph_data.get("nodes", []):
                t = n.get("type", "Event")
                all_type_counts[t] = all_type_counts.get(t, 0) + 1

            sel_type = None
            if st.session_state.graph_clicked:
                nd = next((n for n in graph_data.get("nodes", [])
                           if n["id"] == st.session_state.graph_clicked), None)
                if nd:
                    sel_type = nd.get("type")

            for ntype, cfg in NODE_CONFIG.items():
                count     = all_type_counts.get(ntype, 0)
                is_on     = ntype in st.session_state.active_types
                shape_r   = "50%" if cfg["shape"] == "dot" else "3px"
                dot_color  = cfg["color"] if is_on else "#334155"
                name_color = cfg["color"] if is_on else "#475569"
                bg         = "#1a2035" if ntype == sel_type else ("#111827" if is_on else "#0a0f1a")
                border_c   = f'{cfg["color"]}88' if is_on else "#1e293b"

                card_col, tog_col = st.columns([5, 1], gap="small")
                with card_col:
                    st.markdown(
                        f'<div style="border-left:3px solid {border_c};padding:7px 9px;'
                        f'background:{bg};border-radius:4px;margin-bottom:4px;'
                        f'border:1px solid rgba(71,85,105,0.15);border-left:3px solid {border_c};">'
                        f'<div style="display:flex;align-items:center;gap:6px;">'
                        f'<span style="width:8px;height:8px;border-radius:{shape_r};background:{dot_color};'
                        f'flex-shrink:0;box-shadow:0 0 4px {dot_color}88;"></span>'
                        f'<span style="font-size:11px;font-weight:600;color:{name_color};">{ntype}</span>'
                        f'<span style="font-size:10px;color:#334155;margin-left:auto;">{count}</span>'
                        f'</div>'
                        f'<div style="font-size:10px;color:{"#475569" if is_on else "#1e293b"};'
                        f'padding-left:14px;margin-top:2px;">{cfg["desc"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with tog_col:
                    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                    val = st.toggle("", value=is_on, key=f"toggle_{ntype}", label_visibility="collapsed")
                    if val != is_on:
                        if val:
                            st.session_state.active_types.add(ntype)
                        else:
                            st.session_state.active_types.discard(ntype)
                        st.rerun()


        # ── Tab 2: Cross-Domain Links ─────────────────────────────────────────
        with tab2:
            if show_cross:
                xd = safe_get("/ontology/cross-domain", silent=True)
                if xd and xd.get("connections"):
                    for conn in xd["connections"]:
                        fn      = conn.get("from_name", "")
                        tn      = conn.get("to_name", "")
                        reason  = conn.get("reason", "")
                        fd_raw  = conn.get("from_domain", "")
                        td_raw  = conn.get("to_domain", "")
                        # Domain stored as "DOM_CLIMATE" → strip prefix → "Climate"
                        fd      = fd_raw.replace("DOM_", "").title() if fd_raw else ""
                        td      = td_raw.replace("DOM_", "").title() if td_raw else ""
                        fc      = DOMAIN_COLORS.get(fd, "#94a3b8")
                        tc      = DOMAIN_COLORS.get(td, "#94a3b8")
                        st.markdown(
                            f'<div style="background:#0a1628;border:1px solid rgba(255,215,0,0.15);'
                            f'border-left:3px solid #FFD700;border-radius:6px;'
                            f'padding:8px 10px;margin-bottom:6px;">'
                            f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;">'
                            f'<span style="width:7px;height:7px;border-radius:50%;background:{fc};flex-shrink:0;box-shadow:0 0 4px {fc}88;"></span>'
                            f'<span style="font-size:11px;font-weight:700;color:{fc} !important;">{fn}</span>'
                            f'<span style="font-size:9px;color:#475569 !important;margin-left:2px;">{fd}</span>'
                            f'</div>'
                            f'<div style="font-size:10px;color:#475569;margin:1px 0 1px 12px;">↓</div>'
                            f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:4px;">'
                            f'<span style="width:7px;height:7px;border-radius:50%;background:{tc};flex-shrink:0;box-shadow:0 0 4px {tc}88;"></span>'
                            f'<span style="font-size:11px;font-weight:700;color:{tc} !important;">{tn}</span>'
                            f'<span style="font-size:9px;color:#475569 !important;margin-left:2px;">{td}</span>'
                            f'</div>'
                            f'<div style="font-size:9.5px;color:#64748b;padding-left:12px;'
                            f'font-style:italic;line-height:1.4;">{reason}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        '<div style="font-size:11px;color:#334155;padding:8px;">Enable Cross-links toggle to load connections.</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    '<div style="font-size:11px;color:#334155;padding:8px;">Enable the Cross-links toggle above to see connections.</div>',
                    unsafe_allow_html=True,
                )

    # ══ RIGHT — full graph ════════════════════════════════════════════════════
    with col_graph:
        # Focus mode banner
        if focus_ids:
            _focus_tuple   = EVENTS_BY_ID.get(st.session_state.get("ontology_sel"))
            focused_name   = _focus_tuple[1] if _focus_tuple else st.session_state.get("ontology_sel", "")
            neighbor_count = len(focus_ids) - 1
            st.markdown(
                f'<div style="background:#0a1628;border:1px solid #f97316;border-left:4px solid #f97316;'
                f'border-radius:8px;padding:7px 12px;margin-bottom:6px;display:flex;align-items:center;gap:10px;">'
                f'<span style="font-size:11px;font-weight:700;color:#f97316;">Focus Mode</span>'
                f'<span style="font-size:11px;color:#94a3b8;">{focused_name}</span>'
                f'<span style="font-size:10px;color:#475569;margin-left:4px;">· {neighbor_count} connected nodes</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        nodes, edges = _build_graph(graph_data, filter_type=active_filter, focus_ids=focus_ids)

        # When cross-links toggle is OFF, hide CONNECTED_TO edges entirely
        if not show_cross:
            edges = [e for e in edges if e.color != EDGE_COLORS["CONNECTED_TO"]]

        config = Config(
            width="100%",
            height=640,
            directed=True,
            physics=physics,
            hierarchical=False,
            node={"labelProperty": "label"},
            edge={"labelProperty": "title", "smooth": {"type": "continuous"}},
            interaction={
                "hover": True,
                "tooltipDelay": 100,
                "navigationButtons": False,
                "keyboard": True,
                "zoomView": True,
                "dragView": True,
                "selectConnectedEdges": True,
                "multiselect": False,
                "hideEdgesOnDrag": True,
            },
            manipulation=False,
        )

        clicked = agraph(nodes=nodes, edges=edges, config=config)

        if clicked:
            st.session_state.graph_clicked = clicked
            # Auto-focus when an Event node is clicked
            clicked_node = next((n for n in graph_data.get("nodes", []) if n["id"] == clicked), None)
            if clicked_node and clicked_node.get("type") == "Event":
                # clicked is "Event_EVT_..." — strip prefix to get bare event_id
                bare = clicked[len("Event_"):] if clicked.startswith("Event_") else clicked
                if st.session_state.get("ontology_sel") != bare:
                    st.session_state.ontology_sel = bare
                    # Clear selectbox cache so it reflects new focus on rerun
                    st.session_state.pop("focus_select", None)
                    st.rerun()

    # ══ RIGHT — node detail panel ══════════════════════════════════════════════
    with col_detail:
        st.markdown(
            "<div style='font-size:0.7em;color:#475569;text-transform:uppercase;"
            "letter-spacing:0.1em;font-weight:700;margin-bottom:8px;'>NODE DETAIL</div>",
            unsafe_allow_html=True,
        )

        sel_node_id = st.session_state.graph_clicked
        if not sel_node_id:
            st.markdown(
                '<div style="background:#0a1628;border:1px dashed #1e293b;border-radius:10px;'
                'padding:24px 14px;text-align:center;margin-top:8px;">'
                '<div style="font-size:18px;margin-bottom:8px;">🔍</div>'
                '<div style="font-size:11px;color:#334155;line-height:1.6;">'
                'Click any node on the graph to explore its details</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            nd = next((n for n in graph_data.get("nodes", []) if n["id"] == sel_node_id), None)
            if nd:
                ntype  = nd.get("type", "Event")
                color  = NODE_CONFIG.get(ntype, {}).get("color", "#f97316")
                nlabel = _humanize(nd.get("label") or sel_node_id)
                props  = nd.get("props", {})

                # Clean field name mapping
                FIELD_LABELS = {
                    "description": "Description",
                    "date":        "Date",
                    "severity":    "Severity",
                    "value":       "Value",
                    "unit":        "Unit",
                    "source":      "Source",
                    "url":         "Source URL",
                    "budget_inr_cr": "Budget (₹ Cr)",
                    "role":        "Role",
                    "type":        "Sub-type",
                    "title":       "Title",
                }
                # Fields to skip (raw IDs, redundant keys)
                SKIP_FIELDS = {"name", "impact_id", "event_id", "actor_id",
                               "scheme_id", "evidence_id", "region_id", "policy_id"}

                # Type badge + name
                st.markdown(
                    f'<div style="background:#0a1628;border:1px solid {color}44;'
                    f'border-left:4px solid {color};border-radius:10px;padding:12px 14px;'
                    f'overflow:hidden;word-break:break-word;">'
                    f'<span style="background:{color}22;color:{color};font-size:9.5px;font-weight:700;'
                    f'padding:2px 7px;border-radius:4px;border:1px solid {color}44;'
                    f'text-transform:uppercase;letter-spacing:0.05em;">{ntype}</span>'
                    f'<div style="font-size:13px;font-weight:700;color:{color};margin-top:8px;'
                    f'line-height:1.3;overflow-wrap:break-word;">{nlabel}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Clean property rows
                rows_html = ""
                for k, v in props.items():
                    if not v or k in SKIP_FIELDS:
                        continue
                    label = FIELD_LABELS.get(k, k.replace("_", " ").title())
                    display_v = str(v).replace("_", " ").title() if isinstance(v, str) else str(v)
                    if k == "url":
                        display_v = f'<a href="{v}" target="_blank" style="color:{color};font-size:10px;">View source →</a>'
                    rows_html += (
                        f'<div style="display:flex;gap:8px;padding:6px 0;'
                        f'border-bottom:1px solid #0f1e35;">'
                        f'<span style="font-size:10px;color:#475569;min-width:72px;max-width:72px;'
                        f'flex-shrink:0;overflow:hidden;">{label}</span>'
                        f'<span style="font-size:10px;color:#94a3b8;line-height:1.4;'
                        f'overflow-wrap:break-word;word-break:break-word;min-width:0;">{display_v}</span>'
                        f'</div>'
                    )

                if rows_html:
                    st.markdown(
                        f'<div style="background:#060f1e;border:1px solid #1e293b;border-radius:8px;'
                        f'padding:8px 12px;margin-top:6px;overflow:hidden;">{rows_html}</div>',
                        unsafe_allow_html=True,
                    )

                # Live Feed button — only for Event nodes
                if ntype == "Event":
                    bare_id = sel_node_id.replace("Event_", "", 1)
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <style>
                    button[kind="primary"] {{
                        background: linear-gradient(135deg, {color}, {color}cc) !important;
                        border: none !important;
                        color: #fff !important;
                        font-family: Outfit, sans-serif !important;
                        font-weight: 700 !important;
                        font-size: 0.82em !important;
                        letter-spacing: 0.03em !important;
                        border-radius: 10px !important;
                        box-shadow: 0 4px 16px {color}55 !important;
                    }}
                    button[kind="primary"]:hover {{
                        box-shadow: 0 6px 24px {color}88 !important;
                        opacity: 0.92 !important;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                    if st.button("View in Delivery Monitor  →", key=f"goto_feed_{sel_node_id}",
                                 use_container_width=True, type="primary"):
                        st.session_state["deep_link_feed"] = bare_id
                        st.switch_page("pages/03_Delivery_Monitor.py")

    # ══ SCHEME DECISION PANEL ════════════════════════════════════════════════
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.7em;color:#475569;text-transform:uppercase;'
        'letter-spacing:0.1em;font-weight:700;margin-bottom:10px;border-top:1px solid #1e293b;padding-top:14px;">'
        'SCHEME DECISION PANEL — TYPE 1 vs TYPE 2</div>',
        unsafe_allow_html=True,
    )

    # Static scheme classification
    TYPE1_SCHEMES = [
        {"name": "State Disaster Response Fund",    "id": "SCH_SDRF",      "budget": "₹43,900 Cr", "trigger": "Flood / Cyclone / Disaster", "ministry": "MHA",  "events": ["Delhi Floods", "Cyclone Dana", "Wayanad", "Chamoli"]},
        {"name": "National Disaster Response Fund", "id": "SCH_NDRF_FUND", "budget": "₹12,390 Cr", "trigger": "National emergency declared",  "ministry": "MHA",  "events": ["Delhi Floods", "Cyclone Dana", "Wayanad"]},
        {"name": "PM-KUSUM / Rupaya Solar",         "id": "SCH_PLI_SEMI",  "budget": "₹76,000 Cr", "trigger": "Semiconductor supply shock",   "ministry": "MoCI", "events": ["Tata Semiconductor Fab"]},
    ]

    TYPE2_SCHEMES = [
        {"name": "AMRUT 2.0",                  "id": "SCH_AMRUT",    "budget": "₹66,750 Cr", "focus": "Urban water/drainage infrastructure", "ministry": "MoHUA",  "delhi": "3 drainage projects · ₹5.38 Cr · 2 completed ✅"},
        {"name": "PMAY-U (Urban)",             "id": "SCH_PMAY",     "budget": "₹401 Cr",    "focus": "Affordable urban housing",            "ministry": "MoHUA",  "delhi": "17,067 houses · ₹401 Cr · 100% complete ✅"},
        {"name": "Ayushman Bharat PMJAY",      "id": "SCH_AYUSHMAN", "budget": "₹7,200 Cr",  "focus": "Universal health coverage",           "ministry": "MoHFW",  "delhi": "7.4 Cr cards issued · 2.2 Cr hospitalised"},
        {"name": "PM SVANidhi",                "id": "SCH_SVANIDHI", "budget": "₹700 Cr",    "focus": "Street vendor micro-credit",          "ministry": "MoHUA",  "delhi": "68.7L beneficiaries · 3rd tranche"},
        {"name": "SBM Urban 2.0",              "id": "SCH_SBM",      "budget": "₹1,400 Cr",  "focus": "Sanitation / waste-free cities",      "ministry": "MoHUA",  "delhi": "ODF+ certified wards"},
        {"name": "Jal Jeevan Mission",         "id": "SCH_JJBY",     "budget": "₹197,000 Cr","focus": "Har ghar jal — tap water to all",     "ministry": "Jal Shakti", "delhi": "14.39 Cr connections (76.7%)"},
        {"name": "DDUGJY Rural Power",         "id": "SCH_DDUGJY",   "budget": "₹12,544 Cr", "focus": "Rural electrification",               "ministry": "Power",  "delhi": "100% village electrification"},
        {"name": "PLI — Semiconductor",        "id": "SCH_PLI_SEMI", "budget": "₹76,000 Cr", "focus": "Domestic chip manufacturing",         "ministry": "MoCI",   "delhi": "Tata / CG Power · ₹1.26 Lakh Cr investment"},
    ]

    t1col, t2col = st.columns([1, 2], gap="large")

    with t1col:
        st.markdown(
            '<div style="background:#0d1826;border:1px solid #ef444433;border-left:4px solid #ef4444;'
            'border-radius:10px;padding:12px 14px;margin-bottom:12px;">'
            '<div style="font-size:11px;font-weight:800;color:#ef4444;text-transform:uppercase;'
            'letter-spacing:0.08em;margin-bottom:8px;">🚨 Type 1 — Event-Triggered Response</div>'
            '<div style="font-size:10.5px;color:#64748b;margin-bottom:10px;line-height:1.5;">'
            'Activated only when a qualifying disaster or emergency is declared. '
            'Funds are released directly to state/national agencies.'
            '</div>',
            unsafe_allow_html=True,
        )
        for s in TYPE1_SCHEMES:
            evts_html = " · ".join(f'<span style="color:#ef444488;">{e}</span>' for e in s["events"])
            st.markdown(
                f'<div style="background:#060f1e;border:1px solid #ef444422;border-radius:8px;'
                f'padding:9px 12px;margin-bottom:6px;">'
                f'<div style="font-size:11.5px;font-weight:700;color:#fca5a5;">{s["name"]}</div>'
                f'<div style="font-size:10px;color:#64748b;margin-top:3px;">'
                f'{s["budget"]} &nbsp;·&nbsp; {s["ministry"]}</div>'
                f'<div style="font-size:9.5px;color:#475569;margin-top:4px;">'
                f'Trigger: <span style="color:#94a3b8;">{s["trigger"]}</span></div>'
                f'<div style="font-size:9.5px;color:#334155;margin-top:3px;">Events: {evts_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with t2col:
        st.markdown(
            '<div style="background:#0a1a0a;border:1px solid #22c55e33;border-left:4px solid #22c55e;'
            'border-radius:10px;padding:12px 14px;margin-bottom:12px;">'
            '<div style="font-size:11px;font-weight:800;color:#22c55e;text-transform:uppercase;'
            'letter-spacing:0.08em;margin-bottom:8px;">🏗️ Type 2 — Ongoing Delivery Schemes</div>'
            '<div style="font-size:10.5px;color:#64748b;margin-bottom:10px;line-height:1.5;">'
            'Always-on implementation programmes. Triggered events create urgency and unlock '
            'additional fund releases, but delivery is continuous.'
            '</div>',
            unsafe_allow_html=True,
        )
        cols_a, cols_b = st.columns(2, gap="small")
        half = len(TYPE2_SCHEMES) // 2
        for i, s in enumerate(TYPE2_SCHEMES):
            target_col = cols_a if i < half else cols_b
            with target_col:
                st.markdown(
                    f'<div style="background:#060f1e;border:1px solid #22c55e22;border-radius:8px;'
                    f'padding:9px 12px;margin-bottom:6px;">'
                    f'<div style="font-size:11.5px;font-weight:700;color:#86efac;">{s["name"]}</div>'
                    f'<div style="font-size:10px;color:#64748b;margin-top:2px;">'
                    f'{s["budget"]} &nbsp;·&nbsp; {s["ministry"]}</div>'
                    f'<div style="font-size:9.5px;color:#475569;margin-top:3px;">{s["focus"]}</div>'
                    f'<div style="font-size:9.5px;color:#22c55e88;margin-top:4px;border-top:1px solid #1e293b;'
                    f'padding-top:3px;">Delhi: {s["delhi"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Delivery chain CTA ────────────────────────────────────────────────────
    st.markdown(
        '<div style="background:#0a1628;border:1px solid #22c55e44;border-radius:10px;'
        'padding:10px 16px;display:flex;align-items:center;gap:16px;margin-top:4px;">'
        '<div style="flex:1;font-size:12px;color:#64748b;">'
        '📍 <strong style="color:#22c55e;">Delhi Pilot</strong> — AMRUT + PMAY delivery tracked to asset level '
        'with real data.gov.in evidence. Click below to see full ground-truth proof chain.'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("View Delhi Pilot → Delivery Monitor", key="goto_delivery_pilot", type="primary"):
        st.session_state["feed_sel"] = "EVT_DELHI_FLOODS_2023"
        st.switch_page("pages/03_Delivery_Monitor.py")
    st.markdown('</div>', unsafe_allow_html=True)


page()
