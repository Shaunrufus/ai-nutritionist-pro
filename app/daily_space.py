"""
app/daily_space.py - User's Personal Daily Space & Food Diary for AI Nutritionist Pro.
Stores user dish photos, meal timelines (Breakfast, Lunch, Dinner, Snacks),
and tracks daily calorie & macro targets vs actuals.
"""

import streamlit as st
import json
import base64
from pathlib import Path
from datetime import datetime, date
import pandas as pd

try:
    from app.auth import get_current_user
except (ImportError, ModuleNotFoundError):
    from auth import get_current_user

MEALS_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "user_meals_db.json"

def _ensure_meals_db():
    MEALS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not MEALS_DB_PATH.exists():
        with open(MEALS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)

def _load_meals_db():
    _ensure_meals_db()
    try:
        with open(MEALS_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_meals_db(db):
    _ensure_meals_db()
    with open(MEALS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, default=str)

def log_user_meal(user_email: str, meal_type: str, title: str, calories: float, protein: float, carbs: float, fat: float, items: list, image_b64: str = None) -> bool:
    """Saves a meal with dish photo and macros for a user."""
    db = _load_meals_db()
    email_key = user_email.lower().strip()
    if email_key not in db:
        db[email_key] = []

    meal_entry = {
        "id": f"meal_{int(datetime.now().timestamp())}",
        "date": date.today().isoformat(),
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "meal_type": meal_type,
        "title": title,
        "calories": round(calories),
        "protein": round(protein, 1),
        "carbs": round(carbs, 1),
        "fat": round(fat, 1),
        "items": items,
        "image_b64": image_b64
    }

    db[email_key].insert(0, meal_entry)
    _save_meals_db(db)
    return True

def delete_user_meal(user_email: str, meal_id: str) -> bool:
    db = _load_meals_db()
    email_key = user_email.lower().strip()
    if email_key in db:
        db[email_key] = [m for m in db[email_key] if m.get("id") != meal_id]
        _save_meals_db(db)
        return True
    return False

def get_user_meals_by_date(user_email: str, target_date_str: str) -> list:
    db = _load_meals_db()
    email_key = user_email.lower().strip()
    user_meals = db.get(email_key, [])
    return [m for m in user_meals if m.get("date") == target_date_str]

def render_daily_space_page():
    """Renders the comprehensive personal space and daily food diary."""
    user = get_current_user()

    if not user:
        st.markdown("""
        <div style="text-align:center;margin:3rem auto;max-width:550px">
            <div style="font-size:4rem;margin-bottom:1rem">🔒</div>
            <h2 style="font-family:'Outfit',sans-serif;font-size:2rem;color:#e2eeff;margin-bottom:8px">
                User Sign In Required
            </h2>
            <p style="color:rgba(203,213,240,0.7);font-size:0.95rem;line-height:1.6;margin-bottom:1.5rem">
                To keep your dish photos, meal timeline, and personal nutrition records securely saved in your own space, please sign in with your Google account.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c2:
            if st.button("🚀 Go to Google Sign-In Page", type="primary", use_container_width=True):
                st.session_state["nav_selection"] = "👤 Sign In / Google"
                # Do not set sidebar_nav_radio directly — widget key, causes error
                st.rerun()
        return

    # User is Authenticated
    user_name = user.get("name", "User")
    user_email = user.get("email", "")
    target_cals = user.get("target_calories", 2200)
    target_prot = user.get("target_protein", 120)
    target_carbs = user.get("target_carbs", 220)
    target_fat = user.get("target_fat", 65)

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-bottom:1.5rem">
        <div>
            <div class="hero-badge">📅 Personal Food Diary</div>
            <h1 style="font-family:'Outfit',sans-serif;font-size:2.2rem;font-weight:700;
                       background:linear-gradient(135deg,#22d3ee,#a78bfa);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                       background-clip:text;margin:4px 0">
                {user_name}'s Daily Space
            </h1>
            <div style="color:rgba(165,180,252,0.6);font-size:0.85rem">
                Logged in as <b>{user_email}</b> • Cloud Sync Active
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Date selector row
    d_col1, d_col2 = st.columns([2, 1])
    with d_col1:
        selected_date = st.date_input("Select Date to View", value=date.today(), key="daily_space_date_picker")
    date_str = selected_date.isoformat()

    meals_for_day = get_user_meals_by_date(user_email, date_str)

    # Calculate Totals for the Day
    day_cals = sum(m.get("calories", 0) for m in meals_for_day)
    day_prot = sum(m.get("protein", 0) for m in meals_for_day)
    day_carbs = sum(m.get("carbs", 0) for m in meals_for_day)
    day_fat = sum(m.get("fat", 0) for m in meals_for_day)

    cal_pct = min(100, int((day_cals / target_cals) * 100)) if target_cals > 0 else 0
    prot_pct = min(100, int((day_prot / target_prot) * 100)) if target_prot > 0 else 0
    carbs_pct = min(100, int((day_carbs / target_carbs) * 100)) if target_carbs > 0 else 0
    fat_pct = min(100, int((day_fat / target_fat) * 100)) if target_fat > 0 else 0

    # Macro Summary Bar Cards
    st.markdown(f"""
    <div class="glass-card" style="padding:1.5rem;margin-bottom:1.5rem">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
            <h3 style="font-family:'Outfit',sans-serif;font-size:1.15rem;color:#e2eeff;margin:0">
                Daily Macro Targets vs Consumed ({selected_date.strftime('%B %d, %Y')})
            </h3>
            <span style="font-size:0.85rem;font-weight:600;color:#22d3ee;background:rgba(34,211,238,0.1);padding:4px 12px;border-radius:12px;border:1px solid rgba(34,211,238,0.3)">
                {len(meals_for_day)} Meals Logged
            </span>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:12px">
            <!-- Calories -->
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(34,211,238,0.25);border-radius:14px;padding:12px">
                <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:rgba(165,180,252,0.7)">
                    <span>🔥 CALORIES</span>
                    <b>{cal_pct}%</b>
                </div>
                <div style="font-family:'Outfit',sans-serif;font-size:1.3rem;font-weight:700;color:#22d3ee;margin:4px 0">
                    {day_cals} <span style="font-size:0.8rem;color:rgba(203,213,240,0.6)">/ {target_cals} kcal</span>
                </div>
                <div style="width:100%;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden">
                    <div style="width:{cal_pct}%;height:100%;background:linear-gradient(90deg,#06b6d4,#3b82f6);border-radius:3px"></div>
                </div>
            </div>

            <!-- Protein -->
            <div style="background:rgba(16,185,129,0.04);border:1px solid rgba(16,185,129,0.25);border-radius:14px;padding:12px">
                <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:rgba(52,211,153,0.8)">
                    <span>💪 PROTEIN</span>
                    <b>{prot_pct}%</b>
                </div>
                <div style="font-family:'Outfit',sans-serif;font-size:1.3rem;font-weight:700;color:#34d399;margin:4px 0">
                    {day_prot:.0f}g <span style="font-size:0.8rem;color:rgba(203,213,240,0.6)">/ {target_prot}g</span>
                </div>
                <div style="width:100%;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden">
                    <div style="width:{prot_pct}%;height:100%;background:linear-gradient(90deg,#10b981,#34d399);border-radius:3px"></div>
                </div>
            </div>

            <!-- Carbs -->
            <div style="background:rgba(245,158,11,0.04);border:1px solid rgba(245,158,11,0.25);border-radius:14px;padding:12px">
                <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:rgba(251,191,36,0.8)">
                    <span>🌾 CARBS</span>
                    <b>{carbs_pct}%</b>
                </div>
                <div style="font-family:'Outfit',sans-serif;font-size:1.3rem;font-weight:700;color:#fbbf24;margin:4px 0">
                    {day_carbs:.0f}g <span style="font-size:0.8rem;color:rgba(203,213,240,0.6)">/ {target_carbs}g</span>
                </div>
                <div style="width:100%;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden">
                    <div style="width:{carbs_pct}%;height:100%;background:linear-gradient(90deg,#f59e0b,#fbbf24);border-radius:3px"></div>
                </div>
            </div>

            <!-- Fat -->
            <div style="background:rgba(244,63,94,0.04);border:1px solid rgba(244,63,94,0.25);border-radius:14px;padding:12px">
                <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:rgba(251,113,133,0.8)">
                    <span>🫧 FAT</span>
                    <b>{fat_pct}%</b>
                </div>
                <div style="font-family:'Outfit',sans-serif;font-size:1.3rem;font-weight:700;color:#fb7185;margin:4px 0">
                    {day_fat:.0f}g <span style="font-size:0.8rem;color:rgba(203,213,240,0.6)">/ {target_fat}g</span>
                </div>
                <div style="width:100%;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden">
                    <div style="width:{fat_pct}%;height:100%;background:linear-gradient(90deg,#e11d48,#fb7185);border-radius:3px"></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Meals Timeline Display
    st.markdown('<div class="section-header">🍽️ Logged Dishes & Live Photos</div>', unsafe_allow_html=True)

    if not meals_for_day:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;padding:2.5rem 1.5rem">
            <div style="font-size:3rem;margin-bottom:0.5rem">📸</div>
            <h3 style="font-family:'Outfit',sans-serif;color:#a5b4fc;margin-bottom:6px">No Meals Logged for {selected_date.strftime('%b %d')}</h3>
            <p style="color:rgba(203,213,240,0.6);font-size:0.85rem;margin-bottom:1rem">
                Use the <b>Live Camera Calorie Tracker</b> to snap your dish and save it directly into your daily space!
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, meal in enumerate(meals_for_day):
            m_id = meal.get("id")
            m_type = meal.get("meal_type", "Meal")
            m_title = meal.get("title", "Delicious Meal")
            m_time = meal.get("timestamp", "")
            m_cal = meal.get("calories", 0)
            m_prot = meal.get("protein", 0)
            m_carbs = meal.get("carbs", 0)
            m_fat = meal.get("fat", 0)
            m_img = meal.get("image_b64", None)
            m_items = meal.get("items", [])

            type_icons = {"Breakfast": "🌅", "Lunch": "☀️", "Dinner": "🌙", "Snack": "🫖"}
            icon = type_icons.get(m_type, "🍽️")

            m_col1, m_col2 = st.columns([1, 2.5])

            with m_col1:
                if m_img:
                    st.markdown(f"""
                    <div style="border-radius:14px;overflow:hidden;border:1px solid rgba(34,211,238,0.3);box-shadow:0 6px 20px rgba(0,0,0,0.5)">
                        <img src="data:image/jpeg;base64,{m_img}" style="width:100%;height:180px;object-fit:cover;display:block">
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="height:180px;background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.1);
                                border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:3rem">
                        {icon}
                    </div>
                    """, unsafe_allow_html=True)

            with m_col2:
                st.markdown(f"""
                <div class="glass-card" style="padding:1.2rem;height:100%">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                        <div>
                            <span style="font-size:0.8rem;background:rgba(34,211,238,0.1);border:1px solid rgba(34,211,238,0.3);
                                         color:#22d3ee;padding:2px 10px;border-radius:12px;font-weight:600">
                                {icon} {m_type}
                            </span>
                            <span style="color:rgba(165,180,252,0.5);font-size:0.75rem;margin-left:8px">{m_time}</span>
                        </div>
                        <div style="font-family:'Outfit',sans-serif;font-weight:700;font-size:1.1rem;color:#22d3ee">
                            🔥 {m_cal} kcal
                        </div>
                    </div>
                    
                    <h3 style="font-family:'Outfit',sans-serif;font-size:1.2rem;color:#e2eeff;margin:6px 0">{m_title}</h3>
                    
                    <div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0">
                        <span class="macro-pill protein">💪 {m_prot}g Protein</span>
                        <span class="macro-pill carbs">🌾 {m_carbs}g Carbs</span>
                        <span class="macro-pill fat">🫧 {m_fat}g Fat</span>
                    </div>

                    <div style="font-size:0.8rem;color:rgba(203,213,240,0.6);margin-top:6px">
                        <b>Items:</b> {', '.join([it.get('name', '') for it in m_items]) if m_items else 'Scanned Plate'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"🗑️ Delete Entry", key=f"del_meal_{m_id}"):
                    delete_user_meal(user_email, m_id)
                    st.rerun()

            st.markdown("<hr style='border-top:1px solid rgba(255,255,255,0.06);margin:1.2rem 0'>", unsafe_allow_html=True)
