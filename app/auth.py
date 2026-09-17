"""
app/auth.py - Authentication System for AI Nutritionist Pro.
Supports Google-style sign-in and email/password accounts.
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
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump({"users": {}, "sessions": {}}, f, indent=2)

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

def render_auth_page():
    """Renders the clean, premium Sign In interface."""
    user = get_current_user()

    if user:
        # ── Signed-in state ──────────────────────────────────────
        st.markdown(f"""
        <div style="max-width:480px;margin:3rem auto;">
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(34,211,238,0.2);
                        border-radius:24px;padding:2.5rem 2rem;text-align:center;
                        backdrop-filter:blur(24px);box-shadow:0 16px 48px rgba(0,0,0,0.4)">
                <div style="width:72px;height:72px;border-radius:50%;
                            background:linear-gradient(135deg,#22d3ee,#a855f7);
                            margin:0 auto 1.2rem;display:flex;align-items:center;
                            justify-content:center;font-size:1.8rem;font-weight:700;
                            color:#fff;box-shadow:0 0 28px rgba(34,211,238,0.35)">
                    {user.get('name', 'U')[:1].upper()}
                </div>
                <div style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:700;
                            color:#e2eeff;margin-bottom:4px">
                    {user.get('name', 'User')}
                </div>
                <div style="font-size:0.82rem;color:rgba(165,180,252,0.6);margin-bottom:1.4rem">
                    {user.get('email', '')}
                </div>
                <div style="display:inline-flex;align-items:center;gap:6px;
                            background:rgba(34,211,238,0.08);border:1px solid rgba(34,211,238,0.25);
                            padding:4px 14px;border-radius:20px;font-size:0.78rem;color:#34d399;
                            margin-bottom:1.5rem">
                    <span>🟢</span> <span>Account Active</span>
                </div>
                <p style="color:rgba(203,213,240,0.55);font-size:0.88rem;line-height:1.6;margin:0">
                    Your nutrition logs and meal history are saved securely to your account.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_l, col_btn, col_r = st.columns([1, 2, 1])
        with col_btn:
            if st.button("Sign Out", type="secondary", use_container_width=True, key="auth_signout_btn"):
                logout_user()
                st.rerun()
        return

    # ── Sign-in / Create account ────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin:2rem 0 2.5rem">
        <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:700;
                    background:linear-gradient(135deg,#22d3ee,#a78bfa);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text;margin-bottom:0.6rem">
            Welcome Back
        </div>
        <p style="color:rgba(165,180,252,0.55);font-size:0.9rem;max-width:400px;margin:0 auto">
            Sign in to access your personal nutrition dashboard, meal history, and daily goals.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_google, tab_email = st.tabs(["  Sign in with Google  ", "  Email & Password  "])

        # ── Google / Quick Sign-In Tab ──────────────────────────
        with tab_google:
            st.markdown("""
            <div style="height:1rem"></div>
            <div style="background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.07);
                        border-radius:18px;padding:1.8rem 1.5rem;margin-bottom:1.2rem">
                <p style="color:rgba(165,180,252,0.55);font-size:0.83rem;text-align:center;
                           margin-bottom:1.4rem;line-height:1.5">
                    Enter your name and Google email address to sign in.
                    Your data stays private and is never shared.
                </p>
            """, unsafe_allow_html=True)

            google_name = st.text_input(
                "Your Name",
                placeholder="e.g. Alex Morgan",
                key="g_name_input",
                label_visibility="visible"
            )
            google_email = st.text_input(
                "Google Email",
                placeholder="e.g. alex@gmail.com",
                key="g_email_input",
                label_visibility="visible"
            )

            st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

            # Single clean button — no duplicate fake HTML button
            if st.button(
                "Continue with Google",
                type="primary",
                use_container_width=True,
                key="google_login_submit"
            ):
                clean_email = google_email.strip()
                if not clean_email or "@" not in clean_email:
                    st.error("Please enter a valid email address.")
                elif not google_name.strip():
                    st.error("Please enter your name.")
                else:
                    display_name = google_name.strip()
                    user_profile = {
                        "name": display_name,
                        "email": clean_email.lower(),
                        "auth_provider": "Google",
                        "created_at": datetime.now().isoformat(),
                        "last_login": datetime.now().isoformat(),
                        "target_calories": 2200,
                        "target_protein": 120,
                        "target_carbs": 220,
                        "target_fat": 65
                    }
                    login_user(user_profile)
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        # ── Email & Password Tab ────────────────────────────────
        with tab_email:
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            email_mode = st.radio(
                "Mode",
                ["Sign In", "Create Account"],
                horizontal=True,
                label_visibility="collapsed",
                key="email_mode_radio"
            )

            email = st.text_input("Email", placeholder="you@example.com", key="custom_email")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="custom_pass")

            if email_mode == "Create Account":
                name = st.text_input("Full Name", placeholder="Your Name", key="custom_name")
                st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
                if st.button("Create Account", type="primary", use_container_width=True, key="custom_signup_btn"):
                    if not email or not password or not name:
                        st.error("Please fill in all fields.")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        db = _load_db()
                        email_clean = email.lower().strip()
                        if email_clean in db["users"]:
                            st.error("An account with this email already exists. Try signing in.")
                        else:
                            new_user = {
                                "name": name.strip(),
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
                            st.rerun()
            else:
                st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
                if st.button("Sign In", type="primary", use_container_width=True, key="custom_signin_btn"):
                    if not email or not password:
                        st.error("Please enter your email and password.")
                    else:
                        db = _load_db()
                        email_clean = email.lower().strip()
                        if email_clean in db["users"]:
                            user_rec = db["users"][email_clean]
                            if user_rec.get("password_hash") == hash_password(password):
                                login_user(user_rec)
                                st.rerun()
                            else:
                                st.error("Incorrect password.")
                        else:
                            st.error("No account found with this email.")
