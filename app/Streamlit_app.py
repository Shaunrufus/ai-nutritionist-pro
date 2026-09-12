import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import joblib
import pandas as pd
import os
import requests

# ===== PAGE CONFIG — must be FIRST Streamlit call =====
st.set_page_config(
    page_title="AI Nutritionist Pro",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== 1. ENVIRONMENT CONFIGURATION =====
def get_api_key():
    """Load OPENROUTER_API_KEY from .env (local) or Streamlit secrets (cloud)."""
    try:
        if "OPENROUTER_API_KEY" in st.secrets:
            return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        pass
    env_path = Path(__file__).resolve().parents[1] / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    return os.getenv("OPENROUTER_API_KEY")

api_key = get_api_key()

# ===== 2. FUTURISTIC GLASSMORPHISM CSS =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

/* ─── Root & Base ─────────────────────────────────────────── */
html, body, .stApp {
    background: #050a14 !important;
    color: #e2eeff !important;
    font-family: 'Inter', sans-serif !important;
}

.stApp {
    background: radial-gradient(ellipse at 20% 10%, rgba(6,182,212,0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(139,92,246,0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(16,185,129,0.04) 0%, transparent 70%),
                linear-gradient(135deg, #050a14 0%, #0a0f24 50%, #060b18 100%) !important;
    min-height: 100vh;
}

/* ─── Animated Orb Background ─────────────────────────────── */
.stApp::before {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: 
        radial-gradient(circle at 20% 20%, rgba(6,182,212,0.04) 0%, transparent 40%),
        radial-gradient(circle at 80% 80%, rgba(139,92,246,0.04) 0%, transparent 40%);
    animation: orbFloat 20s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}
@keyframes orbFloat {
    0%   { transform: translate(0,0) rotate(0deg); }
    100% { transform: translate(30px, 20px) rotate(5deg); }
}

/* ─── Sidebar ──────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(6,10,28,0.95) 0%, rgba(10,15,40,0.98) 100%) !important;
    border-right: 1px solid rgba(6,182,212,0.15) !important;
    backdrop-filter: blur(20px) !important;
}
section[data-testid="stSidebar"] * {
    color: #cbd5f0 !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] h1, h2, h3 {
    color: #a5b4fc !important;
}

/* ─── Glass Card Mixin ─────────────────────────────────────── */
.glass-card {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06) !important;
    padding: 1.8rem !important;
    margin-bottom: 1.2rem !important;
    transition: all 0.3s ease !important;
}
.glass-card:hover {
    border-color: rgba(6,182,212,0.25) !important;
    box-shadow: 0 12px 48px rgba(0,0,0,0.5), 0 0 30px rgba(6,182,212,0.06), inset 0 1px 0 rgba(255,255,255,0.08) !important;
    transform: translateY(-2px) !important;
}

/* ─── Metric Cards ─────────────────────────────────────────── */
.metric-card {
    background: linear-gradient(135deg, rgba(6,182,212,0.08) 0%, rgba(139,92,246,0.06) 100%);
    border: 1px solid rgba(6,182,212,0.2);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(6,182,212,0.8), transparent);
    animation: shimmer 3s ease-in-out infinite;
}
@keyframes shimmer {
    0%, 100% { opacity: 0.4; }
    50%       { opacity: 1; }
}
.metric-card:hover {
    border-color: rgba(6,182,212,0.5);
    box-shadow: 0 0 30px rgba(6,182,212,0.12);
    transform: translateY(-3px);
}
.metric-value {
    font-family: 'Outfit', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #22d3ee, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
}
.metric-label {
    color: rgba(165,180,252,0.7);
    font-size: 0.78rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 0.5rem;
}
.metric-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    display: block;
}

/* ─── Meal Cards ───────────────────────────────────────────── */
.meal-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-left: 3px solid;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin: 0.8rem 0;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}
.meal-card.breakfast { border-left-color: #f59e0b; }
.meal-card.snack1    { border-left-color: #10b981; }
.meal-card.lunch     { border-left-color: #06b6d4; }
.meal-card.snack2    { border-left-color: #8b5cf6; }
.meal-card.dinner    { border-left-color: #f43f5e; }
.meal-card.hydration { border-left-color: #3b82f6; }
.meal-card:hover {
    background: rgba(255,255,255,0.04);
    border-color: rgba(255,255,255,0.12);
    transform: translateX(4px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

/* ─── Hero Header ──────────────────────────────────────────── */
.hero-title {
    font-family: 'Outfit', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #22d3ee 0%, #a78bfa 50%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    color: rgba(165,180,252,0.65);
    font-size: 1rem;
    font-weight: 400;
    margin-top: 0.5rem;
    letter-spacing: 0.3px;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(6,182,212,0.1);
    border: 1px solid rgba(6,182,212,0.3);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #22d3ee;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

/* ─── Section Headers ──────────────────────────────────────── */
.section-header {
    font-family: 'Outfit', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #a5b4fc;
    text-transform: uppercase;
    letter-spacing: 2px;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(165,180,252,0.1);
}

/* ─── Primary Button ───────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #06b6d4, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.9rem 2.5rem !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 20px rgba(6,182,212,0.3), 0 0 40px rgba(124,58,237,0.2) !important;
    transition: all 0.3s ease !important;
    position: relative !important;
    overflow: hidden !important;
    width: 100% !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(6,182,212,0.45), 0 0 60px rgba(124,58,237,0.3) !important;
}
.stButton > button[kind="primary"]:active {
    transform: translateY(0) !important;
}

/* ─── Inputs ───────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e2eeff !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: rgba(6,182,212,0.5) !important;
    box-shadow: 0 0 0 3px rgba(6,182,212,0.1) !important;
}

/* ─── Expander ─────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 14px !important;
    color: #a5b4fc !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-top: none !important;
    border-radius: 0 0 14px 14px !important;
}

/* ─── Divider ──────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.06) !important;
    margin: 1.5rem 0 !important;
}

/* ─── Spinner ──────────────────────────────────────────────── */
.stSpinner > div {
    border-color: #06b6d4 !important;
}

/* ─── Status boxes ─────────────────────────────────────────── */
.stSuccess {
    background: rgba(16,185,129,0.08) !important;
    border: 1px solid rgba(16,185,129,0.25) !important;
    border-radius: 12px !important;
}
.stError {
    background: rgba(244,63,94,0.08) !important;
    border: 1px solid rgba(244,63,94,0.25) !important;
    border-radius: 12px !important;
}
.stWarning {
    background: rgba(245,158,11,0.08) !important;
    border: 1px solid rgba(245,158,11,0.25) !important;
    border-radius: 12px !important;
}

/* ─── Radio ────────────────────────────────────────────────── */
.stRadio > div {
    gap: 0.6rem !important;
}
.stRadio label {
    color: #cbd5f0 !important;
}

/* ─── File uploader ────────────────────────────────────────── */
.stFileUploader {
    background: rgba(255,255,255,0.02) !important;
    border: 2px dashed rgba(6,182,212,0.2) !important;
    border-radius: 14px !important;
    padding: 1rem !important;
    transition: all 0.3s ease !important;
}
.stFileUploader:hover {
    border-color: rgba(6,182,212,0.4) !important;
    background: rgba(6,182,212,0.03) !important;
}

/* ─── Scrollbar ────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(6,182,212,0.3); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(6,182,212,0.6); }

/* ─── Pulse animation ──────────────────────────────────────── */
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 20px rgba(6,182,212,0.1); }
    50%       { box-shadow: 0 0 40px rgba(6,182,212,0.25); }
}
.pulse-glow { animation: pulse-glow 3s ease-in-out infinite; }

/* ─── Diet plan results ────────────────────────────────────── */
.result-wrapper {
    background: rgba(5,10,20,0.8);
    border: 1px solid rgba(6,182,212,0.2);
    border-radius: 20px;
    padding: 2rem;
    margin-top: 2rem;
    backdrop-filter: blur(20px);
}
.result-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, #22d3ee, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 1.5rem;
}

/* ─── Macro pill tags ──────────────────────────────────────── */
.macro-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(6,182,212,0.1);
    border: 1px solid rgba(6,182,212,0.25);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #22d3ee;
    margin: 2px;
}
.macro-pill.protein { background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.25); color: #34d399; }
.macro-pill.carbs   { background: rgba(245,158,11,0.1); border-color: rgba(245,158,11,0.25); color: #fbbf24; }
.macro-pill.fat     { background: rgba(244,63,94,0.1);  border-color: rgba(244,63,94,0.25);  color: #fb7185; }

/* Hide streamlit default footer/branding */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ===== 3. API KEY CHECK =====
if not api_key:
    st.markdown("""
    <div style="background:rgba(244,63,94,0.1);border:1px solid rgba(244,63,94,0.3);border-radius:16px;padding:2rem;text-align:center;margin-top:4rem">
        <div style="font-size:3rem;margin-bottom:1rem">🔑</div>
        <div style="font-family:Outfit,sans-serif;font-size:1.5rem;font-weight:700;color:#fb7185;margin-bottom:0.8rem">
            OpenRouter API Key Missing
        </div>
        <div style="color:rgba(203,213,240,0.7);font-size:0.95rem;line-height:1.7">
            <b>Local:</b> Create a <code>.env</code> file with:<br>
            <code style="background:rgba(255,255,255,0.05);padding:4px 12px;border-radius:6px;display:inline-block;margin:0.5rem 0">OPENROUTER_API_KEY=your_key_here</code><br><br>
            <b>Cloud (Hugging Face / Streamlit):</b> Add to secrets:<br>
            <code style="background:rgba(255,255,255,0.05);padding:4px 12px;border-radius:6px;display:inline-block;margin:0.5rem 0">OPENROUTER_API_KEY = "your_key_here"</code>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ===== 4. OPENROUTER CLIENT =====
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

# ===== 5. FETCH AVAILABLE FREE MODELS =====
@st.cache_data(ttl=3600)
def fetch_free_models():
    """Fetch available free models from OpenRouter API."""
    # Curated list of high-quality free models (as of Sept 2026)
    curated_free_models = [
        ("google/gemma-4-31b-it:free",                      "🟢 Google: Gemma 4 31B"),
        ("google/gemma-4-26b-a4b-it:free",                  "🟢 Google: Gemma 4 26B"),
        ("nvidia/nemotron-3-ultra-550b-a55b:free",           "⚡ NVIDIA: Nemotron 3 Ultra 550B"),
        ("nvidia/nemotron-3-super-120b-a12b:free",           "⚡ NVIDIA: Nemotron 3 Super 120B"),
        ("nvidia/nemotron-3.5-lightning:free",               "⚡ NVIDIA: Nemotron 3.5 Lightning"),
        ("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free","⚡ NVIDIA: Nemotron 3 Nano Omni"),
        ("thinkingmachines/inkling:free",                    "🔵 Thinking Machines: Inkling"),
        ("liquid/lfm-2.5-2.6b:free",                        "💧 LiquidAI: LFM 2.5 (Fast)"),
    ]
    # Try to validate via API, fall back to curated list
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5
        )
        if resp.status_code == 200:
            all_models = resp.json().get("data", [])
            live_free_ids = {
                m["id"] for m in all_models
                if float(m.get("pricing", {}).get("prompt", 1)) == 0
            }
            validated = [(mid, name) for mid, name in curated_free_models if mid in live_free_ids]
            # Add any extra live free models not in curated list
            extra = [
                (m["id"], f"🌐 {m['name']}")
                for m in all_models
                if float(m.get("pricing", {}).get("prompt", 1)) == 0
                and ":free" in m["id"]
                and m["id"] not in {mid for mid, _ in curated_free_models}
            ]
            return validated + extra[:5] if validated else curated_free_models
    except Exception:
        pass
    return curated_free_models

free_models = fetch_free_models()
model_display_names = [name for _, name in free_models]
model_ids = [mid for mid, _ in free_models]

# ===== 6. ML MODEL LOADING =====
@st.cache_resource
def load_ml_model():
    model_path = Path(__file__).resolve().parents[1] / "models" / "nutrition_regressor.pkl"
    try:
        return joblib.load(str(model_path))
    except Exception as e:
        st.error(f"❌ Could not load ML model: {e}")
        st.stop()

ml_model = load_ml_model()


# ===== 7. SIDEBAR =====
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1.2rem 0 0.5rem">
        <div style="font-size:3rem;margin-bottom:0.5rem">🥗</div>
        <div style="font-family:Outfit,sans-serif;font-size:1.1rem;font-weight:700;
                    background:linear-gradient(135deg,#22d3ee,#a78bfa);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text">AI Nutritionist Pro</div>
        <div style="color:rgba(165,180,252,0.5);font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;margin-top:4px">
            Powered by OpenRouter
        </div>
    </div>
    <hr style="border-top:1px solid rgba(165,180,252,0.1);margin:1rem 0">
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">🤖 AI Model</div>', unsafe_allow_html=True)

    selected_idx = st.selectbox(
        "Choose Free Model",
        range(len(model_display_names)),
        format_func=lambda i: model_display_names[i],
        key="model_selector"
    )
    selected_model = model_ids[selected_idx]

    st.markdown(f"""
    <div style="background:rgba(6,182,212,0.06);border:1px solid rgba(6,182,212,0.15);
                border-radius:10px;padding:0.8rem;margin:0.8rem 0;font-size:0.75rem;color:rgba(165,180,252,0.6)">
        <b style="color:#22d3ee">Free tier</b> — No cost, no rate limit warnings.<br>
        Model: <code style="color:#a78bfa;font-size:0.7rem">{selected_model}</code>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="border-top:1px solid rgba(165,180,252,0.1)">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">💬 Quick Chat</div>', unsafe_allow_html=True)

    user_question = st.text_input(
        "Ask a nutrition question",
        placeholder="e.g. What foods boost metabolism?",
        key="quick_chat_input"
    )

    if user_question:
        with st.spinner("Thinking..."):
            try:
                qr = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are a concise, expert nutritionist. Answer briefly and practically."},
                        {"role": "user", "content": user_question}
                    ],
                    max_tokens=400,
                    temperature=0.6
                )
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
                            border-radius:12px;padding:1rem;margin-top:0.5rem;font-size:0.85rem;
                            color:#cbd5f0;line-height:1.6">
                    {qr.choices[0].message.content}
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ {e}")

    st.markdown('<hr style="border-top:1px solid rgba(165,180,252,0.1)">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📄 Health Data</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload health report (optional)", type=["csv", "pdf"])
    if uploaded_file:
        st.success(f"✅ Uploaded: {uploaded_file.name}")


# ===== 8. HERO HEADER =====
st.markdown("""
<div style="padding:2rem 0 1.5rem">
    <div class="hero-badge">✨ AI-Powered Nutrition Intelligence</div>
    <div class="hero-title">Your Personal AI Nutritionist</div>
    <div class="hero-subtitle">
        Scientifically-optimized meal plans tailored to your biology — powered by cutting-edge free AI models.
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Feature cards row ───
col1, col2, col3, col4 = st.columns(4)
feature_cards = [
    ("🧬", "Personalized", "Based on your unique biology"),
    ("🤖", "AI-Powered",   "Latest free OpenRouter models"),
    ("🥘", "Indian Meals", "Budget-friendly local ingredients"),
    ("📊", "Macro-tracked", "Calories, protein, carbs & fat"),
]
for col, (icon, title, desc) in zip([col1, col2, col3, col4], feature_cards):
    with col:
        st.markdown(f"""
        <div class="metric-card" style="padding:1.2rem;margin-bottom:1rem">
            <span class="metric-icon">{icon}</span>
            <div style="font-family:Outfit,sans-serif;font-size:0.95rem;font-weight:600;
                        color:#a5b4fc;margin-bottom:4px">{title}</div>
            <div style="font-size:0.75rem;color:rgba(165,180,252,0.55)">{desc}</div>
        </div>
        """, unsafe_allow_html=True)


# ===== 9. HEALTH PROFILE =====
st.markdown('<div class="section-header" style="margin-top:1rem">🧑‍⚕️ Your Health Profile</div>', unsafe_allow_html=True)
st.markdown('<div class="glass-card pulse-glow">', unsafe_allow_html=True)

with st.expander("", expanded=True):
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        gender = st.selectbox("⚧ Gender", ["Male", "Female", "Other"], key="gender")
    with r1c2:
        age = st.number_input("🎂 Age", 5, 100, 25, key="age")
    with r1c3:
        goal = st.selectbox("🎯 Goal", ["Weight Loss", "Weight Gain", "Weight Maintenance"], key="goal")

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        height_unit = st.radio("Height Unit", ["cm", "m", "ft"], index=0, horizontal=True, key="h_unit")
        height = st.number_input(f"📏 Height ({height_unit})", min_value=0.0, value=170.0, key="height")
    with r2c2:
        weight_unit = st.radio("Weight Unit", ["kg", "lbs"], index=0, horizontal=True, key="w_unit")
        weight = st.number_input(f"⚖️ Weight ({weight_unit})", min_value=0.0, value=70.0, key="weight")

    activity = st.select_slider(
        "🏃 Activity Level",
        options=["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
        value="Moderately Active",
        key="activity"
    )

    dietary = st.multiselect(
        "🌿 Dietary Preferences (optional)",
        ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Low-Carb", "High-Protein", "Diabetic-Friendly"],
        key="dietary"
    )

st.markdown('</div>', unsafe_allow_html=True)


# ===== 10. LIVE BMI & METRIC CARDS =====
height_m = height / 100 if height_unit == "cm" else (height * 0.3048 if height_unit == "ft" else height)
weight_kg = weight * 0.453592 if weight_unit == "lbs" else weight
bmi = round(weight_kg / (height_m ** 2), 2) if height_m > 0 else 0

# BMI category
if bmi < 18.5:
    bmi_cat, bmi_color = "Underweight", "#f59e0b"
elif bmi < 25:
    bmi_cat, bmi_color = "Normal", "#10b981"
elif bmi < 30:
    bmi_cat, bmi_color = "Overweight", "#f59e0b"
else:
    bmi_cat, bmi_color = "Obese", "#f43f5e"

# Activity multipliers for estimated TDEE
activity_factors = {
    "Sedentary": 1.2, "Lightly Active": 1.375,
    "Moderately Active": 1.55, "Very Active": 1.725, "Extremely Active": 1.9
}
# Harris-Benedict BMR
if gender == "Male":
    bmr = 88.36 + (13.4 * weight_kg) + (4.8 * height_m * 100) - (5.7 * age)
else:
    bmr = 447.6 + (9.2 * weight_kg) + (3.1 * height_m * 100) - (4.3 * age)

tdee = round(bmr * activity_factors.get(activity, 1.55))

m1, m2, m3, m4 = st.columns(4)
metrics = [
    (m1, "⚖️", f"{bmi}", f"BMI • {bmi_cat}"),
    (m2, "🔥", f"{tdee}", "Est. Daily Calories"),
    (m3, "📏", f"{height_m:.2f}m", "Height"),
    (m4, "💪", f"{weight_kg:.1f}kg", "Weight"),
]
for col, icon, val, label in metrics:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <span class="metric-icon">{icon}</span>
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)


# ===== 11. GENERATE DIET PLAN BUTTON =====
st.markdown("<br>", unsafe_allow_html=True)

if st.button("✨ Generate My Personalized Diet Plan", type="primary", key="generate_btn"):
    with st.spinner("🧬 Analyzing your biological profile..."):
        try:
            # Get model features
            try:
                expected_features = ml_model.feature_names_in_
            except AttributeError:
                try:
                    expected_features = ml_model.get_booster().feature_names
                except AttributeError:
                    st.error("❌ Could not determine model's expected features")
                    st.stop()

            # Build input dict
            input_dict = {
                'Age': age,
                'Height_cm': height_m * 100,
                'Weight_kg': weight_kg,
                'BMI': bmi,
                'Gender_Male':   1 if gender == "Male"   else 0,
                'Gender_Female': 1 if gender == "Female" else 0,
                'Gender_Other':  1 if gender == "Other"  else 0,
            }
            for feature in expected_features:
                if feature not in input_dict:
                    input_dict[feature] = 0

            input_df = pd.DataFrame([input_dict])[expected_features]
            prediction = ml_model.predict(input_df)

            if len(prediction[0]) != 4:
                st.error(f"❌ Unexpected prediction format. Got {len(prediction[0])} outputs, expected 4.")
                st.stop()

            calories, protein, carbs, fat = prediction[0]

            # Show macro pills
            st.markdown(f"""
            <div style="margin:1.5rem 0;display:flex;flex-wrap:wrap;gap:8px;align-items:center">
                <span style="color:rgba(165,180,252,0.6);font-size:0.85rem;font-weight:600">
                    ML-Predicted Macros:
                </span>
                <span class="macro-pill">🔥 {calories:.0f} kcal</span>
                <span class="macro-pill protein">💪 {protein:.0f}g Protein</span>
                <span class="macro-pill carbs">🌾 {carbs:.0f}g Carbs</span>
                <span class="macro-pill fat">🫧 {fat:.0f}g Fat</span>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"⚠️ Nutrition calculation error: {e}")
            # Fallback to TDEE-based estimates
            calories = tdee
            protein = round(weight_kg * 1.8)
            fat = round(calories * 0.25 / 9)
            carbs = round((calories - protein * 4 - fat * 9) / 4)
            st.info(f"ℹ️ Using TDEE-based estimates: {calories:.0f} kcal | {protein}g P | {carbs}g C | {fat}g F")

    dietary_note = f"Dietary preferences: {', '.join(dietary)}." if dietary else "No specific dietary restrictions."

    with st.spinner("🍽️ Crafting your personalized Indian meal plan..."):
        try:
            response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Indian nutritionist creating beautifully detailed meal plans.
Format your response using clean Markdown with emoji section headers.
Include for EACH meal:
- Exact portion sizes in grams/ml
- Key nutritional values
- Simple preparation notes
- Budget-friendly, easily available Indian ingredients
Use this exact structure with these section headers:
## 🌅 Breakfast
## 🍎 Mid-Morning Snack  
## ☀️ Lunch
## 🫖 Evening Snack
## 🌙 Dinner
## 💧 Hydration & Tips"""
                    },
                    {
                        "role": "user",
                        "content": f"""Create a detailed {goal.lower()} meal plan for:
- Age: {age} | Gender: {gender} | BMI: {bmi} ({bmi_cat})
- Activity: {activity}
- Daily Targets: {calories:.0f} kcal | {protein:.0f}g protein | {carbs:.0f}g carbs | {fat:.0f}g fat
- {dietary_note}

Make it practical, delicious, and achievable for an Indian lifestyle."""
                    }
                ],
                temperature=0.72,
                max_tokens=3500
            )

            plan_text = response.choices[0].message.content

            # ─── Results Display ───
            st.markdown(f"""
            <div class="result-wrapper">
                <div class="result-title">🍽️ Your Personalized Diet Plan</div>
                <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:1.5rem">
                    <span class="macro-pill">👤 {age}y {gender}</span>
                    <span class="macro-pill">🎯 {goal}</span>
                    <span class="macro-pill">🏃 {activity}</span>
                    <span class="macro-pill">⚖️ BMI {bmi} — {bmi_cat}</span>
                </div>
            """, unsafe_allow_html=True)

            # Split plan into meal sections and display as cards
            sections = {
                "🌅 Breakfast":           ("breakfast", "☀️ Breakfast"),
                "🍎 Mid-Morning Snack":   ("snack1",    "🍎 Mid-Morning Snack"),
                "☀️ Lunch":               ("lunch",     "🌞 Lunch"),
                "🫖 Evening Snack":       ("snack2",    "🫖 Evening Snack"),
                "🌙 Dinner":              ("dinner",    "🌙 Dinner"),
                "💧 Hydration & Tips":    ("hydration", "💧 Hydration & Tips"),
            }

            import re
            parts = re.split(r'\n(?=##\s)', plan_text)

            if len(parts) > 1:
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    # Find which card class to use
                    card_class = "lunch"  # default
                    for section_header, (css_class, _) in sections.items():
                        if any(kw in part[:40] for kw in section_header.split()):
                            card_class = css_class
                            break
                    st.markdown(f'<div class="meal-card {card_class}">', unsafe_allow_html=True)
                    st.markdown(part)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Fallback: render full plan in one card
                st.markdown(plan_text)

            st.markdown("</div>", unsafe_allow_html=True)

            # Download button
            st.download_button(
                label="⬇️ Download My Diet Plan",
                data=f"AI Nutritionist Pro — Diet Plan\n{'='*50}\n\n{plan_text}",
                file_name="my_diet_plan.txt",
                mime="text/plain",
                key="download_plan"
            )
            st.balloons()

        except Exception as e:
            st.markdown(f"""
            <div style="background:rgba(244,63,94,0.08);border:1px solid rgba(244,63,94,0.25);
                        border-radius:14px;padding:1.5rem;margin-top:1rem">
                <div style="font-family:Outfit,sans-serif;font-size:1rem;font-weight:600;color:#fb7185;margin-bottom:0.5rem">
                    🚨 Error generating meal plan
                </div>
                <div style="color:rgba(203,213,240,0.7);font-size:0.85rem">
                    {str(e)}<br><br>
                    <b>Try:</b><br>
                    • Selecting a different model<br>
                    • Checking your OpenRouter API key<br>
                    • Verifying your OpenRouter account credits
                </div>
            </div>
            """, unsafe_allow_html=True)


# ===== 12. FOOTER =====
st.markdown("""
<div style="margin-top:4rem;padding:2rem 0;text-align:center;
            border-top:1px solid rgba(255,255,255,0.05)">
    <div style="color:rgba(165,180,252,0.4);font-size:0.75rem;letter-spacing:1px">
        Built with ❤️ using Streamlit • Powered by OpenRouter Free Models
        <br>
        <span style="color:rgba(165,180,252,0.25)">🔒 API keys stored securely — never exposed in code</span>
    </div>
</div>
""", unsafe_allow_html=True)
