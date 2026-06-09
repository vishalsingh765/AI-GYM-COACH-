import streamlit as st
from services.auth.auth_service import create_user, authenticate_user

def render_auth_wall():
    """Render premium authentication wall with modern UI"""
    
    if st.session_state.get("user_id") is not None:
        return True
    
    # Premium background for auth page
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        background-attachment: fixed;
    }
    
    .auth-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    .auth-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        border-radius: 28px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 2rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    
    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .auth-header h1 {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #fff 0%, #00d4ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .auth-header p {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    /* Custom tab styling */
    .auth-tabs {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 0.5rem;
    }
    
    .auth-tab {
        flex: 1;
        text-align: center;
        padding: 0.75rem;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
        border-radius: 10px;
    }
    
    .auth-tab.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .auth-tab.inactive {
        color: #94a3b8;
    }
    
    .input-group {
        margin-bottom: 1.5rem;
    }
    
    .input-group label {
        display: block;
        margin-bottom: 0.5rem;
        color: #cbd5e1;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .input-group input {
        width: 100%;
        padding: 0.75rem 1rem;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        color: white;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .input-group input:focus {
        outline: none;
        border-color: #00d4ff;
        background: rgba(255, 255, 255, 0.12);
    }
    
    .auth-button {
        width: 100%;
        padding: 0.875rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 12px;
        color: white;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-top: 1rem;
    }
    
    .auth-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(102, 126, 234, 0.4);
    }
    
    .error-message {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 12px;
        padding: 0.75rem;
        color: #f87171;
        font-size: 0.875rem;
        margin-bottom: 1rem;
    }
    
    .success-message {
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 12px;
        padding: 0.75rem;
        color: #4ade80;
        font-size: 0.875rem;
        margin-bottom: 1rem;
    }
    
    .feature-list {
        margin-top: 2rem;
        padding-top: 2rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .feature-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    .feature-icon {
        font-size: 1.25rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for auth
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    
    # Main container
    with st.container():
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        # Hero section
        st.markdown("""
        <div class="auth-header">
            <div style="font-size: 4rem;">🏋️‍♂️</div>
            <h1>AI Real-time GYM Trainer</h1>
            <p>Your personal AI coach for perfect form</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Auth card
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        # Custom tab buttons using columns
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.auth_mode == "login":
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    text-align: center;
                    padding: 0.75rem;
                    border-radius: 12px;
                    font-weight: 600;
                    color: white;
                ">
                    🔐 Login
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button("🔐 Login", key="login_tab_btn", use_container_width=True):
                    st.session_state.auth_mode = "login"
                    st.rerun()
        
        with col2:
            if st.session_state.auth_mode == "signup":
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    text-align: center;
                    padding: 0.75rem;
                    border-radius: 12px;
                    font-weight: 600;
                    color: white;
                ">
                    📝 Sign Up
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button("📝 Sign Up", key="signup_tab_btn", use_container_width=True):
                    st.session_state.auth_mode = "signup"
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Display messages
        if st.session_state.get("auth_error"):
            st.markdown(f'<div class="error-message">❌ {st.session_state.auth_error}</div>', unsafe_allow_html=True)
            st.session_state.auth_error = None
        
        if st.session_state.get("auth_success"):
            st.markdown(f'<div class="success-message">✅ {st.session_state.auth_success}</div>', unsafe_allow_html=True)
            st.session_state.auth_success = None
        
        # Only show Login form when auth_mode is "login"
        if st.session_state.auth_mode == "login":
            with st.form("login_form"):
                username_or_email = st.text_input(
                    "Username or Email",
                    placeholder="Enter your username or email",
                    key="login_username"
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password"
                )
                
                submitted = st.form_submit_button("Start Training", use_container_width=True)
                
                if submitted:
                    if not username_or_email or not password:
                        st.session_state.auth_error = "Please fill in all fields"
                        st.rerun()
                    
                    result = authenticate_user(username_or_email, password)
                    
                    if result["success"]:
                        st.session_state["user_id"] = result["user"]["id"]
                        st.session_state["username"] = result["user"]["username"]
                        st.session_state["user_email"] = result["user"]["email"]
                        st.rerun()
                    else:
                        st.session_state.auth_error = result["error"]
                        st.rerun()
        
        # Only show Signup form when auth_mode is "signup"
        elif st.session_state.auth_mode == "signup":
            with st.form("signup_form"):
                username = st.text_input(
                    "Username",
                    placeholder="Choose a unique username",
                    key="signup_username"
                )
                email = st.text_input(
                    "Email",
                    placeholder="your@email.com",
                    key="signup_email"
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Choose a strong password",
                    key="signup_password"
                )
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Confirm your password",
                    key="signup_confirm"
                )
                
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                
                if submitted:
                    if not all([username, email, password, confirm_password]):
                        st.session_state.auth_error = "Please fill in all fields"
                        st.rerun()
                    
                    if password != confirm_password:
                        st.session_state.auth_error = "Passwords do not match"
                        st.rerun()
                    
                    if len(password) < 6:
                        st.session_state.auth_error = "Password must be at least 6 characters"
                        st.rerun()
                    
                    result = create_user(username, email, password)
                    
                    if result["success"]:
                        st.session_state.auth_success = "Account created successfully! Please login."
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.session_state.auth_error = result["error"]
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close auth-card
        
        # Features section
        st.markdown("""
        <div class="feature-list">
            <div class="feature-item">
                <span class="feature-icon">🎯</span>
                <span>Real-time pose detection with 99% accuracy</span>
            </div>
            <div class="feature-item">
                <span class="feature-icon">🤖</span>
                <span>AI-powered voice coaching for perfect form</span>
            </div>
            <div class="feature-item">
                <span class="feature-icon">📊</span>
                <span>Detailed workout analytics and history</span>
            </div>
            <div class="feature-item">
                <span class="feature-icon">💪</span>
                <span>Multiple exercises: Squats, Push-ups, Curls & more</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close auth-container
    
    return False

# For backward compatibility
render_login_wall = render_auth_wall