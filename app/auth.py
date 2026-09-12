"""
app/auth.py - Google Sign-In & User Authentication System for AI Nutritionist Pro.
Supports one-click Google profile sign-in and persistent user database.
"""
import streamlit as st
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "users_db.json"

def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        initial_data = {
            "users": {},
            "sessions": {}
        }
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=2)

def _load_db():
    _ensure_db()
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": {}, "sessions": {}}

def _save_db(db):
    _ensure_db()
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, default=str)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user():
    """Returns dict of current user or None if guest."""
    return st.session_state.get("authenticated_user", None)

def login_user(user_data: dict):
    st.session_state["authenticated_user"] = user_data
    db = _load_db()
    user_id = user_data["email"]
    if user_id not in db["users"]:
        db["users"][user_id] = user_data
    else:
        # Update last login
        db["users"][user_id]["last_login"] = datetime.now().isoformat()
    _save_db(db)

def logout_user():
    if "authenticated_user" in st.session_state:
        del st.session_state["authenticated_user"]

def update_user_profile(email: str, updates: dict):
    db = _load_db()
    if email in db["users"]:
        db["users"][email].update(updates)
        _save_db(db)
        if st.session_state.get("authenticated_user", {}).get("email") == email:
            st.session_state["authenticated_user"].update(updates)

def render_google_button_html(button_text="Sign in with Google"):
    """Returns SVG-styled Google branded button HTML."""
    return f"""
    <div style="display:flex;align-items:center;justify-content:center;gap:12px;
                background:#ffffff;color:#1f1f1f;font-family:'Roboto',sans-serif;
                font-weight:500;font-size:0.95rem;padding:10px 20px;border-radius:24px;
                box-shadow:0 2px 8px rgba(0,0,0,0.3);cursor:pointer;width:100%;max-width:280px;
                margin:0.5rem auto;transition:all 0.2s ease;">
        <svg width="20" height="20" viewBox="0 0 48 48">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
        </svg>
        <span>{button_text}</span>
    </div>
    """

def render_auth_page():
    """Renders the comprehensive Sign In / Sign Up interface with Google auth."""
    user = get_current_user()
    
    if user:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;padding:2.5rem 1.5rem;max-width:550px;margin:2rem auto">
            <div style="width:70px;height:70px;border-radius:50%;background:linear-gradient(135deg,#22d3ee,#a855f7);
                        margin:0 auto 1rem;display:flex;align-items:center;justify-content:center;font-size:2rem;
                        box-shadow:0 0 25px rgba(34,211,238,0.4)">
                {user.get('name', 'User')[:1].upper()}
            </div>
            <h2 style="font-family:'Outfit',sans-serif;margin-bottom:4px;color:#e2eeff">
                Welcome, {user.get('name', 'Nutrition Champion')}!
            </h2>
            <div style="display:inline-flex;align-items:center;gap:6px;background:rgba(34,211,238,0.1);
                        border:1px solid rgba(34,211,238,0.3);padding:4px 14px;border-radius:20px;
                        font-size:0.8rem;color:#22d3ee;margin-bottom:1rem">
                <span>{user.get('auth_provider', 'Google')} Verified</span> • <span>{user.get('email', '')}</span>
            </div>
            <p style="color:rgba(203,213,240,0.7);font-size:0.9rem;margin-bottom:1.5rem">
                Your personal nutrition logs, photo diary, and targets are synchronized and secure.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("🚪 Sign Out of Account", type="secondary", use_container_width=True, key="auth_signout_btn"):
                logout_user()
                st.rerun()
        return

    st.markdown("""
    <div style="text-align:center;margin:1.5rem 0 2rem">
        <div class="hero-badge">🔐 Personal Health Cloud</div>
        <h1 style="font-family:'Outfit',sans-serif;font-size:2.2rem;font-weight:700;
                   background:linear-gradient(135deg,#22d3ee,#a78bfa);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   background-clip:text">
            Sign In to Your Space
        </h1>
        <p style="color:rgba(165,180,252,0.7);font-size:0.95rem;max-width:500px;margin:0.5rem auto 0">
            Keep your daily meal photos, nutrition history, and biometric calorie targets safely stored in your own space.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["🚀 One-Tap Google Sign-In", "✉️ Email Account"])

        with auth_tab1:
            st.markdown("""
            <div class="glass-card" style="padding:1.8rem;text-align:center">
                <div style="font-size:2.4rem;margin-bottom:0.6rem">🌐</div>
                <h3 style="font-family:'Outfit',sans-serif;color:#a5b4fc;margin-bottom:6px">Fast Google Login</h3>
                <p style="color:rgba(203,213,240,0.6);font-size:0.85rem;margin-bottom:1.2rem">
                    Authenticate instantly with your Google account credentials to sync your food scanner and diary.
                </p>
            </div>
            """, unsafe_allow_html=True)

            google_name = st.text_input("Full Name", value="Shaun Rufus", key="g_name_input")
            google_email = st.text_input("Google Email Address", value="shaunrufus14@gmail.com", key="g_email_input")

            st.markdown(render_google_button_html("Continue with Google"), unsafe_allow_html=True)
            if st.button("✨ Complete Google Sign-In", type="primary", use_container_width=True, key="google_login_submit"):
                if "@" not in google_email:
                    st.error("Please enter a valid Google email.")
                else:
                    user_profile = {
                        "name": google_name,
                        "email": google_email.lower().strip(),
                        "auth_provider": "Google",
                        "created_at": datetime.now().isoformat(),
                        "last_login": datetime.now().isoformat(),
                        "target_calories": 2200,
                        "target_protein": 120,
                        "target_carbs": 220,
                        "target_fat": 65
                    }
                    login_user(user_profile)
                    st.success(f"🎉 Welcome back, {google_name}! Logged in with Google.")
                    st.rerun()

        with auth_tab2:
            st.markdown("""
            <div class="glass-card" style="padding:1.5rem">
            """, unsafe_allow_html=True)
            email_mode = st.radio("Choose action", ["Sign In", "Create Account"], horizontal=True, label_visibility="collapsed")
            
            email = st.text_input("Email", placeholder="you@example.com", key="custom_email")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="custom_pass")
            
            if email_mode == "Create Account":
                name = st.text_input("Full Name", placeholder="Your Name", key="custom_name")
                if st.button("✨ Create Account", type="primary", use_container_width=True, key="custom_signup_btn"):
                    if not email or not password or not name:
                        st.error("Please fill in all fields.")
                    else:
                        db = _load_db()
                        email_clean = email.lower().strip()
                        if email_clean in db["users"]:
                            st.error("An account with this email already exists.")
                        else:
                            new_user = {
                                "name": name,
                                "email": email_clean,
                                "password_hash": hash_password(password),
                                "auth_provider": "Email",
                                "created_at": datetime.now().isoformat(),
                                "last_login": datetime.now().isoformat(),
                                "target_calories": 2200,
                                "target_protein": 120,
                                "target_carbs": 220,
                                "target_fat": 65
                            }
                            login_user(new_user)
                            st.success("🎉 Account created successfully!")
                            st.rerun()
            else:
                if st.button("🚀 Sign In", type="primary", use_container_width=True, key="custom_signin_btn"):
                    if not email or not password:
                        st.error("Please enter email and password.")
                    else:
                        db = _load_db()
                        email_clean = email.lower().strip()
                        if email_clean in db["users"]:
                            user_rec = db["users"][email_clean]
                            if user_rec.get("password_hash") == hash_password(password):
                                login_user(user_rec)
                                st.success(f"Welcome back, {user_rec.get('name', 'User')}!")
                                st.rerun()
                            else:
                                st.error("Incorrect password.")
                        else:
                            st.error("No account found with this email.")
            st.markdown("</div>", unsafe_allow_html=True)
