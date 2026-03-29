"""
voice_text_input() — Streamlit text input with mic icon embedded inside the right edge.
Uses browser Web Speech API (Chrome/Edge). No API key needed.
Sync uses React _valueTracker trick so Streamlit reads typed/spoken text correctly.
"""
import streamlit as st
import streamlit.components.v1 as components


def voice_text_input(
    placeholder: str = "Type or speak…",
    key: str = "voice_input",
    value: str = "",
    help: str = "",
    lang: str = "en-IN",
    auto_submit_btn_text: str = "",
) -> str:
    """
    Renders a dark-themed text input with a mic icon inside the right edge.
    Returns the current string value (same as st.text_input).

    - Click the mic icon to start voice recognition (Web Speech API).
    - Works in Chrome / Edge. Falls back silently in unsupported browsers.
    - auto_submit_btn_text: if set, auto-clicks a button with that text after speech ends.
    """

    # ── Hidden real Streamlit input (Python reads from this) ─────────────────
    escaped_ph = placeholder.replace('"', '\\"')
    st.markdown(f"""
    <style>
    div[data-testid="stTextInput"]:has(input[placeholder="{escaped_ph}"]) {{
        position: absolute !important;
        opacity: 0 !important;
        pointer-events: none !important;
        height: 0 !important;
        min-height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    current = st.text_input(
        label=key,
        value=value,
        placeholder=placeholder,
        key=key,
        help=help,
        label_visibility="collapsed",
    )

    # ── Visual input with embedded mic ────────────────────────────────────────
    auto_click_js = ""
    if auto_submit_btn_text:
        escaped_btn = auto_submit_btn_text.replace("'", "\\'")
        auto_click_js = f"""
      function clickSubmit() {{
        const btns = window.parent.document.querySelectorAll('button');
        for (const btn of btns) {{
          if (btn.innerText.trim() === '{escaped_btn}') {{ btn.click(); return; }}
        }}
      }}
      setTimeout(clickSubmit, 400);
"""

    components.html(f"""
    <!DOCTYPE html><html><head>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap" rel="stylesheet">
    <style>
      *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
      html, body {{ background: transparent; height: 46px; overflow: hidden; }}

      .wrap {{ position: relative; width: 100%; height: 42px; }}

      #vi {{
        width: 100%;
        height: 42px;
        background: rgb(14, 17, 23);
        border: 1px solid rgba(49,51,63,0.9);
        border-radius: 8px;
        color: rgb(250,250,250);
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        padding: 0 46px 0 14px;
        outline: none;
        transition: border-color 0.15s ease;
      }}
      #vi::placeholder {{ color: rgba(250,250,250,0.35); }}
      #vi:focus {{ border-color: rgba(249,115,22,0.6); box-shadow: 0 0 0 2px rgba(249,115,22,0.15); }}

      #mb {{
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        width: 28px;
        height: 28px;
        border-radius: 50%;
        border: none;
        background: transparent;
        color: rgba(250,250,250,0.35);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: color 0.15s ease, background 0.15s ease;
        outline: none;
        padding: 0;
      }}
      #mb:hover {{ color: #f97316; background: rgba(249,115,22,0.1); }}
      #mb.rec {{
        color: #ef4444;
        background: rgba(239,68,68,0.12);
        animation: pulse 1s ease infinite;
      }}
      @keyframes pulse {{
        0%,100% {{ box-shadow: 0 0 0 0 rgba(239,68,68,0.5); }}
        50%      {{ box-shadow: 0 0 0 5px rgba(239,68,68,0); }}
      }}
    </style>
    </head>
    <body>
    <div class="wrap">
      <input id="vi" type="text" placeholder="{placeholder}"
             aria-label="{placeholder}" autocomplete="off" />
      <button id="mb" title="Voice input — click to speak (Chrome/Edge)"
              aria-label="Voice input" onclick="toggle()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2.5"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="23"/>
          <line x1="8"  y1="23" x2="16" y2="23"/>
        </svg>
      </button>
    </div>

    <script>
      const vi  = document.getElementById('vi');
      const btn = document.getElementById('mb');
      const PH  = {repr(placeholder)};
      let rec = null, active = false;

      // Pre-fill visible input from existing Streamlit session value
      (function seedValue() {{
        try {{
          for (const inp of window.parent.document.querySelectorAll('input[type="text"]')) {{
            if (inp.placeholder === PH) {{ if (inp.value) vi.value = inp.value; break; }}
          }}
        }} catch(_) {{}}
      }})();

      // Mirror every keystroke into the hidden Streamlit input via _valueTracker trick
      vi.addEventListener('input', () => syncToStreamlit(vi.value));
      vi.addEventListener('keydown', (e) => {{
        if (e.key === 'Enter') syncToStreamlit(vi.value);
      }});

      function syncToStreamlit(val) {{
        try {{
          for (const inp of window.parent.document.querySelectorAll('input[type="text"]')) {{
            if (inp.placeholder === PH) {{
              // _valueTracker trick: makes React's onChange fire on programmatic update
              const tracker = inp._valueTracker;
              if (tracker) tracker.setValue('');
              Object.getOwnPropertyDescriptor(
                window.parent.HTMLInputElement.prototype, 'value'
              ).set.call(inp, val);
              inp.dispatchEvent(new Event('input',  {{ bubbles: true }}));
              inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
              break;
            }}
          }}
        }} catch(_) {{}}
      }}

      function toggle() {{ active ? stop() : start(); }}

      function start() {{
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {{ btn.title = 'Voice not supported — use Chrome or Edge'; return; }}
        rec = new SR();
        rec.lang = '{lang}';
        rec.interimResults = true;
        rec.onstart  = () => {{
          active = true;
          btn.classList.add('rec');
          btn.title = 'Listening…';
        }};
        rec.onresult = (e) => {{
          const transcript = Array.from(e.results).map(r => r[0].transcript).join('');
          vi.value = transcript;
          if (e.results[e.results.length - 1].isFinal) {{
            syncToStreamlit(transcript);
            {auto_click_js}
          }}
        }};
        rec.onerror = stop;
        rec.onend   = stop;
        rec.start();
      }}

      function stop() {{
        active = false;
        btn.classList.remove('rec');
        btn.title = 'Voice input — click to speak (Chrome/Edge)';
        if (rec) {{ rec.stop(); rec = null; }}
        syncToStreamlit(vi.value);
      }}
    </script>
    </body></html>
    """, height=46, scrolling=False)

    return current
