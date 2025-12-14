"""
Authentication feature module.
Handles user registration, login, and logout.
"""

import streamlit as st
import re
import time
import logging

logger = logging.getLogger(__name__)


def show_register_form(db):
    """Display registration form."""
    # Header with professional styling
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #667eea; margin-bottom: 0.5rem;'>🎯 AI CV Screener</h1>
        <h2 style='color: #333; font-weight: 400; margin-bottom: 0.5rem;'>Create Your Account</h2>
        <p style='color: #666; font-size: 1rem;'>Join us to streamline your recruitment process</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create centered form container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("register_form"):
            st.markdown("#### 📝 Registration Details")
            username = st.text_input("👤 Username", max_chars=50, placeholder="Enter your username")
            email = st.text_input("📧 Email Address", placeholder="your.email@example.com")
            password = st.text_input("🔒 Password", type="password", placeholder="Minimum 6 characters")
            password_confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter your password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("✨ Create Account", use_container_width=True, type="primary")
        
        if submit:
            # Validation
            if not username or not email or not password:
                st.error("All fields are required!")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters!")
            elif password != password_confirm:
                st.error("Passwords do not match!")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Invalid email format!")
            else:
                try:
                    logger.info(f"Registration attempt for user: {username}")
                    # Create user
                    success, message = db.create_user(username, email, password)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.info("🔄 Redirecting to login page...")
                        logger.info(f"User registered successfully: {username}")
                        time.sleep(1.5)
                        st.session_state["show_login"] = True
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                        logger.warning(f"Registration failed for {username}: {message}")
                except Exception as e:
                    logger.error(f"Error during registration: {e}", exc_info=True)
                    st.error(f"❌ An error occurred: {str(e)}")
        
        st.markdown("""
        <div style='text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;'>
            <p style='color: #666; margin: 0;'>Already have an account?</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔙 Back to Login", use_container_width=True):
            st.session_state["show_login"] = True
            st.rerun()


def show_login_form(db):
    """Display login form."""
    # Header with professional styling
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #667eea; margin-bottom: 0.5rem;'>🎯 AI CV Screener</h1>
        <h2 style='color: #333; font-weight: 400; margin-bottom: 0.5rem;'>Welcome Back</h2>
        <p style='color: #666; font-size: 1rem;'>Sign in to access your recruitment dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create centered form container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("#### 🔑 Login Credentials")
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("🚀 Sign In", use_container_width=True, type="primary")
        
        if submit:
            if not username or not password:
                st.error("⚠️ Please enter both username and password!")
            else:
                try:
                    logger.info(f"Login attempt for user: {username}")
                    user = db.authenticate_user(username, password)
                    
                    if user:
                        st.session_state["logged_in"] = True
                        st.session_state["user"] = user
                        st.session_state["current_page"] = "Dashboard"
                        logger.info(f"User logged in successfully: {username}")
                        st.success(f"✅ Welcome back, {user['username']}!")
                        st.info("🔄 Loading your dashboard...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password!")
                        logger.warning(f"Login failed for user: {username}")
                except Exception as e:
                    logger.error(f"Error during login: {e}", exc_info=True)
                    st.error(f"❌ An error occurred: {str(e)}")
        
        st.markdown("""
        <div style='text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;'>
            <p style='color: #666; margin: 0;'>Don't have an account yet?</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✨ Create New Account", use_container_width=True):
            st.session_state["show_login"] = False
            st.rerun()


def logout():
    """Handle user logout."""
    try:
        username = st.session_state.get("user", {}).get("username", "Unknown")
        logger.info(f"User logging out: {username}")
        st.session_state["logged_in"] = False
        st.session_state["user"] = None
        st.session_state["page"] = "login"
        st.rerun()
    except Exception as e:
        logger.error(f"Error during logout: {e}", exc_info=True)
        st.error(f"An error occurred during logout: {str(e)}")


# Need to import time for sleep
import time
