import os
import base64
import streamlit as st
import streamlit.components.v1 as components

# =========================
# CSS LOADER
# =========================

def load_css(css_path="static/style.css"):
    """Load CSS from file"""
    if os.path.exists(css_path):
        with open(css_path, 'r') as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# =========================
# FONT LOADER
# =========================

def inject_local_font(font_path="static/AdobeClean.otf",
                      font_name="AdobeClean"):
    """Inject local font into the app"""
    if not os.path.exists(font_path):
        return

    with open(font_path, "rb") as f:
        font_data = base64.b64encode(f.read()).decode()

    ext = os.path.splitext(font_path)[1].lower().replace(".", "")

    mime_map = {
        "ttf": "font/ttf",
        "otf": "font/otf",
        "woff": "font/woff",
        "woff2": "font/woff2"
    }

    format_map = {
        "ttf": "truetype",
        "otf": "opentype",
        "woff": "woff",
        "woff2": "woff2"
    }

    mime = mime_map.get(ext, "font/otf")
    fmt = format_map.get(ext, "opentype")

    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: '{font_name}';
            src: url('data:{mime};base64,{font_data}')
                 format('{fmt}');
        }}
        
        html, body, .stApp {{
            font-family: '{font_name}', sans-serif;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================
# PREMIUM THEME
# =========================

def load_premium_theme():
    """Load premium theme styling"""
    st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        background-attachment: fixed;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15, 12, 41, 0.95) 0%, rgba(36, 36, 62, 0.95) 100%);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Headers */
    h1, h2, h3 {
        background: linear-gradient(135deg, #fff 0%, #00d4ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(102, 126, 234, 0.4);
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1rem;
    }
    
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        color: white;
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00d4ff, #667eea);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    
    /* Make sidebar always visible */
    [data-testid="collapsedControl"] {
        display: none;
    }
    
    /* Text colors */
    p, span, label {
        color: #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)

def hero_banner():
    """Display premium hero banner"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
    ">
        <h1 style="color: white; margin-bottom: 0.5rem;">🤖 AI Real-time GYM Coach</h1>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.1rem;">
            Real-time pose detection with AI voice coaching
        </p>
    </div>
    """, unsafe_allow_html=True)

def metric_card(title, value, icon="📊"):
    """Display a custom metric card"""
    st.markdown(
        f"""
        <div style="
            background: rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 1rem;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        ">
            <div style="font-size: 2rem;">{icon}</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #00d4ff;">{value}</div>
            <div style="color: #cbd5e1;">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def inject_webrtc_styles():
    """Inject styles into WebRTC iframes"""
    components.html(
        """
        <script>
        function patchIframeStyles() {
            const iframes = window.parent.document.querySelectorAll("iframe");
            iframes.forEach((iframe) => {
                try {
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    if (!doc || !doc.head) return;
                    if (doc.getElementById("gymcoach-style")) return;
                    
                    const style = doc.createElement("style");
                    style.id = "gymcoach-style";
                    style.textContent = `
                        button {
                            border-radius: 12px !important;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                            color: white !important;
                            border: none !important;
                            font-weight: 600 !important;
                        }
                        video {
                            border-radius: 16px !important;
                            border: 2px solid #00d4ff !important;
                        }
                    `;
                    doc.head.appendChild(style);
                } catch(err) {}
            });
        }
        setInterval(patchIframeStyles, 1000);
        </script>
        """,
        height=0,
    )
