import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import joblib
import pandas as pd
import os
import requests

# ===== 1. ENVIRONMENT CONFIG =====
def get_api_key():
    env_path = Path(__file__).resolve().parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    return os.getenv("OPENROUTER_API_KEY")

api_key = get_api_key()

# ===== 2. OPENROUTER CLIENT =====
client = OpenAI(
    api_key=api_key or "missing",
    base_url="https://openrouter.ai/api/v1"
) if api_key else None

# ===== 3. FETCH FREE MODELS =====
CURATED_FREE_MODELS = [
    ("google/gemma-4-31b-it:free",                       "🟢 Google: Gemma 4 31B"),
    ("google/gemma-4-26b-a4b-it:free",                   "🟢 Google: Gemma 4 26B"),
    ("nvidia/nemotron-3-ultra-550b-a55b:free",            "⚡ NVIDIA: Nemotron 3 Ultra 550B"),
    ("nvidia/nemotron-3-super-120b-a12b:free",            "⚡ NVIDIA: Nemotron 3 Super 120B"),
    ("nvidia/nemotron-3.5-lightning:free",                "⚡ NVIDIA: Nemotron 3.5 Lightning"),
    ("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free","⚡ NVIDIA: Nemotron 3 Nano Omni"),
    ("thinkingmachines/inkling:free",                     "🔵 Thinking Machines: Inkling"),
    ("liquid/lfm-2.5-2.6b:free",                         "💧 LiquidAI: LFM 2.5 (Fast)"),
]

def fetch_free_model_ids():
    if api_key:
        try:
            resp = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )
            if resp.status_code == 200:
                all_models = resp.json().get("data", [])
                live_ids = {m["id"] for m in all_models if float(m.get("pricing",{}).get("prompt",1)) == 0}
                validated = [name for mid, name in CURATED_FREE_MODELS if mid in live_ids]
                return validated if validated else [name for _, name in CURATED_FREE_MODELS]
        except Exception:
            pass
    return [name for _, name in CURATED_FREE_MODELS]

MODEL_NAMES = fetch_free_model_ids()
MODEL_MAP = {name: mid for mid, name in CURATED_FREE_MODELS}

# ===== 4. ML MODEL =====
def load_ml_model():
    paths = [
        Path(__file__).resolve().parent / "models" / "nutrition_regressor.pkl",
        Path(__file__).resolve().parents[1] / "models" / "nutrition_regressor.pkl",
    ]
    for p in paths:
        if p.exists():
            return joblib.load(str(p))
    return None

ml_model = load_ml_model()


# ===== 5. CORE LOGIC =====
def compute_metrics(gender, age, height_unit, height, weight_unit, weight, activity):
    height_m = height/100 if height_unit == "cm" else (height*0.3048 if height_unit == "ft" else height)
    weight_kg = weight * 0.453592 if weight_unit == "lbs" else weight
    bmi = round(weight_kg / (height_m**2), 2) if height_m > 0 else 0

    if bmi < 18.5:  bmi_cat, bmi_clr = "Underweight", "#f59e0b"
    elif bmi < 25:  bmi_cat, bmi_clr = "Normal",      "#10b981"
    elif bmi < 30:  bmi_cat, bmi_clr = "Overweight",  "#f59e0b"
    else:           bmi_cat, bmi_clr = "Obese",       "#f43f5e"

    activity_factors = {
        "Sedentary": 1.2, "Lightly Active": 1.375,
        "Moderately Active": 1.55, "Very Active": 1.725, "Extremely Active": 1.9
    }
    if gender == "Male":
        bmr = 88.36 + (13.4*weight_kg) + (4.8*height_m*100) - (5.7*age)
    else:
        bmr = 447.6 + (9.2*weight_kg) + (3.1*height_m*100) - (4.3*age)
    tdee = round(bmr * activity_factors.get(activity, 1.55))

    return height_m, weight_kg, bmi, bmi_cat, bmi_clr, tdee


def generate_diet_plan(gender, age, goal, height_unit, height, weight_unit, weight, activity, dietary_str, model_name):
    if not api_key:
        return "❌ **OpenRouter API key not configured.** Add `OPENROUTER_API_KEY` to your `.env` file or Hugging Face Space secrets.", "", ""

    height_m, weight_kg, bmi, bmi_cat, bmi_clr, tdee = compute_metrics(
        gender, age, height_unit, height, weight_unit, weight, activity
    )
    dietary = [d.strip() for d in dietary_str.split(",") if d.strip()] if dietary_str else []
    dietary_note = f"Dietary preferences: {', '.join(dietary)}." if dietary else "No specific dietary restrictions."

    # ── ML Prediction ──
    calories, protein, carbs, fat = tdee, round(weight_kg*1.8), 0, 0
    fat = round(calories * 0.25 / 9)
    carbs = round((calories - protein*4 - fat*9) / 4)
    ml_note = "📊 *Macros estimated using Harris-Benedict formula.*"

    if ml_model:
        try:
            try:    expected_features = ml_model.feature_names_in_
            except: expected_features = ml_model.get_booster().feature_names
            inp = {
                'Age': age, 'Height_cm': height_m*100, 'Weight_kg': weight_kg, 'BMI': bmi,
                'Gender_Male': 1 if gender=="Male" else 0,
                'Gender_Female': 1 if gender=="Female" else 0,
                'Gender_Other': 1 if gender=="Other" else 0,
            }
            for f in expected_features:
                if f not in inp: inp[f] = 0
            pred = ml_model.predict(pd.DataFrame([inp])[expected_features])
            if len(pred[0]) == 4:
                calories, protein, carbs, fat = pred[0]
                ml_note = "🤖 *Macros predicted by ML model (XGBoost).*"
        except Exception as e:
            ml_note = f"⚠️ ML model error ({e}) — using formula fallback."

    # ── LLM Call ──
    selected_model = MODEL_MAP.get(model_name, "google/gemma-4-31b-it:free")
    try:
        resp = client.chat.completions.create(
            model=selected_model,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert Indian nutritionist. Format each section with emoji headers exactly as:
## 🌅 Breakfast
## 🍎 Mid-Morning Snack
## ☀️ Lunch
## 🫖 Evening Snack
## 🌙 Dinner
## 💧 Hydration & Tips
Include exact portion sizes, key nutrients, and simple prep notes. Use budget-friendly Indian ingredients."""
                },
                {
                    "role": "user",
                    "content": f"""Create a detailed {goal.lower()} meal plan for:
- Age: {age} | Gender: {gender} | BMI: {bmi} ({bmi_cat}) | Activity: {activity}
- Daily Targets: {calories:.0f} kcal | {protein:.0f}g protein | {carbs:.0f}g carbs | {fat:.0f}g fat
- {dietary_note}
Make it practical and achievable for an Indian lifestyle."""
                }
            ],
            temperature=0.72,
            max_tokens=3500
        )
        plan = resp.choices[0].message.content
    except Exception as e:
        plan = f"❌ LLM error: {e}\n\nTry selecting a different model."

    # ── Metrics HTML ──
    metrics_html = f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0">
  <div style="background:linear-gradient(135deg,rgba(6,182,212,.12),rgba(139,92,246,.08));border:1px solid rgba(6,182,212,.25);border-radius:14px;padding:16px;text-align:center">
    <div style="font-size:1.6rem;font-weight:700;background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{bmi}</div>
    <div style="color:#a5b4fc;font-size:.7rem;text-transform:uppercase;letter-spacing:1.5px;margin-top:6px">⚖️ BMI • {bmi_cat}</div>
  </div>
  <div style="background:linear-gradient(135deg,rgba(6,182,212,.12),rgba(139,92,246,.08));border:1px solid rgba(6,182,212,.25);border-radius:14px;padding:16px;text-align:center">
    <div style="font-size:1.6rem;font-weight:700;background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{tdee}</div>
    <div style="color:#a5b4fc;font-size:.7rem;text-transform:uppercase;letter-spacing:1.5px;margin-top:6px">🔥 Daily Calories</div>
  </div>
  <div style="background:linear-gradient(135deg,rgba(6,182,212,.12),rgba(139,92,246,.08));border:1px solid rgba(6,182,212,.25);border-radius:14px;padding:16px;text-align:center">
    <div style="font-size:1.6rem;font-weight:700;background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{weight_kg:.1f}kg</div>
    <div style="color:#a5b4fc;font-size:.7rem;text-transform:uppercase;letter-spacing:1.5px;margin-top:6px">💪 Weight</div>
  </div>
  <div style="background:linear-gradient(135deg,rgba(6,182,212,.12),rgba(139,92,246,.08));border:1px solid rgba(6,182,212,.25);border-radius:14px;padding:16px;text-align:center">
    <div style="font-size:1.6rem;font-weight:700;background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{height_m:.2f}m</div>
    <div style="color:#a5b4fc;font-size:.7rem;text-transform:uppercase;letter-spacing:1.5px;margin-top:6px">📏 Height</div>
  </div>
</div>
<div style="display:flex;flex-wrap:wrap;gap:8px;padding:12px 0">
  <span style="background:rgba(6,182,212,.1);border:1px solid rgba(6,182,212,.3);border-radius:20px;padding:4px 14px;font-size:.78rem;font-weight:600;color:#22d3ee">🔥 {calories:.0f} kcal</span>
  <span style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);border-radius:20px;padding:4px 14px;font-size:.78rem;font-weight:600;color:#34d399">💪 {protein:.0f}g Protein</span>
  <span style="background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);border-radius:20px;padding:4px 14px;font-size:.78rem;font-weight:600;color:#fbbf24">🌾 {carbs:.0f}g Carbs</span>
  <span style="background:rgba(244,63,94,.1);border:1px solid rgba(244,63,94,.3);border-radius:20px;padding:4px 14px;font-size:.78rem;font-weight:600;color:#fb7185">🫧 {fat:.0f}g Fat</span>
</div>
<div style="color:rgba(165,180,252,.55);font-size:.75rem;margin-top:4px">{ml_note}</div>
"""
    return plan, metrics_html, f"my_diet_plan_{goal.lower().replace(' ','_')}.txt"


def quick_chat(question, model_name):
    if not api_key:
        return "❌ API key not configured."
    if not question.strip():
        return ""
    selected_model = MODEL_MAP.get(model_name, "google/gemma-4-31b-it:free")
    try:
        resp = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": "You are a concise expert nutritionist. Answer briefly and practically."},
                {"role": "user", "content": question}
            ],
            max_tokens=400,
            temperature=0.6
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"


# ===== 6. CUSTOM CSS =====
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; }

body, .gradio-container {
    background: radial-gradient(ellipse at 20% 10%, rgba(6,182,212,.07) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(139,92,246,.07) 0%, transparent 50%),
                linear-gradient(135deg, #050a14 0%, #0a0f24 50%, #060b18 100%) !important;
    font-family: 'Inter', sans-serif !important;
    color: #e2eeff !important;
    min-height: 100vh;
}

/* Hero */
.hero-section {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    position: relative;
}
.hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(6,182,212,.1); border: 1px solid rgba(6,182,212,.3);
    border-radius: 20px; padding: 5px 16px;
    font-size: .73rem; font-weight: 600; color: #22d3ee;
    letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 1rem;
}
.hero-title {
    font-family: 'Outfit', sans-serif; font-size: 2.8rem; font-weight: 800;
    background: linear-gradient(135deg, #22d3ee 0%, #a78bfa 50%, #34d399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1.1; letter-spacing: -.5px;
    margin: .5rem 0;
}
.hero-sub {
    color: rgba(165,180,252,.6); font-size: .95rem;
    max-width: 500px; margin: .5rem auto 0;
}

/* Feature cards */
.feat-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
    max-width: 860px; margin: 1.8rem auto 0;
}
.feat-card {
    background: linear-gradient(135deg, rgba(6,182,212,.08), rgba(139,92,246,.06));
    border: 1px solid rgba(6,182,212,.2); border-radius: 14px;
    padding: 1.1rem; text-align: center;
    transition: all .3s ease; position: relative; overflow: hidden;
}
.feat-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, rgba(6,182,212,.8), transparent);
    animation: shimmer 3s ease-in-out infinite;
}
@keyframes shimmer { 0%,100%{opacity:.4} 50%{opacity:1} }
.feat-card:hover { border-color: rgba(6,182,212,.5); transform: translateY(-3px); }
.feat-icon { font-size: 1.5rem; margin-bottom: .4rem; }
.feat-title { font-family:'Outfit',sans-serif; font-size:.88rem; font-weight:600; color:#a5b4fc; }
.feat-desc  { font-size:.72rem; color:rgba(165,180,252,.5); margin-top:3px; }

/* Glass panel */
.glass-panel {
    background: rgba(255,255,255,.025) !important;
    border: 1px solid rgba(255,255,255,.08) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(20px) !important;
    padding: 1.8rem !important;
    margin-bottom: 1.2rem !important;
    transition: all .3s ease;
}
.glass-panel:hover {
    border-color: rgba(6,182,212,.2) !important;
}

/* Section headers */
.section-hdr {
    font-family: 'Outfit', sans-serif; font-size: 1rem; font-weight: 600;
    color: #a5b4fc; text-transform: uppercase; letter-spacing: 2px;
    padding-bottom: .6rem; border-bottom: 1px solid rgba(165,180,252,.1);
    margin-bottom: 1rem; display: flex; align-items: center; gap: 8px;
}

/* Gradio overrides */
.gradio-container .block { background: transparent !important; border: none !important; padding: 0 !important; }
label.svelte-1b6s6vi { color: #a5b4fc !important; font-size: .82rem !important; font-weight: 500 !important; letter-spacing: .5px !important; }

input[type=text], input[type=number], textarea, select,
.svelte-1b6s6vi input, .svelte-pbm1f8 {
    background: rgba(255,255,255,.04) !important;
    border: 1px solid rgba(255,255,255,.1) !important;
    border-radius: 10px !important;
    color: #e2eeff !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color .2s;
}
input:focus, textarea:focus {
    border-color: rgba(6,182,212,.5) !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(6,182,212,.08) !important;
}

/* Primary button */
button.primary, .gr-button-primary, button[variant=primary] {
    background: linear-gradient(135deg, #06b6d4, #7c3aed) !important;
    color: #fff !important; border: none !important;
    border-radius: 14px !important; font-family: 'Outfit', sans-serif !important;
    font-size: .95rem !important; font-weight: 600 !important;
    padding: .85rem 2rem !important; letter-spacing: .5px !important;
    box-shadow: 0 4px 20px rgba(6,182,212,.3), 0 0 40px rgba(124,58,237,.15) !important;
    transition: all .3s ease !important;
}
button.primary:hover, .gr-button-primary:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 30px rgba(6,182,212,.45) !important; }

/* Markdown output */
.output-markdown { color: #cbd5f0 !important; line-height: 1.7 !important; }
.output-markdown h2 {
    font-family:'Outfit',sans-serif; font-size:1.05rem; font-weight:700;
    background:linear-gradient(135deg,#22d3ee,#a78bfa);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    border-bottom:1px solid rgba(6,182,212,.15); padding-bottom:.4rem; margin:1.2rem 0 .6rem;
}
.output-markdown li { color: rgba(203,213,240,.85); margin: .25rem 0; }
.output-markdown strong { color: #a5b4fc !important; }
.output-markdown code {
    background: rgba(6,182,212,.1); border: 1px solid rgba(6,182,212,.2);
    border-radius: 4px; padding: 1px 6px; color: #22d3ee; font-size: .82rem;
}

/* Tabs */
.tab-nav { border-bottom: 1px solid rgba(255,255,255,.06) !important; }
.tab-nav button { color: rgba(165,180,252,.6) !important; border-radius:8px 8px 0 0 !important; }
.tab-nav button.selected { color:#22d3ee !important; border-bottom:2px solid #22d3ee !important; background:rgba(6,182,212,.06) !important; }

/* Accordion */
details summary { color: #a5b4fc !important; font-weight: 600 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(6,182,212,.3); border-radius: 4px; }

/* Footer */
.footer-bar {
    text-align: center; padding: 2rem 0; margin-top: 2rem;
    border-top: 1px solid rgba(255,255,255,.05);
    color: rgba(165,180,252,.35); font-size: .73rem; letter-spacing: .5px;
}

/* No API key warning */
.api-warn {
    background: rgba(244,63,94,.08); border: 1px solid rgba(244,63,94,.25);
    border-radius: 16px; padding: 1.5rem; text-align: center; margin: 2rem 0;
    color: #fb7185;
}

@media (max-width: 600px) {
    .hero-title { font-size: 1.8rem; }
    .feat-grid  { grid-template-columns: repeat(2, 1fr); }
}
"""


# ===== 7. GRADIO APP =====
with gr.Blocks(title="AI Nutritionist Pro") as demo:

    # ── Hero Header ──
    gr.HTML("""
    <div class="hero-section">
        <div class="hero-badge">✨ AI-Powered Nutrition Intelligence</div>
        <div class="hero-title">Your Personal AI Nutritionist</div>
        <div class="hero-sub">Scientifically-optimized meal plans tailored to your biology — powered by free OpenRouter AI models</div>
        <div class="feat-grid">
            <div class="feat-card"><div class="feat-icon">🧬</div><div class="feat-title">Personalized</div><div class="feat-desc">Based on your unique biology</div></div>
            <div class="feat-card"><div class="feat-icon">🤖</div><div class="feat-title">AI-Powered</div><div class="feat-desc">Latest free OpenRouter models</div></div>
            <div class="feat-card"><div class="feat-icon">🥘</div><div class="feat-title">Indian Meals</div><div class="feat-desc">Budget-friendly local ingredients</div></div>
            <div class="feat-card"><div class="feat-icon">📊</div><div class="feat-title">Macro-tracked</div><div class="feat-desc">Calories, protein, carbs & fat</div></div>
        </div>
    </div>
    """)

    with gr.Row():
        # ══ LEFT COLUMN — Inputs ══
        with gr.Column(scale=2, elem_classes="glass-panel"):
            gr.HTML('<div class="section-hdr">🤖 AI Model Selection</div>')
            model_choice = gr.Dropdown(
                choices=MODEL_NAMES,
                value=MODEL_NAMES[0] if MODEL_NAMES else None,
                label="Choose Free AI Model",
                info="All models are free via OpenRouter — no cost to you",
                interactive=True
            )

            gr.HTML('<div class="section-hdr" style="margin-top:1.4rem">🧑‍⚕️ Your Health Profile</div>')

            with gr.Row():
                gender = gr.Dropdown(["Male", "Female", "Other"], value="Male", label="⚧ Gender")
                age    = gr.Number(value=25, minimum=5, maximum=100, label="🎂 Age")
                goal   = gr.Dropdown(
                    ["Weight Loss", "Weight Gain", "Weight Maintenance"],
                    value="Weight Loss", label="🎯 Goal"
                )

            with gr.Row():
                height_unit = gr.Radio(["cm", "m", "ft"], value="cm", label="Height Unit")
                height      = gr.Number(value=170.0, minimum=1.0, label="📏 Height")
            with gr.Row():
                weight_unit = gr.Radio(["kg", "lbs"], value="kg", label="Weight Unit")
                weight      = gr.Number(value=70.0, minimum=1.0, label="⚖️ Weight")

            activity = gr.Dropdown(
                ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
                value="Moderately Active", label="🏃 Activity Level"
            )

            dietary = gr.Textbox(
                label="🌿 Dietary Preferences (optional — comma separated)",
                placeholder="e.g. Vegetarian, Gluten-Free, Diabetic-Friendly",
                lines=1
            )

            gen_btn = gr.Button("✨ Generate My Personalized Diet Plan", variant="primary", size="lg")

        # ══ RIGHT COLUMN — Quick Chat ══
        with gr.Column(scale=1, elem_classes="glass-panel"):
            gr.HTML('<div class="section-hdr">💬 Quick Nutrition Chat</div>')
            chat_q  = gr.Textbox(
                label="Ask a nutrition question",
                placeholder="e.g. What foods boost metabolism?",
                lines=2
            )
            chat_btn = gr.Button("Ask AI 🚀", size="sm")
            chat_out = gr.Markdown(label="", elem_classes="output-markdown")
            gr.HTML('<div style="color:rgba(165,180,252,.35);font-size:.72rem;margin-top:.5rem">Powered by the selected free AI model above</div>')

            gr.HTML('<div class="section-hdr" style="margin-top:1.5rem">📄 Upload Health Data</div>')
            upload = gr.File(
                label="Upload health report (optional)",
                file_types=[".csv", ".pdf"],
                type="filepath"
            )
            upload_note = gr.Markdown(visible=False)

    # ── Metrics Row ──
    with gr.Row():
        metrics_html = gr.HTML(label="Health Metrics")

    # ── Diet Plan Output ──
    gr.HTML('<div class="section-hdr" style="margin-top:1rem">🍽️ Your Personalized Diet Plan</div>')
    with gr.Row(elem_classes="glass-panel"):
        plan_out = gr.Markdown(
            label="",
            elem_classes="output-markdown",
            value="*Your meal plan will appear here after clicking Generate...*"
        )

    download_out = gr.File(label="⬇️ Download Diet Plan", visible=False)

    # ── Footer ──
    gr.HTML("""
    <div class="footer-bar">
        Built with ❤️ using Gradio • Hosted on Hugging Face Spaces • Powered by OpenRouter Free Models<br>
        <span style="color:rgba(165,180,252,.2)">🔒 API keys stored securely — never exposed in code</span>
    </div>
    """)

    # ── Event Handlers ──
    def on_generate(gender, age, goal, height_unit, height, weight_unit, weight, activity, dietary, model_name):
        plan, m_html, fname = generate_diet_plan(
            gender, age, goal, height_unit, height, weight_unit, weight, activity, dietary, model_name
        )
        # Write download file
        dl_path = None
        if plan and not plan.startswith("❌"):
            import tempfile
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
            tmp.write(f"AI Nutritionist Pro — Diet Plan\n{'='*50}\n\n{plan}")
            tmp.close()
            dl_path = tmp.name
        return plan, m_html, gr.update(value=dl_path, visible=dl_path is not None)

    gen_btn.click(
        fn=on_generate,
        inputs=[gender, age, goal, height_unit, height, weight_unit, weight, activity, dietary, model_choice],
        outputs=[plan_out, metrics_html, download_out],
        show_progress=True
    )

    chat_btn.click(
        fn=quick_chat,
        inputs=[chat_q, model_choice],
        outputs=[chat_out]
    )
    chat_q.submit(
        fn=quick_chat,
        inputs=[chat_q, model_choice],
        outputs=[chat_out]
    )

    def on_upload(f):
        if f:
            return gr.update(value=f"✅ Uploaded: `{Path(f).name}`", visible=True)
        return gr.update(visible=False)

    upload.change(fn=on_upload, inputs=[upload], outputs=[upload_note])


# ===== 8. LAUNCH =====
if __name__ == "__main__":
    demo.launch(
        css=CUSTOM_CSS,
        theme=gr.themes.Base(),
        server_name="0.0.0.0",
        server_port=7860,
    )
