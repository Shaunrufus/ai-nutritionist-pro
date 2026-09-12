---
title: AI Nutritionist Pro
emoji: 🥗
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.27.0
app_file: app.py
pinned: true
license: mit
---

# 🥗 AI Nutritionist Pro

> **Live App:** [Streamlit Cloud](https://share.streamlit.io) | **Backup:** Hugging Face Spaces

A futuristic AI-powered nutritionist that generates personalized Indian meal plans using:
- 🤖 **OpenRouter Free AI Models** — Google Gemma 4, NVIDIA Nemotron, and more (no cost!)
- 🧬 **ML-based macro prediction** — XGBoost model trained on nutrition data
- 🎨 **Glassmorphism UI** — futuristic dark mode with animated cards

## 🚀 Quick Deploy

### Streamlit Cloud (Primary — Free, 24/7 with UptimeRobot)
1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select this repo
3. Set main file: `app/Streamlit_app.py`
4. Add secret: `OPENROUTER_API_KEY = "your_key"`

### Local Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OpenRouter API key to .env
streamlit run app/Streamlit_app.py
```

## 🔑 API Key
Get your free OpenRouter key at: https://openrouter.ai/keys

## 🌐 Free Models Used
| Model | Provider |
|-------|----------|
| gemma-4-31b-it:free | Google |
| nemotron-3-ultra-550b:free | NVIDIA |
| nemotron-3-super-120b:free | NVIDIA |
| nemotron-3.5-lightning:free | NVIDIA |
| inkling:free | Thinking Machines |
| lfm-2.5-2.6b:free | LiquidAI |

## 🛡️ Security
- API keys stored in `.env` (local) or Streamlit/HF secrets (cloud)
- `.env` is in `.gitignore` — never committed to git